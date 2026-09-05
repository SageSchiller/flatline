#!/usr/bin/env bash
# The six-campaign regression as one line (D162). Runs q1..q6 in parallel
# under their own data directories, waits, and prints the four things that
# matter: crashes or persona errors, where each campaign ended, the endings
# and bonds reached by play, and the commands each never typed.
set -u
cd "$(dirname "$0")"
PERSONAS=(q1_netrunner q2_fighter q3_face q4_explorer q5_drift q6_runcraft)
for f in "${PERSONAS[@]}"; do rm -rf "data/$f"; rm -f "logs/$f.done"; done
for f in "${PERSONAS[@]}"; do
  (timeout 900 python3 "$f.py" > "logs/$f.out" 2>&1; echo done > "logs/$f.done") &
done
wait
echo "== crashes and persona errors =="
grep -c "!!! CRASH\|!!! PERSONA ERROR" logs/q?_*.log
echo "== where each ended =="
for f in "${PERSONAS[@]}"; do tail -1 "logs/$f.out" | cut -c1-200; done
echo "== endings, bonds, doors =="
grep -h "^--- " logs/q?_*.log | grep -E "ENDING|bond partner|after the door" | cut -c1-120
echo "== never typed by any of them =="
python3 - <<'PY'
sets = []
for f in ('q1_netrunner','q2_fighter','q3_face','q4_explorer','q5_drift','q6_runcraft'):
    for line in open(f'logs/{f}.log', errors='replace'):
        if line.startswith('### never typed:'):
            sets.append(set(line.split(':', 1)[1].split()))
u = set.intersection(*sets) if sets else set()
print(len(u), ' '.join(sorted(u)))
PY
