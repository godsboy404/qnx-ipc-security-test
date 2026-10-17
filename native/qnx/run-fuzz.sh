#!/bin/sh
set -eu
# Uploaded into a new, unique /data/ipcsec-lab/fuzz/<run_id> directory.
# All child commands and the target device are fixed by the compiled lab monitor.
export PATH=/system/bin:/proc/boot:$PATH
if [ -e /dev/ipcsec-lab ]; then
    echo 'Existing lab device; refusing takeover' >&2
    exit 2
fi
chmod 700 lab-resmgr lab-fuzzer lab-monitor
monitor_pid=
cleanup() {
    if [ -n "$monitor_pid" ]; then
        kill "$monitor_pid" 2>/dev/null || true
        wait "$monitor_pid" 2>/dev/null || true
    fi
}
trap cleanup EXIT HUP INT TERM
./lab-monitor > native-stdout.txt 2> native-stderr.txt &
monitor_pid=$!
status=0
wait "$monitor_pid" || status=$?
monitor_pid=
exit "$status"
