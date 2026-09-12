#!/usr/bin/env bash
# Persistent interpreter for the Mac-side interviewer/scorer (needs the natural-greek-sft `nsft` package): system python3 with the repo on PYTHONPATH.
export PYTHONPATH="$HOME/Projects/natural-greek-sft/src:$HOME/Projects/natural-greek-sft${PYTHONPATH:+:$PYTHONPATH}"
exec python3 "$@"
