#ifndef LAB_PROTOCOL_H
#define LAB_PROTOCOL_H
#include <stdint.h>
/* Application payload draft only, not a QNX _IO_* wire header.
 * Approve devctl framing or explicit private-message dispatch before implementation.
 * Do not send this struct directly to arbitrary resource managers.
 */
#define LAB_MAX_PAYLOAD 64u
#define LAB_OP_ECHO 1u
typedef struct lab_request {
    uint32_t operation;
    uint32_t declared_length;
    int32_t offset;
    uint32_t flags;
    uint8_t payload[LAB_MAX_PAYLOAD];
} lab_request_t;
#endif
