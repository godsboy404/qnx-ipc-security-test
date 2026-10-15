#include <errno.h>
#include <inttypes.h>
#include <signal.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#include "lab_protocol.h"

extern char **environ;
static volatile sig_atomic_t interrupted;
static void on_signal(int sig) { (void)sig; interrupted=1; }
static uint64_t now_ns(void) {
    struct timespec t;
    if(clock_gettime(CLOCK_MONOTONIC,&t)) exit(2);
    return (uint64_t)t.tv_sec*1000000000ULL+(uint64_t)t.tv_nsec;
}
static void nap(void) { struct timespec t={0,20000000}; nanosleep(&t,NULL); }
typedef struct {
    pid_t pid;
    int reaped,status;
} child_t;
static int launch(child_t *c,const char *path,char *const args[]) {
    int rc=posix_spawn(&c->pid,path,NULL,NULL,args,environ);
    if(rc) { errno=rc;perror("posix_spawn");return -1; }
    return 0;
}
static const char *poll_child(child_t *c) {
    if(c->pid<=0) return "unknown";
    if(!c->reaped) {
        pid_t n=waitpid(c->pid,&c->status,WNOHANG);
        if(n==0) return "running";
        if(n==c->pid) c->reaped=1;
        else return "unknown";
    }
    if(WIFSIGNALED(c->status)) return "signaled";
    if(WIFEXITED(c->status)) return "exited";
    return "unknown";
}
static void stop_owned(child_t *c) {
    if(c->pid<=0 || c->reaped) return;
    kill(c->pid,SIGTERM);
    uint64_t deadline=now_ns()+1000000000ULL;
    while(!c->reaped && now_ns()<deadline) { poll_child(c);nap(); }
    if(!c->reaped) { kill(c->pid,SIGKILL);waitpid(c->pid,&c->status,0);c->reaped=1; }
}
static int peer(void) {
    FILE *fp=fopen("heartbeat.jsonl","w");
    if(!fp)return 2;
    while(!interrupted) {
        fprintf(fp,"{\"pid\":%d,\"mono_ns\":%" PRIu64 "}\n",(int)getpid(),now_ns());
        fflush(fp);
        struct timespec t={0,50000000};nanosleep(&t,NULL);
    }
    fclose(fp);return 0;
}
static int selftest(void) {
    child_t a={0},b={0};
    char *args_a[]={"./lab-monitor","--exit7",NULL};
    char *args_b[]={"./lab-monitor","--term",NULL};
    if(launch(&a,args_a[0],args_a) || launch(&b,args_b[0],args_b)) { stop_owned(&a);stop_owned(&b);return 2; }
    uint64_t deadline=now_ns()+2000000000ULL;
    while((!a.reaped || !b.reaped) && now_ns()<deadline) { poll_child(&a);poll_child(&b);nap(); }
    int exitok=a.reaped && WIFEXITED(a.status) && WEXITSTATUS(a.status)==7;
    int sigok=b.reaped && WIFSIGNALED(b.status) && WTERMSIG(b.status)==SIGTERM;
    stop_owned(&a);stop_owned(&b);
    FILE *fp=fopen("monitor-selftest.json","w");
    if(!fp)return 2;
    fprintf(fp,"{\"exit7_observed\":%s,\"sigterm_observed\":%s,\"scope\":\"owned calibration children, not resource-manager crash injection\"}\n",
            exitok ? "true":"false",sigok ? "true":"false");
    fclose(fp);return exitok && sigok ? 0:2;
}
int main(int argc,char **argv) {
    if(argc==2 && !strcmp(argv[1],"--exit7"))return 7;
    if(argc==2 && !strcmp(argv[1],"--term")) { raise(SIGTERM);return 2; }
    signal(SIGTERM,on_signal);signal(SIGINT,on_signal);signal(SIGHUP,on_signal);
    if(argc==2 && !strcmp(argv[1],"--peer"))return peer();
    if(argc!=1)return 2;
    if(access(LAB_DEVICE_PATH,F_OK)==0) { fputs("Existing lab device; refusing takeover\n",stderr);return 2; }
    if(selftest())return 2;
    child_t target={0},worker={0},heartbeat={0};
    FILE *log=fopen("monitor.jsonl","w");
    if(!log)return 2;
    char *targetargs[]={"./lab-resmgr",NULL};
    char *peerargs[]={"./lab-monitor","--peer",NULL};
    char *workerargs[]={"./lab-fuzzer",NULL};
    int ready=0,watchdog=0,rc=2;
    uint64_t start=now_ns(),deadline=start+15000000000ULL;
    const char *ts="unknown",*ws="unknown",*ps="unknown";
    if(launch(&target,targetargs[0],targetargs) || launch(&heartbeat,peerargs[0],peerargs))goto done;
    for(unsigned i=0;i<250 && !interrupted;i++) {
        ts=poll_child(&target);
        if(strcmp(ts,"running"))break;
        if(access(LAB_DEVICE_PATH,F_OK)==0) { ready=1;break; }
        nap();
    }
    if(!ready || launch(&worker,workerargs[0],workerargs))goto done;
    do {
        ts=poll_child(&target);ws=poll_child(&worker);ps=poll_child(&heartbeat);
        fprintf(log,"{\"monitor_pid\":%d,\"mono_ns\":%" PRIu64 ",\"target_pid\":%d,\"target_state\":\"%s\","
                "\"worker_pid\":%d,\"worker_state\":\"%s\",\"peer_pid\":%d,\"peer_state\":\"%s\"}\n",
                (int)getpid(),now_ns(),(int)target.pid,ts,(int)worker.pid,ws,(int)heartbeat.pid,ps);
        fflush(log);
        if(strcmp(ts,"running") || strcmp(ps,"running") || strcmp(ws,"running"))break;
        if(now_ns()>=deadline) { watchdog=1;break; }
        nap();
    } while(!interrupted);
    rc=!interrupted && !watchdog && !strcmp(ts,"running") && !strcmp(ps,"running") &&
       worker.reaped && WIFEXITED(worker.status) && WEXITSTATUS(worker.status)==0 ? 0:2;
done:
    {
        FILE *summary=fopen("monitor-summary.json","w");
        if(summary) {
            fprintf(summary,"{\"backend\":\"qnx-native\",\"monitor_pid\":%d,\"target_pid\":%d,\"worker_pid\":%d,"
                "\"peer_pid\":%d,\"target_state_before_cleanup\":\"%s\",\"worker_state\":\"%s\","
                "\"peer_state_before_cleanup\":\"%s\",\"worker_exit_code\":%d,\"target_exit_code\":%d,"
                "\"target_signal\":%d,\"watchdog_expired\":%s,\"interrupted\":%s,"
                "\"cleanup_expected\":true,\"system_service_probe\":null,\"isolation_verdict\":\"INCONCLUSIVE\"}\n",
                (int)getpid(),(int)target.pid,(int)worker.pid,(int)heartbeat.pid,ts,ws,ps,
                worker.reaped && WIFEXITED(worker.status) ? WEXITSTATUS(worker.status):-1,
                target.reaped && WIFEXITED(target.status) ? WEXITSTATUS(target.status):-1,
                target.reaped && WIFSIGNALED(target.status) ? WTERMSIG(target.status):0,
                watchdog ? "true":"false",interrupted ? "true":"false");
            fclose(summary);
        } else rc=2;
    }
    stop_owned(&worker);stop_owned(&target);stop_owned(&heartbeat);
    fclose(log);
    return rc;
}
