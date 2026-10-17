#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/neutrino.h>
#include <time.h>
#include <unistd.h>
#include "lab_protocol.h"
#include "lab_policy.h"

static uint64_t now_ns(void)
{
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) exit(2);
    return (uint64_t)t.tv_sec*1000000000ULL+(uint64_t)t.tv_nsec;
}
static int nibble(char c)
{
    if(c>='0' && c<='9') return c-'0';
    if(c>='a' && c<='f') return c-'a'+10;
    return -1;
}
static int authorized(void) {
    char text[64]={0};
    FILE *fp=fopen("authorization.txt","r");
    if(!fp)return 0;
    size_t n=fread(text,1,sizeof(text)-1,fp);
    int ok=!ferror(fp) && feof(fp) && n==strlen("lab-resmgr-01 allow\n") &&
        !memcmp(text,"lab-resmgr-01 allow\n",n);
    fclose(fp);return ok;
}
static int authorization_barrier(unsigned sequence) {
    FILE *fp=fopen("auth-request.next","w");
    if(!fp)return 0;
    int bad=fprintf(fp,"%u\n",sequence)<0;
    if(fclose(fp))bad=1;
    if(bad || rename("auth-request.next","auth-request.txt"))return 0;
    uint64_t deadline=now_ns()+2000000000ULL;
    while(now_ns()<deadline) {
        fp=fopen("auth-ack.txt","r");
        if(fp) {
            unsigned ack=0;char extra;int parsed=fscanf(fp,"%u %c",&ack,&extra);fclose(fp);
            if(parsed!=1 || ack>sequence)return 0;
            if(ack==sequence)return 1;
        } else if(errno!=ENOENT)return 0;
        struct timespec pause={0,1000000};nanosleep(&pause,NULL);
    }
    return 0;
}
static int policy_selftest(void) {
    lab_policy_t p={0};int ok=1;
    for(unsigned i=0;i<10;i++)ok &= lab_policy_check(&p,1,"lab-resmgr-01",0,1,4,0,0,4,100,1)==LAB_ALLOW;
    ok &= lab_policy_check(&p,1,"lab-resmgr-01",0,1,4,0,0,4,999999999,1)==LAB_RATE_LIMIT;
    ok &= lab_policy_check(&p,1,"lab-resmgr-01",1,1,4,0,0,4,100,1)==LAB_ALLOW;
    ok &= lab_policy_check(&p,1,"lab-resmgr-01",0,1,4,0,0,4,1000000100ULL,1)==LAB_ALLOW;
    ok &= lab_policy_check(&p,0,"lab-resmgr-01",0,1,4,0,0,4,1000000101ULL,1)==LAB_SCOPE_DENY;
    ok &= lab_policy_check(&p,1,"unknown",0,1,4,0,0,4,1000000101ULL,1)==LAB_SCOPE_DENY;
    ok &= lab_policy_check(&p,1,"lab-resmgr-01",2,1,0,0,0,0,100,1)==LAB_ALLOW;
    ok &= lab_policy_check(&p,1,"lab-resmgr-01",3,1,0xffffffff,0,0,4,100,1)==LAB_BLOCK;
    ok &= p.count[3]==0;
    FILE *fp=fopen("policy-selftest.json","w");
    if(!fp)return 0;
    fprintf(fp,"{\"passed\":%s,\"clock_source\":\"synthetic exact-boundary calibration; live traffic uses CLOCK_MONOTONIC\"}\n",ok ? "true":"false");
    fclose(fp);return ok;
}
int main(void)
{
    FILE *input=fopen("corpus.tsv","r"), *output=fopen("fuzz-results.jsonl","w");
    if(!input || !output) { perror("corpus/result"); return 2; }
    int fd=-1,version=1,defend=0,auth_control=0;
    lab_policy_t policy={0};
    FILE *mode=fopen("defense-mode.txt","r");
    if(mode) {
        char setting[32];
        if(!fgets(setting,sizeof(setting),mode) || (strcmp(setting,"baseline\n") && strcmp(setting,"defense\n") && strcmp(setting,"baseline-auth\n") && strcmp(setting,"defense-auth\n")))return 2;
        defend=!strncmp(setting,"defense",7);auth_control=strstr(setting,"-auth")!=NULL;version=2;fclose(mode);
        if(auth_control && access("authorization-plan.txt",F_OK))return 2;
        if(!policy_selftest())return 2;
    } else {
        fd=open(LAB_DEVICE_PATH,O_RDWR);
        if(fd<0) { perror("open owned lab device"); return 2; }
    }
    pid_t pid=getpid();
    FILE *meta=fopen("fuzzer-meta.json","w");
    if(!meta)return 2;
    fprintf(meta,"{\"EINVAL\":%d,\"EMSGSIZE\":%d,\"ETIMEDOUT\":%d,\"ENOTTY\":%d,\"max_cases\":200,\"max_actual_payload\":65,\"schema_version\":%d,\"defense_enabled\":%s}\n",
            EINVAL,EMSGSIZE,ETIMEDOUT,ENOTTY,version,defend ? "true":"false");
    fclose(meta);
    char line[512]; unsigned count=0;
    while(fgets(line,sizeof(line),input)) {
        char id[32],mutation[32],hex[131];
        lab_request_t req;
        unsigned char wire[LAB_HEADER_SIZE+65],expected[sizeof(wire)];
        memset(&req,0,sizeof(req)); memset(wire,0,sizeof(wire));
        if(++count>200 || !strchr(line,'\n')) { fputs("bounded corpus violated\n",stderr); return 2; }
        int consumed=0,fields;unsigned session=0,delay_ms=0;
        if(version==2) fields=sscanf(line,"%31s %31s %" SCNu32 " %" SCNu32 " %" SCNd32 " %" SCNu32 " %130s %u %u %n",
                  id,mutation,&req.operation,&req.declared_length,&req.offset,&req.flags,hex,&session,&delay_ms,&consumed);
        else fields=sscanf(line,"%31s %31s %" SCNu32 " %" SCNu32 " %" SCNd32 " %" SCNu32 " %130s %n",
                  id,mutation,&req.operation,&req.declared_length,&req.offset,&req.flags,hex,&consumed);
        if(fields!=(version==2 ? 9:7) || session>=8 || delay_ms>1100)return 2;
        if(line[consumed]!='\0' || strspn(id,"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")!=strlen(id)) return 2;
        if(strcmp(mutation,"normal") && strcmp(mutation,"boundary") && strcmp(mutation,"field") && strcmp(mutation,"combination")) return 2;
        size_t actual=strcmp(hex,"-")==0 ? 0 : strlen(hex)/2;
        if(actual>65 || (strcmp(hex,"-") && strlen(hex)%2)) return 2;
        for(size_t j=0;j<actual;j++) {
            int high=nibble(hex[j*2]),low=nibble(hex[j*2+1]);
            if(high<0 || low<0) return 2;
            wire[LAB_HEADER_SIZE+j]=(unsigned char)((high<<4)|low);
        }
        memcpy(wire,&req,LAB_HEADER_SIZE);
        size_t bytes=LAB_HEADER_SIZE+actual;
        memcpy(expected,wire,bytes);
        if(delay_ms) { struct timespec pause={delay_ms/1000,(long)(delay_ms%1000)*1000000};nanosleep(&pause,NULL); }
        if(auth_control && !authorization_barrier(count)) { fputs("Authorization barrier failed; no next IPC\n",stderr);return 2; }
        uint64_t begin=now_ns(), timeout=2000000000ULL;
        int auth=version==1 ? 1:authorized();
        lab_decision_t decision=version==1 ? LAB_ALLOW:lab_policy_check(&policy,auth,"lab-resmgr-01",session,
            req.operation,req.declared_length,req.offset,req.flags,actual,begin,defend);
        int forwarded=decision==LAB_ALLOW,rc=-1;
        if(forwarded) {
            if(fd<0)fd=open(LAB_DEVICE_PATH,O_RDWR);
            if(fd<0) { perror("open owned lab device");return 2; }
            if(TimerTimeout(CLOCK_MONOTONIC,_NTO_TIMEOUT_SEND|_NTO_TIMEOUT_REPLY,NULL,&timeout,NULL)) return 2;
            rc=devctl(fd,LAB_DCMD_ECHO,wire,bytes,NULL);
        }
        uint64_t end=now_ns();
        const char *outcome=!forwarded ? "NOT_SENT" : (rc==EOK ? "REPLY" : (rc==ETIMEDOUT ? "TIMEOUT" :
            ((rc==EINVAL || rc==EMSGSIZE || rc==ENOTTY) ? "ERROR_REPLY":"IPC_ERROR")));
        int matches=rc==EOK && memcmp(wire,expected,bytes)==0;
        printf("case=%s outcome=%s\n",id,outcome);
        fprintf(output,"{\"case_id\":\"%s\",\"mutation\":\"%s\",\"backend\":\"qnx-native\","
                "\"fuzzer_pid\":%d,\"operation\":%" PRIu32 ",\"declared_length\":%" PRIu32 ","
                "\"offset\":%" PRId32 ",\"flags\":%" PRIu32 ",\"payload_hex\":\"%s\","
                "\"actual_payload_bytes\":%zu,\"dcmd_bytes\":%zu,\"return_code\":%d,"
                "\"begin_ns\":%" PRIu64 ",\"end_ns\":%" PRIu64 ",\"elapsed_ns\":%" PRIu64 ","
                "\"outcome\":\"%s\",\"reply_matches\":%s,\"forwarded\":%s,\"decision\":\"%s\","
                "\"session_index\":%u,\"delay_before_ms\":%u,\"authorized\":%s}\n",
                id,mutation,(int)pid,req.operation,req.declared_length,req.offset,req.flags,
                actual ? hex : "",actual,bytes,rc,begin,end,end-begin,outcome,matches ? "true":"false",
                forwarded ? "true":"false",lab_decision_name(decision),session,delay_ms,auth ? "true":"false");
        fflush(output);
        if(rc==ETIMEDOUT) { fclose(output); close(fd); return 3; }
        struct timespec delay={0,10000000};
        nanosleep(&delay,NULL);
    }
    int bad=ferror(input) || !count;
    fclose(input);fclose(output);if(fd>=0)close(fd);
    return bad ? 2 : 0;
}
