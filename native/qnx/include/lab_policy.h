#ifndef LAB_POLICY_H
#define LAB_POLICY_H
#include <stdint.h>
#include <stddef.h>
#include <string.h>
/* SEC-01/03/04: single-threaded application gateway, eight bounded sessions.
 * Call with CLOCK_MONOTONIC before every forwarded request. */
typedef struct { uint64_t sent[8][10]; unsigned count[8]; } lab_policy_t;
typedef enum { LAB_ALLOW, LAB_BLOCK, LAB_RATE_LIMIT, LAB_SCOPE_DENY } lab_decision_t;
static inline const char *lab_decision_name(lab_decision_t d) {
    static const char *names[]={"ALLOW","BLOCK","RATE_LIMIT","SCOPE_DENY"};
    return names[d];
}
static inline lab_decision_t lab_policy_check(lab_policy_t *p, int authorized,
        const char *target, unsigned session, uint32_t operation,
        uint32_t declared, int32_t offset, uint32_t flags, size_t actual,
        uint64_t now, int defend) {
    if(!authorized || strcmp(target,"lab-resmgr-01") || session>=8) return LAB_SCOPE_DENY;
    if(!defend) return LAB_ALLOW; /* Bounded baseline only; scope still checked. */
    if(operation!=1 || flags || actual>64 || declared!=actual ||
       offset<0 || (uint32_t)offset>declared) return LAB_BLOCK;
    unsigned kept=0;
    for(unsigned i=0;i<p->count[session];i++) {
        if(now<p->sent[session][i]) return LAB_SCOPE_DENY; /* Fail closed on clock regression. */
        if(now-p->sent[session][i]<1000000000ULL)
            p->sent[session][kept++]=p->sent[session][i];
    }
    p->count[session]=kept;
    if(kept==10) return LAB_RATE_LIMIT;
    p->sent[session][p->count[session]++]=now;
    return LAB_ALLOW;
}
#endif
