#!/usr/bin/env bash
# Runs the three netlists in ngspice (batch mode) and writes plain-text
# results to results/data/. The netlists themselves contain no ngspice-only
# commands, so the same files open unchanged in LTspice.
#
# Usage (from the repo root or anywhere):  bash scripts/run_ngspice.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NET="$ROOT/netlists"
OUT="$ROOT/results/data"
mkdir -p "$OUT"

command -v ngspice >/dev/null || { echo "ngspice not found on PATH" >&2; exit 1; }

run() {   # $1 = netlist, $2 = ngspice commands after 'run'
  local netlist="$1" cmds="$2" ctl
  ctl="$(mktemp)"
  cat > "$ctl" <<EOF
* control wrapper
.control
set wr_singlescale
set wr_vecnames
set noaskquit
cd $NET
source $netlist
run
cd $OUT
$cmds
quit
.endc
.end
EOF
  echo "-> $netlist"
  ngspice -b "$ctl" > "$OUT/${netlist%.cir}.log" 2>&1 || {
    echo "ngspice failed on $netlist, see $OUT/${netlist%.cir}.log" >&2; rm -f "$ctl"; exit 1; }
  rm -f "$ctl"
}

run current_sense_tran.cir "wrdata tran.txt v(sense) v(vout)"
run current_sense_dc.cir   "wrdata dc.txt v(sense) v(vout)"
run current_sense_ac.cir   "let mag_db = db(v(vout))
let phase_deg = 180/pi*cph(v(vout))
wrdata ac.txt mag_db phase_deg"

echo "Done. Results in results/data/"
