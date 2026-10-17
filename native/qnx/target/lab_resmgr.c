#include <errno.h>
#include <inttypes.h>
#include <signal.h>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/dispatch.h>
#include <sys/neutrino.h>
#include <sys/iofunc.h>
#include <sys/resmgr.h>
#include "lab_protocol.h"

static FILE *audit;
static unsigned audit_sequence;
static int controlled_pause_enabled,checkpoint_after_reply;

static int lab_devctl(resmgr_context_t *ctp, io_devctl_t *msg, void *handle)
{
    iofunc_ocb_t *ocb = handle;
    int status = iofunc_devctl_default(ctp, msg, ocb);
    if (status != _RESMGR_DEFAULT) return status;
    if (msg->i.dcmd != LAB_DCMD_ECHO) return ENOTTY;
    /* Independent receiver evidence, written before application validation. */
    if (ctp->size < sizeof(msg->i)) return EINVAL;
    size_t received=ctp->size-sizeof(msg->i);
    if(received>LAB_HEADER_SIZE+65) return EMSGSIZE;
    struct timespec stamp;
    if(clock_gettime(CLOCK_MONOTONIC,&stamp)) return EIO;
    fprintf(audit,"{\"sequence\":%u,\"target_pid\":%d,\"mono_ns\":%" PRIu64 ",\"dcmd_bytes\":%zu,\"wire_hex\":\"",
        ++audit_sequence,(int)getpid(),(uint64_t)((uint64_t)stamp.tv_sec*1000000000ULL+(uint64_t)stamp.tv_nsec),received);
    const unsigned char *raw=_DEVCTL_DATA(msg->i);
    for(size_t i=0;i<received;i++) fprintf(audit,"%02x",raw[i]);
    fputs("\"}\n",audit);
    if(fflush(audit)) return EIO;
    if (ctp->rcvid == 0) return ENOTSUP; /* No combined-request reply reuse. */

    /* Validate actual received bytes before touching the application header.
     * nbytes is checked for consistency, never used as proof of received size. */
    if (ctp->size < sizeof(msg->i) + LAB_HEADER_SIZE) return EINVAL;
    size_t actual = ctp->size - sizeof(msg->i);
    if (actual > sizeof(lab_request_t)) return EMSGSIZE;
    if (msg->i.nbytes != actual) return EINVAL;
    if (ctp->info.srcmsglen != (int)(ctp->offset + ctp->size)) return EMSGSIZE;
    if (ctp->info.dstmsglen < (int)(sizeof(msg->o) + actual)) return EMSGSIZE;

    lab_request_t request;
    memset(&request, 0, sizeof(request));
    memcpy(&request, _DEVCTL_DATA(msg->i), actual);
    if (request.operation != LAB_OP_ECHO || request.flags != 0) return EINVAL;
    if (request.declared_length > LAB_MAX_PAYLOAD ||
        request.declared_length != actual - LAB_HEADER_SIZE) return EINVAL;
    if (request.offset < 0 || (uint32_t)request.offset > request.declared_length) return EINVAL;
    /* Only the explicit gate ECHO may arm the pause, never a preceding stat,
     * open or close whose handler may finish after the host creates a flag. */
    if(controlled_pause_enabled && request.declared_length==4 && !memcmp(request.payload,"gate",4) &&
       access("pause-before-receive.ready",F_OK)==0)checkpoint_after_reply=1;

    memset(&msg->o, 0, sizeof(msg->o));
    msg->o.nbytes = (uint32_t)actual;
    memcpy(_DEVCTL_DATA(msg->o), &request, actual);
    return _RESMGR_PTR(ctp, &msg->o, sizeof(msg->o) + actual);
}

int main(int argc,char **argv)
{
    int controlled_pause=argc==2 && !strcmp(argv[1],"--controlled-pause"),pause_used=0;
    if(argc!=1 && !controlled_pause)return EXIT_FAILURE;
    controlled_pause_enabled=controlled_pause;
    audit=fopen("target-audit.jsonl","w");
    if(!audit) { perror("target audit");return EXIT_FAILURE; }
    dispatch_t *dpp = dispatch_create();
    if (!dpp) { perror("dispatch_create"); return EXIT_FAILURE; }
    resmgr_attr_t rattr;
    resmgr_connect_funcs_t cfuncs;
    resmgr_io_funcs_t ifuncs;
    iofunc_attr_t attr;
    memset(&rattr, 0, sizeof(rattr));
    rattr.nparts_max = 1;
    rattr.msg_max_size = 2048;
    iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &cfuncs, _RESMGR_IO_NFUNCS, &ifuncs);
    ifuncs.devctl = lab_devctl;
    iofunc_attr_init(&attr, S_IFCHR | 0600, NULL, NULL);
    if (resmgr_attach(dpp, &rattr, LAB_DEVICE_PATH, _FTYPE_ANY, 0, &cfuncs, &ifuncs, &attr) == -1) {
        perror("resmgr_attach"); dispatch_destroy(dpp); return EXIT_FAILURE;
    }
    dispatch_context_t *context = dispatch_context_alloc(dpp);
    if (!context) { perror("dispatch_context_alloc"); dispatch_destroy(dpp); return EXIT_FAILURE; }
    printf("READY path=%s protocol=devctl-echo-v1\n", LAB_DEVICE_PATH);
    fflush(stdout);
    for (;;) {
        dispatch_context_t *next = dispatch_block(context);
        if (!next) {
            if (errno == EINTR) continue;
            perror("dispatch_block"); break;
        }
        context = next;
        dispatch_handler(context);
        /* Opt-in experiment checkpoint: stop after the previous reply and
         * before dispatch_block posts another receive. Not a production API. */
        if(controlled_pause && !pause_used && checkpoint_after_reply) {
            pause_used=1;raise(SIGSTOP);
        }
    }
    dispatch_context_free(context);
    dispatch_destroy(dpp);
    return EXIT_FAILURE;
}
