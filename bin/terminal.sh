#!/usr/bin/env -S bash -l
setsid -f ghostty </dev/null >/dev/null 2>&1 || exit 1
exit 0
