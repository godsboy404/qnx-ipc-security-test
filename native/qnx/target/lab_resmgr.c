#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/dispatch.h>
#include <sys/neutrino.h>
#include <sys/iofunc.h>
#include <sys/resmgr.h>
#include "lab_protocol.h"

static int lab_devctl(resmgr_context_t *ctp, io_devctl_t *msg, void *handle)
{
    iofunc_ocb_t *ocb = handle;
    int status = iofunc_devctl_default(ctp, msg, ocb);
    if (status != _RESMGR_DEFAULT) return status;
    if (msg->i.dcmd != LAB_DCMD_ECHO) return ENOTTY;
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

    memset(&msg->o, 0, sizeof(msg->o));
    msg->o.nbytes = (uint32_t)actual;
    memcpy(_DEVCTL_DATA(msg->o), &request, actual);
    return _RESMGR_PTR(ctp, &msg->o, sizeof(msg->o) + actual);
}

int main(void)
{
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
    }
    dispatch_context_free(context);
    dispatch_destroy(dpp);
    return EXIT_FAILURE;
}
