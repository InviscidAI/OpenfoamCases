#!/bin/bash
# Source OpenFOAM if it is somewhere obvious, then run both checks. Convenience only --
# the checks themselves make no assumption about where OpenFOAM lives.
if [ -z "$WM_PROJECT_DIR" ]; then
    for c in /usr/lib/openfoam/openfoam*/etc/bashrc /opt/openfoam*/etc/bashrc \
             "$HOME"/OpenFOAM/OpenFOAM-*/etc/bashrc; do
        [ -f "$c" ] && { . "$c" >/dev/null 2>&1 || true; break; }
    done
fi
here=$(dirname "$0")
"$here/check_fields_parse.sh" && "$here/smoke_test.sh"
