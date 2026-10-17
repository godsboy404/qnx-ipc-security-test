#ifndef LAB_STALL_H
#define LAB_STALL_H
/* Own-service SIGSTOP/SIGCONT experiment. No system-service messages. */
static int stall_flag(const char *path) {
    FILE *fp=fopen(path,"w");if(!fp)return 0;
    return fclose(fp)==0;
}
static int stall_wait_flag(const char *path,uint64_t limit) {
    while(now_ns()<limit) {
        if(access(path,F_OK)==0)return 1;
        nap();
    }return 0;
}
static int stall_request(void) {
    /* Connect while the server is responsive: open/close can also require IPC. */
    int fd=open(LAB_DEVICE_PATH,O_RDWR);if(fd<0)return 2;
    FILE *result=fopen("stall-request.json","w"),*trace=fopen("stall-client-trace.jsonl","w");
    FILE *marker=fopen("stall-result.next","w");
    if(!result || !trace || !marker)return 2;
    if(fclose(marker))return 2;
    setvbuf(result,NULL,_IONBF,0);setvbuf(trace,NULL,_IONBF,0);
    pid_t client_pid=getpid();
    fprintf(trace,"{\"stage\":\"connected\",\"client_pid\":%d,\"mono_ns\":%" PRIu64 "}\n",(int)client_pid,now_ns());
    FILE *fp=fopen("stall-ready.next","w");if(!fp)return 2;
    fprintf(fp,"{\"client_pid\":%d,\"ready_ns\":%" PRIu64 "}\n",(int)getpid(),now_ns());
    if(fclose(fp) || rename("stall-ready.next","stall-ready.json"))return 2;
    if(!stall_wait_flag("stall-arm.ready",now_ns()+5000000000ULL))return 2;
    lab_request_t warm={0};warm.operation=LAB_OP_ECHO;warm.declared_length=4;memcpy(warm.payload,"gate",4);
    lab_request_t warm_expected=warm;
    uint64_t warm_begin=now_ns(),warm_timeout=2000000000ULL;
    if(TimerTimeout(CLOCK_MONOTONIC,_NTO_TIMEOUT_SEND|_NTO_TIMEOUT_REPLY,NULL,&warm_timeout,NULL))return 2;
    int warm_rc=devctl(fd,LAB_DCMD_ECHO,&warm,LAB_HEADER_SIZE+4,NULL);
    uint64_t warm_end=now_ns();
    int warm_matches=warm_rc==EOK && !memcmp(&warm,&warm_expected,LAB_HEADER_SIZE+4);
    fprintf(trace,"{\"stage\":\"checkpoint_request\",\"client_pid\":%d,\"begin_ns\":%" PRIu64 ",\"end_ns\":%" PRIu64 ",\"return_code\":%d,\"reply_matches\":%s}\n",(int)client_pid,warm_begin,warm_end,warm_rc,warm_matches ? "true":"false");
    if(!warm_matches)return 2;
    if(!stall_wait_flag("stall-go.ready",now_ns()+5000000000ULL))return 2;
    lab_request_t req={0};req.operation=LAB_OP_ECHO;req.declared_length=4;memcpy(req.payload,"ping",4);
    fprintf(trace,"{\"stage\":\"before_devctl\",\"mono_ns\":%" PRIu64 "}\n",now_ns());
    uint64_t timeout=2000000000ULL,begin=now_ns();
    if(TimerTimeout(CLOCK_MONOTONIC,_NTO_TIMEOUT_SEND|_NTO_TIMEOUT_REPLY,NULL,&timeout,NULL))return 2;
    int rc=devctl(fd,LAB_DCMD_ECHO,&req,LAB_HEADER_SIZE+4,NULL);
    uint64_t end=now_ns();
    fprintf(trace,"{\"stage\":\"devctl_returned\",\"return_code\":%d,\"mono_ns\":%" PRIu64 "}\n",rc,end);
    fprintf(result,"{\"client_pid\":%d,\"begin_ns\":%" PRIu64 ",\"end_ns\":%" PRIu64 ",\"return_code\":%d,\"configured_timeout_ns\":2000000000,\"outcome\":\"%s\"}\n",
        (int)client_pid,begin,end,rc,rc==ETIMEDOUT ? "TIMEOUT":"UNEXPECTED");
    if(fflush(result) || rename("stall-result.next","stall-result.ready"))return 2;
    /* Resume the service before closing its connection. */
    if(!stall_wait_flag("stall-resumed.ready",now_ns()+5000000000ULL))return 2;
    close(fd);fclose(result);fclose(trace);return rc==ETIMEDOUT ? 0:2;
}
static int stall_experiment(void) {
    if(access(LAB_DEVICE_PATH,F_OK)==0)return 2;
    signal(SIGTERM,on_signal);signal(SIGINT,on_signal);signal(SIGHUP,on_signal);
    child_t target={0},observer={0},before={0},blocked={0},after={0};int ok=0;
    active_target=&target;active_probe=&observer;deadline=now_ns()+15000000000ULL;
    events=fopen("stall-events.jsonl","w");samples=fopen("stall-monitor.jsonl","w");
    if(!events || !samples)return 2;
    FILE *meta=fopen("stall-meta.json","w");if(!meta)return 2;
    fprintf(meta,"{\"backend\":\"qnx-native\",\"fault_kind\":\"controlled_SIGSTOP\",\"SIGSTOP\":%d,\"SIGCONT\":%d,\"ETIMEDOUT\":%d,\"monitor_pid\":%d,\"pause_watchdog_seconds\":6}\n",SIGSTOP,SIGCONT,ETIMEDOUT,(int)getpid());fclose(meta);
    char *server[]={"./lab-resmgr","--controlled-pause",NULL},*osprobe[]={"./lab-recovery","--probe",NULL};
    char *cb[]={"./lab-recovery","--request","before",NULL},*cs[]={"./lab-recovery","--stall-request",NULL},*ca[]={"./lab-recovery","--request","after",NULL};
    if(launch(&observer,osprobe) || launch(&target,server) || !wait_device(&target))goto cleanup;
    event("ready",&target,NULL);
    if(launch(&before,cb) || !wait_client(&before,"before",1))goto cleanup;
    event("before_complete",&target,&before);
    if(launch(&blocked,cs))goto cleanup;
    while(tick("connecting") && access("stall-ready.json",F_OK)!=0)nap();
    if(access("stall-ready.json",F_OK) || strcmp(state(&target),"running"))goto cleanup;
    event("client_connected",&target,&blocked);event("pause_requested",&target,NULL);
    /* Independent signal delivery releases our target even if a monitor call
     * unexpectedly blocks; disarm before the owned target is reaped. */
    owned_pause_pid=(sig_atomic_t)target.pid;signal(SIGALRM,on_signal);alarm(6);
    if(!stall_flag("pause-before-receive.ready") || !stall_flag("stall-arm.ready"))goto cleanup;
    while(tick("pausing") && !strcmp(state(&target),"running"))nap();
    if(strcmp(state(&target),"stopped") || WSTOPSIG(target.status)!=SIGSTOP)goto cleanup;
    event("paused",&target,NULL);
    if(!stall_flag("stall-go.ready"))goto cleanup;
    while(tick("blocked") && access("stall-result.ready",F_OK)!=0) {
        if(strcmp(state(&target),"stopped") || strcmp(state(&blocked),"running"))goto cleanup;
        nap();
    }
    if(access("stall-result.ready",F_OK) || strcmp(state(&target),"stopped"))goto cleanup;
    event("timeout_observed",&target,&blocked);event("resume_requested",&target,NULL);
    if(kill(target.pid,SIGCONT))goto cleanup;
    while(tick("resuming") && !strcmp(state(&target),"stopped"))nap();
    if(strcmp(state(&target),"running"))goto cleanup;
    owned_pause_pid=0;alarm(0);
    event("resumed",&target,NULL);
    if(!stall_flag("stall-resumed.ready") || !wait_client(&blocked,"resumed",1))goto cleanup;
    if(launch(&after,ca) || !wait_client(&after,"after",1))goto cleanup;
    event("after_complete",&target,&after);
    for(unsigned i=0;i<5;i++) { if(!tick("after"))goto cleanup;nap(); }
    ok=1;
cleanup:
    /* Continue our target even on a failed experiment before reaping clients. */
    if(target.pid>0 && !target.reaped)kill(target.pid,SIGCONT);
    owned_pause_pid=0;alarm(0);
    stop_owned(&before);stop_owned(&blocked);stop_owned(&after);stop_owned(&target);stop_owned(&observer);
    FILE *out=fopen("stall-cleanup.json","w");
    if(!out)ok=0;
    else {
        int clean=(target.pid<=0 || target.reaped) && (observer.pid<=0 || observer.reaped) &&
            (before.pid<=0 || before.reaped) && (blocked.pid<=0 || blocked.reaped) && (after.pid<=0 || after.reaped) && access(LAB_DEVICE_PATH,F_OK)!=0;
        fprintf(out,"{\"complete\":%s,\"all_owned_children_reaped\":%s,\"device_present\":%s,\"monitor_pid\":%d,\"target_pid\":%d,\"probe_pid\":%d,\"before_client_pid\":%d,\"blocked_client_pid\":%d,\"after_client_pid\":%d,\"pause_watchdog_triggered\":%s}\n",
            ok ? "true":"false",clean ? "true":"false",access(LAB_DEVICE_PATH,F_OK)==0 ? "true":"false",(int)getpid(),(int)target.pid,(int)observer.pid,(int)before.pid,(int)blocked.pid,(int)after.pid,pause_watchdog_triggered ? "true":"false");
        fclose(out);if(!clean)ok=0;
    }
    fclose(events);fclose(samples);return ok ? 0:2;
}
#endif
