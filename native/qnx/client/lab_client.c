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

static uint64_t monotonic_ns(void)
{
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t) == -1) { perror("clock_gettime"); exit(2); }
    return (uint64_t)t.tv_sec * 1000000000ULL + (uint64_t)t.tv_nsec;
}

int main(int argc, char **argv)
{
    long count = 100;
    int empty = 0;
    if (argc > 1) {
        char *end = NULL;
        count = strtol(argv[1], &end, 10);
        if (*end || count < 1 || count > 1000) { fputs("count must be 1..1000\n", stderr); return 2; }
    }
    if (argc > 2) {
        if (strcmp(argv[2], "--empty") != 0) return 2;
        empty = 1;
    }
    int fd = open(LAB_DEVICE_PATH, O_RDWR);
    if (fd == -1) { perror("open lab device"); return 2; }
    for (long i = 0; i < count; ++i) {
        lab_request_t request, expected;
        memset(&request, 0, sizeof(request));
        request.operation = LAB_OP_ECHO;
        request.declared_length = empty ? 0 : 4;
        if (!empty) memcpy(request.payload, "ping", 4);
        expected = request;
        const size_t wire_bytes = LAB_HEADER_SIZE + request.declared_length;
        uint64_t timeout = 2000000000ULL;
        uint64_t before = monotonic_ns();
        if (TimerTimeout(CLOCK_MONOTONIC, _NTO_TIMEOUT_SEND | _NTO_TIMEOUT_REPLY,
                         NULL, &timeout, NULL) == -1) { perror("TimerTimeout"); close(fd); return 2; }
        int rc = devctl(fd, LAB_DCMD_ECHO, &request, wire_bytes, NULL);
        uint64_t elapsed = monotonic_ns() - before;
        int ok = rc == EOK && memcmp(&request, &expected, wire_bytes) == 0;
        printf("{\"case_id\":\"NATIVE-%04ld\",\"backend\":\"qnx-native\","
               "\"criterion_id\":\"IPC-01\",\"dcmd_bytes\":%zu,\"payload_bytes\":%u,"
               "\"return_code\":%d,\"elapsed_ns\":%" PRIu64 ",\"status\":\"%s\"}\n",
               i, wire_bytes, expected.declared_length, rc, elapsed, ok ? "PASS" : "FAIL");
        if (!ok) { fprintf(stderr, "devctl/reply check failed: %s\n", strerror(rc)); close(fd); return 1; }
    }
    close(fd);
    return 0;
}
