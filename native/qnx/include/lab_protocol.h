#ifndef LAB_PROTOCOL_H
#define LAB_PROTOCOL_H
#include <stdint.h>
#include <stddef.h>
#include <devctl.h>
/* Application payload inside a devctl frame, only for our owned lab device.
 * Actual devctl bytes are LAB_HEADER_SIZE + declared_length (maximum 80).
 * This is not a raw QNX _IO_* header and must not be sent to system services. */
#define LAB_DEVICE_PATH "/dev/ipcsec-lab"
#define LAB_MAX_PAYLOAD 64u
#define LAB_OP_ECHO 1u
typedef struct lab_request {
    uint32_t operation;
    uint32_t declared_length;
    int32_t offset;
    uint32_t flags;
    uint8_t payload[LAB_MAX_PAYLOAD];
} lab_request_t;
#define LAB_HEADER_SIZE offsetof(lab_request_t, payload)
#define LAB_DCMD_ECHO __DIOTF(_DCMD_MISC, 0x51, lab_request_t)
_Static_assert(LAB_HEADER_SIZE == 16, "Protocol header ABI must be 16 bytes");
_Static_assert(sizeof(lab_request_t) == 80, "Protocol capacity ABI must be 80 bytes");
#endif
