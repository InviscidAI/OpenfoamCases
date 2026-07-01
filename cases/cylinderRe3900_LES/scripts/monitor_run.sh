#!/bin/sh
set -eu

cd "${0%/*}/.."

interval="${1:-0}"
status_file="${2:-run.status}"
log_file="${3:-${LOG_FILE:-log.pimpleFoam}}"

write_status()
{
    now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    log="$log_file"

    latest_time="none"
    latest_time="$(grep '^Time = ' "$log" 2>/dev/null | tail -1 | awk '{print $3}' || true)"
    [ -n "$latest_time" ] || latest_time="none"

    latest_co="none"
    latest_co="$(grep '^Courant Number' "$log" 2>/dev/null | tail -1 || true)"
    [ -n "$latest_co" ] || latest_co="none"

    latest_exec="none"
    latest_exec="$(grep '^ExecutionTime' "$log" 2>/dev/null | tail -1 || true)"
    [ -n "$latest_exec" ] || latest_exec="none"

    fatal="no"
    if grep -Eq 'FOAM FATAL|Floating point exception \(|Primary job.*terminated|exited on signal' "$log" 2>/dev/null; then
        fatal="yes"
    fi

    running="no"
    if pgrep -x pimpleFoam >/dev/null 2>&1 || pgrep -x mpirun >/dev/null 2>&1; then
        running="yes"
    fi

    size="0"
    mtime="none"
    if [ -f "$log" ]; then
        size="$(stat -c '%s' "$log")"
        mtime="$(stat -c '%y' "$log")"
    fi

    {
        printf 'checked_utc=%s\n' "$now"
        printf 'running=%s\n' "$running"
        printf 'fatal=%s\n' "$fatal"
        printf 'latest_time=%s\n' "$latest_time"
        printf 'latest_courant=%s\n' "$latest_co"
        printf 'latest_execution=%s\n' "$latest_exec"
        printf 'log_size_bytes=%s\n' "$size"
        printf 'log_mtime=%s\n' "$mtime"
    } > "$status_file"
}

if [ "$interval" = "0" ]; then
    write_status
    cat "$status_file"
    exit 0
fi

while :; do
    write_status
    sleep "$interval"
done
