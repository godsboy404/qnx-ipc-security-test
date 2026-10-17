#!/bin/sh
set -u
PATH=/proc/boot:/bin:/usr/bin:/sbin:/usr/sbin
export PATH
test ! -e /dev/ipcsec-lab || exit 2
chmod 700 lab-resmgr lab-recovery || exit 2
case "${1:-stop}" in
  stop) ./lab-recovery >native-stdout.txt 2>native-stderr.txt & ;;
  stall) ./lab-recovery --stall >native-stdout.txt 2>native-stderr.txt & ;;
  *) exit 2 ;;
esac
owned_monitor=$!
trap 'kill -TERM "$owned_monitor" 2>/dev/null; wait "$owned_monitor" 2>/dev/null; exit 2' HUP INT TERM
wait "$owned_monitor"
result=$?
trap - HUP INT TERM
exit "$result"
