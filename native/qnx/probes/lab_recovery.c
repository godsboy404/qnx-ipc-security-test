#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <signal.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/neutrino.h>
#include <sys/stat.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#include "lab_protocol.h"

extern char **environ;
static volatile sig_atomic_t interrupted;
static volatile sig_atomic_t owned_pause_pid,pause_watchdog_triggered;
static void on_signal(int sig) {
    interrupted=1;
    if(sig==SIGALRM)pause_watchdog_triggered=1;
    if(owned_pause_pid>0)kill((pid_t)owned_pause_pid,SIGCONT);
}
static uint64_t now_ns(void) {
    struct timespec t;
    if(clock_gettime(CLOCK_MONOTONIC,&t))exit(2);
    return (uint64_t)t.tv_sec*1000000000ULL+(uint64_t)t.tv_nsec;
}
static void nap(void) { struct timespec t={0,20000000};nanosleep(&t,NULL); }
typedef struct { pid_t pid;int reaped,status,stopped; } child_t;
static int launch(child_t *c,char *const args[]) {
    int rc=posix_spawn(&c->pid,args[0],NULL,NULL,args,environ);
    if(rc) { errno=rc;perror("posix_spawn");return -1; }return 0;
}
static const char *state(child_t *c) {
    if(c->pid<=0)return "unknown";
    if(!c->reaped) {
        int status;
        pid_t n=waitpid(c->pid,&status,WNOHANG|WUNTRACED|WCONTINUED);
        if(n==0)return c->stopped ? "stopped":"running";
        if(n!=c->pid)return "unknown";
        c->status=status;
        if(WIFSTOPPED(status)) { c->stopped=1;return "stopped"; }
        if(WIFCONTINUED(status)) { c->stopped=0;return "running"; }
        c->reaped=1;
        c->stopped=0;
    }
    return WIFSIGNALED(c->status) ? "signaled":(WIFEXITED(c->status) ? "exited":"unknown");
}
static void stop_owned(child_t *c) {
    if(c->pid<=0 || c->reaped)return;
    /* A suspended owned child must be continued before normal cleanup. */
    kill(c->pid,SIGCONT);
    kill(c->pid,SIGTERM);
    uint64_t deadline=now_ns()+1000000000ULL;
    while(!c->reaped && now_ns()<deadline) { state(c);nap(); }
    if(!c->reaped) { kill(c->pid,SIGKILL);if(waitpid(c->pid,&c->status,0)==c->pid)c->reaped=1; }
}
static int probe(void) {
    signal(SIGTERM,on_signal);signal(SIGINT,on_signal);signal(SIGHUP,on_signal);
    FILE *fp=fopen("os-probe.jsonl","w");if(!fp)return 2;
    while(!interrupted) {
        struct utsname name;struct stat st;uint64_t begin=now_ns();
        int urc=uname(&name),ue=urc ? errno:0;
        int src=stat("/proc",&st),se=src ? errno:0;
        fprintf(fp,"{\"probe_pid\":%d,\"begin_ns\":%" PRIu64 ",\"end_ns\":%" PRIu64 ",\"uname_rc\":%d,\"uname_errno\":%d,\"proc_stat_rc\":%d,\"proc_stat_errno\":%d,\"proc_is_directory\":%s}\n",
            (int)getpid(),begin,now_ns(),urc,ue,src,se,!src && S_ISDIR(st.st_mode) ? "true":"false");
        if(fflush(fp)) { fclose(fp);return 2; }nap();
    }
    fclose(fp);return 0;
}
static int request(const char *stage) {
    const char *path=!strcmp(stage,"before") ? "before.jsonl":(!strcmp(stage,"after") ? "after.jsonl":(!strcmp(stage,"down") ? "down.jsonl":NULL));
    if(!path)return 2;
    FILE *fp=fopen(path,"w");if(!fp)return 2;
    uint64_t begin=now_ns();int fd=open(LAB_DEVICE_PATH,O_RDWR),open_error=fd<0 ? errno:0;
    if(!strcmp(stage,"down")) {
        fprintf(fp,"{\"client_pid\":%d,\"begin_ns\":%" PRIu64 ",\"end_ns\":%" PRIu64 ",\"open_succeeded\":%s,\"open_errno\":%d,\"ipc_sent\":false}\n",
            (int)getpid(),begin,now_ns(),fd>=0 ? "true":"false",open_error);
        if(fd>=0)close(fd);
        fclose(fp);return open_error==ENOENT ? 0:2;
    }
    if(fd<0) { fclose(fp);return 2; }
    for(unsigned i=0;i<10;i++) {
        lab_request_t req={0},expected;
        req.operation=LAB_OP_ECHO;req.declared_length=4;memcpy(req.payload,"ping",4);expected=req;
        uint64_t timeout=2000000000ULL;begin=now_ns();
        if(TimerTimeout(CLOCK_MONOTONIC,_NTO_TIMEOUT_SEND|_NTO_TIMEOUT_REPLY,NULL,&timeout,NULL))return 2;
        int rc=devctl(fd,LAB_DCMD_ECHO,&req,LAB_HEADER_SIZE+4,NULL);
        uint64_t end=now_ns();int matches=rc==EOK && !memcmp(&req,&expected,LAB_HEADER_SIZE+4);
        fprintf(fp,"{\"sequence\":%u,\"client_pid\":%d,\"begin_ns\":%" PRIu64 ",\"end_ns\":%" PRIu64 ",\"return_code\":%d,\"reply_matches\":%s}\n",
            i+1,(int)getpid(),begin,end,rc,matches ? "true":"false");
        if(fflush(fp) || !matches) { close(fd);fclose(fp);return 2; }nap();
    }
    close(fd);fclose(fp);return 0;
}
static FILE *events,*samples;
static uint64_t deadline;
static child_t *active_target,*active_probe;
static void event(const char *name,child_t *target,child_t *client) {
    const char *observed=state(target);
    /* access() may ask the resource manager for attributes: never call it
     * while that manager is stopped. Null means unobserved, not absent. */
    const char *device=target->stopped ? "null":(access(LAB_DEVICE_PATH,F_OK)==0 ? "true":"false");
    fprintf(events,"{\"event\":\"%s\",\"mono_ns\":%" PRIu64 ",\"monitor_pid\":%d,\"target_pid\":%d,\"client_pid\":%d,\"target_state\":\"%s\",\"target_signal\":%d,\"device_present\":%s,\"target_stop_signal\":%d}\n",
        name,now_ns(),(int)getpid(),(int)target->pid,client ? (int)client->pid:0,observed,
        target->reaped && WIFSIGNALED(target->status) ? WTERMSIG(target->status):0,
        device,target->stopped ? WSTOPSIG(target->status):0);fflush(events);
}
static int tick(const char *phase) {
    const char *ts=state(active_target),*ps=state(active_probe);
    fprintf(samples,"{\"phase\":\"%s\",\"mono_ns\":%" PRIu64 ",\"monitor_pid\":%d,\"target_pid\":%d,\"target_state\":\"%s\",\"probe_pid\":%d,\"probe_state\":\"%s\"}\n",
        phase,now_ns(),(int)getpid(),(int)active_target->pid,ts,(int)active_probe->pid,ps);fflush(samples);
    return !interrupted && now_ns()<deadline && !strcmp(ps,"running");
}
static int wait_device(child_t *target) {
    while(tick("startup") && !strcmp(state(target),"running")) {
        if(access(LAB_DEVICE_PATH,F_OK)==0)return 1;
        nap();
    }return 0;
}
static int wait_client(child_t *client,const char *phase,int target_running) {
    while(tick(phase)) {
        if(target_running && strcmp(state(active_target),"running"))return 0;
        const char *cs=state(client);
        if(strcmp(cs,"running"))return client->reaped && WIFEXITED(client->status) && WEXITSTATUS(client->status)==0;
        nap();
    }return 0;
}
#include "lab_stall.h"
int main(int argc,char **argv) {
    if(argc==2 && !strcmp(argv[1],"--probe"))return probe();
    if(argc==3 && !strcmp(argv[1],"--request"))return request(argv[2]);
    if(argc==2 && !strcmp(argv[1],"--stall-request"))return stall_request();
    if(argc==2 && !strcmp(argv[1],"--stall"))return stall_experiment();
    if(argc!=1 || access(LAB_DEVICE_PATH,F_OK)==0)return 2;
    signal(SIGTERM,on_signal);signal(SIGINT,on_signal);signal(SIGHUP,on_signal);
    child_t first={0},second={0},observer={0},before={0},down={0},after={0};int ok=0;
    active_target=&first;active_probe=&observer;deadline=now_ns()+15000000000ULL;
    events=fopen("recovery-events.jsonl","w");samples=fopen("recovery-monitor.jsonl","w");
    if(!events || !samples)return 2;
    FILE *meta=fopen("recovery-meta.json","w");if(!meta)return 2;
    fprintf(meta,"{\"backend\":\"qnx-native\",\"SIGTERM\":%d,\"ENOENT\":%d,\"monitor_pid\":%d,\"fault_kind\":\"controlled_SIGTERM\",\"monitor_deadline_seconds\":15,\"ipc_deadline_seconds\":2}\n",SIGTERM,ENOENT,(int)getpid());fclose(meta);
    char *server[]={"./lab-resmgr",NULL},*osprobe[]={"./lab-recovery","--probe",NULL};
    char *cb[]={"./lab-recovery","--request","before",NULL},*cd[]={"./lab-recovery","--request","down",NULL},*ca[]={"./lab-recovery","--request","after",NULL};
    if(launch(&observer,osprobe) || launch(&first,server) || !wait_device(&first))goto cleanup;
    event("ready",&first,NULL);
    if(launch(&before,cb) || !wait_client(&before,"before",1))goto cleanup;
    event("before_complete",&first,&before);event("stop_requested",&first,NULL);
    if(kill(first.pid,SIGTERM))goto cleanup;
    while(tick("stopping") && !strcmp(state(&first),"running"))nap();
    if(!first.reaped || !WIFSIGNALED(first.status) || WTERMSIG(first.status)!=SIGTERM || access(LAB_DEVICE_PATH,F_OK)==0)goto cleanup;
    event("stopped",&first,NULL);
    if(rename("target-audit.jsonl","target-before.jsonl"))goto cleanup;
    if(launch(&down,cd) || !wait_client(&down,"down",0))goto cleanup;
    event("unavailable_observed",&first,&down);
    for(unsigned i=0;i<10;i++) { if(!tick("down"))goto cleanup;nap(); }
    active_target=&second;
    event("restart_requested",&second,NULL);
    if(launch(&second,server) || !wait_device(&second))goto cleanup;
    event("restarted",&second,NULL);
    if(launch(&after,ca) || !wait_client(&after,"after",1))goto cleanup;
    event("after_complete",&second,&after);
    for(unsigned i=0;i<5;i++) { if(!tick("after"))goto cleanup;nap(); }
    ok=1;
cleanup:
    stop_owned(&before);stop_owned(&down);stop_owned(&after);stop_owned(&first);stop_owned(&second);stop_owned(&observer);
    if(second.pid>0 && rename("target-audit.jsonl","target-after.jsonl"))ok=0;
    FILE *out=fopen("recovery-cleanup.json","w");
    if(!out)ok=0;
    else {
        int clean=first.reaped && second.reaped && observer.reaped && before.reaped && down.reaped && after.reaped && access(LAB_DEVICE_PATH,F_OK)!=0;
        fprintf(out,"{\"complete\":%s,\"all_owned_children_reaped\":%s,\"device_present\":%s,\"monitor_pid\":%d,\"first_target_pid\":%d,\"second_target_pid\":%d,\"probe_pid\":%d,\"before_client_pid\":%d,\"down_client_pid\":%d,\"after_client_pid\":%d}\n",
            ok ? "true":"false",clean ? "true":"false",access(LAB_DEVICE_PATH,F_OK)==0 ? "true":"false",(int)getpid(),(int)first.pid,(int)second.pid,(int)observer.pid,(int)before.pid,(int)down.pid,(int)after.pid);
        fclose(out);if(!clean)ok=0;
    }
    fclose(events);fclose(samples);return ok ? 0:2;
}
