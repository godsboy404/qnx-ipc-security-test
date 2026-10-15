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
int main(void)
{
    FILE *input=fopen("corpus.tsv","r"), *output=fopen("fuzz-results.jsonl","w");
    if(!input || !output) { perror("corpus/result"); return 2; }
    int fd=open(LAB_DEVICE_PATH,O_RDWR);
    if(fd<0) { perror("open owned lab device"); return 2; }
    pid_t pid=getpid();
    char line[512]; unsigned count=0;
    while(fgets(line,sizeof(line),input)) {
        char id[32],mutation[32],hex[131];
        lab_request_t req;
        unsigned char wire[LAB_HEADER_SIZE+65],expected[sizeof(wire)];
        memset(&req,0,sizeof(req)); memset(wire,0,sizeof(wire));
        if(++count>200 || !strchr(line,'\n')) { fputs("bounded corpus violated\n",stderr); return 2; }
        int consumed=0;
        if(sscanf(line,"%31s %31s %" SCNu32 " %" SCNu32 " %" SCNd32 " %" SCNu32 " %130s %n",
                  id,mutation,&req.operation,&req.declared_length,&req.offset,&req.flags,hex,&consumed)!=7) return 2;
        if(line[consumed]!='\0' || strspn(id,"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")!=strlen(id)) return 2;
        if(strcmp(mutation,"normal") && strcmp(mutation,"boundary") && strcmp(mutation,"field") && strcmp(mutation,"combination")) return 2;
        size_t actual=strcmp(hex,"-")==0 ? 0 : strlen(hex)/2;
        if(actual>65 || (actual && strlen(hex)%2)) return 2;
        for(size_t j=0;j<actual;j++) {
            int high=nibble(hex[j*2]),low=nibble(hex[j*2+1]);
            if(high<0 || low<0) return 2;
            wire[LAB_HEADER_SIZE+j]=(unsigned char)((high<<4)|low);
        }
        memcpy(wire,&req,LAB_HEADER_SIZE);
        size_t bytes=LAB_HEADER_SIZE+actual;
        memcpy(expected,wire,bytes);
        uint64_t begin=now_ns(), timeout=2000000000ULL;
        if(TimerTimeout(CLOCK_MONOTONIC,_NTO_TIMEOUT_SEND|_NTO_TIMEOUT_REPLY,NULL,&timeout,NULL)) return 2;
        int rc=devctl(fd,LAB_DCMD_ECHO,wire,bytes,NULL);
        uint64_t end=now_ns();
        const char *outcome=rc==EOK ? "REPLY" : (rc==ETIMEDOUT ? "TIMEOUT" : "ERROR_REPLY");
        int matches=rc==EOK && memcmp(wire,expected,bytes)==0;
        printf("case=%s outcome=%s\n",id,outcome);
        fprintf(output,"{\"case_id\":\"%s\",\"mutation\":\"%s\",\"backend\":\"qnx-native\","
                "\"fuzzer_pid\":%d,\"operation\":%" PRIu32 ",\"declared_length\":%" PRIu32 ","
                "\"offset\":%" PRId32 ",\"flags\":%" PRIu32 ",\"payload_hex\":\"%s\","
                "\"actual_payload_bytes\":%zu,\"dcmd_bytes\":%zu,\"return_code\":%d,"
                "\"begin_ns\":%" PRIu64 ",\"end_ns\":%" PRIu64 ",\"elapsed_ns\":%" PRIu64 ","
                "\"outcome\":\"%s\",\"reply_matches\":%s}\n",
                id,mutation,(int)pid,req.operation,req.declared_length,req.offset,req.flags,
                actual ? hex : "",actual,bytes,rc,begin,end,end-begin,outcome,matches ? "true":"false");
        fflush(output);
        if(rc==ETIMEDOUT) { fclose(output); close(fd); return 3; }
        struct timespec delay={0,10000000};
        nanosleep(&delay,NULL);
    }
    int bad=ferror(input) || !count;
    fclose(input);fclose(output);close(fd);
    return bad ? 2 : 0;
}
