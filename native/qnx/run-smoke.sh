#!/bin/sh
# Executes legal requests against this project's own device only.
set -eu
cd /data/ipcsec-lab
export PATH=/system/bin:/proc/boot:$PATH
server_pid=
cleanup() {
    if [ -n "$server_pid" ]; then
        kill "$server_pid" 2>/dev/null || true
        wait "$server_pid" 2>/dev/null || true
    fi
}
trap cleanup EXIT HUP INT TERM
if [ -e /dev/ipcsec-lab ]; then
    echo 'Device already present; refusing to replace an unknown existing server' >&2
    exit 2
fi
./hello-qnx > hello.txt
./lab-resmgr > resmgr.log 2>&1 &
server_pid=$!
waitfor /dev/ipcsec-lab 10
./lab-client 100 > normal.jsonl
./lab-client 1 --empty > empty.jsonl
cleanup
server_pid=
sleep 1
if [ -e /dev/ipcsec-lab ]; then
    echo 'Device path did not detach after owned server exit' >&2
    exit 2
fi
./lab-resmgr > resmgr-restart.log 2>&1 &
server_pid=$!
waitfor /dev/ipcsec-lab 10
./lab-client 100 > restarted.jsonl
echo 'SMOKE_OK normal=100 empty=1 restarted=100'
