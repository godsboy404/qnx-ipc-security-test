#ifndef LAB_AUTH_CONTROL_H
#define LAB_AUTH_CONTROL_H
/* SEC-01 experiment controller. Only fixed files in this unique run directory. */
typedef struct {
    char states[200][32];
    unsigned count,done;
    FILE *events;
} auth_control_t;
static const char *auth_content(const char *state) {
    if(!strcmp(state,"allow"))return "lab-resmgr-01 allow\n";
    if(!strcmp(state,"deny"))return "lab-resmgr-01 deny\n";
    if(!strcmp(state,"malformed"))return "lab-resmgr-01 allow EXTRA\n";
    if(!strcmp(state,"wrong-target"))return "unregistered-target allow\n";
    return NULL;
}
static int auth_control_init(auth_control_t *c) {
    FILE *fp=fopen("authorization-plan.txt","r");
    if(!fp)return errno==ENOENT ? 0:-1;
    char state[32];
    while(fscanf(fp,"%31s",state)==1) {
        if(c->count==200 || (!auth_content(state) && strcmp(state,"missing"))) { fclose(fp);return -1; }
        strcpy(c->states[c->count++],state);
    }
    int bad=ferror(fp) || !c->count;fclose(fp);
    if(bad)return -1;
    c->events=fopen("authorization-events.jsonl","w");
    return c->events ? 0:-1;
}
static int auth_control_tick(auth_control_t *c) {
    if(!c->events)return 0;
    FILE *fp=fopen("auth-request.txt","r");
    if(!fp)return errno==ENOENT ? 0:-1;
    unsigned requested=0;char extra;
    int parsed=fscanf(fp,"%u %c",&requested,&extra);fclose(fp);
    if(parsed!=1)return -1;
    if(requested==c->done)return 0;
    if(requested!=c->done+1 || requested>c->count)return -1;
    const char *state=c->states[c->done],*content=auth_content(state);
    if(!strcmp(state,"missing")) {
        if(unlink("authorization.txt") && errno!=ENOENT)return -1;
    } else {
        fp=fopen("authorization.next","w");
        if(!fp)return -1;
        int bad=fputs(content,fp)==EOF;
        if(fclose(fp))bad=1;
        if(bad || rename("authorization.next","authorization.txt"))return -1;
    }
    /* Read back what the worker will observe, before releasing its next call. */
    char observed[64]={0};size_t size=0;int present=0;
    fp=fopen("authorization.txt","r");
    if(fp) {
        present=1;size=fread(observed,1,sizeof(observed)-1,fp);
        int bad=ferror(fp) || !feof(fp);fclose(fp);
        if(bad || !content || size!=strlen(content) || memcmp(observed,content,size))return -1;
    } else if(errno!=ENOENT || strcmp(state,"missing"))return -1;
    uint64_t applied=now_ns();
    fprintf(c->events,"{\"sequence\":%u,\"monitor_pid\":%d,\"applied_ns\":%" PRIu64 ",\"state\":\"%s\",\"file_present\":%s,\"content_hex\":\"",
        requested,(int)getpid(),applied,state,present ? "true":"false");
    for(size_t i=0;i<size;i++)fprintf(c->events,"%02x",(unsigned char)observed[i]);
    fputs("\"}\n",c->events);
    if(fflush(c->events))return -1;
    fp=fopen("auth-ack.next","w");
    if(!fp)return -1;
    int bad=fprintf(fp,"%u\n",requested)<0;
    if(fclose(fp))bad=1;
    if(bad || rename("auth-ack.next","auth-ack.txt"))return -1;
    c->done=requested;return 0;
}
#endif
