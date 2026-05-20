#!/usr/bin/env python3
"""
GRIDLAND Mycelium v2 — Change Logging Script

Usage:
  python3 .mycelium/record.py \
    --agent horizon \
    --phase primary|critique|refined|pm_review|qa_gate \
    --file src/frontend/cesium/entities/AircraftEntity.js \
    --action created|modified|reviewed|gate_pass|gate_fail|assigned \
    --rationale "Why this change was made and what it does" \
    [--critique_of myc_YYYYMMDDHHMMSS0000] \
    [--department discovery|visualization|pipeline|context|quality|none]

Output:
  Appends to .mycelium/log.json (machine-readable)
  Appends to .mycelium/CHANGELOG.md (human-readable)
"""

import json
import os
import argparse
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MYCELIUM_LOG = os.path.join(SCRIPT_DIR, 'log.json')
MYCELIUM_MD = os.path.join(SCRIPT_DIR, 'CHANGELOG.md')


def load_log():
    if not os.path.exists(MYCELIUM_LOG):
        return []
    with open(MYCELIUM_LOG, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_log(entries):
    with open(MYCELIUM_LOG, 'w') as f:
        json.dump(entries, f, indent=2)


def append_changelog(entry):
    timestamp = entry['timestamp']
    agent = entry['agent']
    phase = entry['phase']
    filename = os.path.basename(entry['file'])
    rationale = entry['rationale']
    entry_id = entry['id']

    critique_line = ''
    if entry.get('critique_of'):
        critique_line = f"\n**Critiques:** {entry['critique_of']}"

    line = (
        f"\n### {timestamp} — {agent} ({phase}) — `{filename}`\n"
        f"**Entry ID:** {entry_id}{critique_line}\n"
        f"{rationale}\n"
        f"---\n"
    )
    with open(MYCELIUM_MD, 'a') as f:
        f.write(line)


def main():
    p = argparse.ArgumentParser(
        description='Record a Mycelium change log entry for GRIDLAND'
    )
    p.add_argument('--agent', required=True,
                   help='Agent name (nexus, atlas, echo, horizon, prism, pulse, relay, cartographer, meridian, sentinel, arbiter)')
    p.add_argument('--phase', required=True,
                   choices=['primary', 'critique', 'refined', 'pm_review', 'qa_gate'],
                   help='Lifecycle phase of this entry')
    p.add_argument('--file', required=True,
                   help='File path that was created or modified')
    p.add_argument('--action', required=True,
                   help='Action taken (created, modified, reviewed, gate_pass, gate_fail, assigned, routed)')
    p.add_argument('--rationale', required=True,
                   help='Explanation of what was done and why. Be specific.')
    p.add_argument('--critique_of', default=None,
                   help='ID of the Mycelium entry this is critiquing (critics only)')
    p.add_argument('--department', default='unknown',
                   choices=['discovery', 'visualization', 'pipeline', 'context', 'quality', 'none', 'unknown'],
                   help='Department this agent belongs to')
    p.add_argument('--diff_summary', default=None,
                   help='Optional brief summary of what changed in the file')
    p.add_argument('--success_criteria', default=None,
                   help='Optional: what does success look like for this change?')

    args = p.parse_args()

    entries = load_log()
    now = datetime.now(timezone.utc)
    entry_id = f"myc_{now.strftime('%Y%m%d%H%M%S')}{len(entries):04d}"

    entry = {
        'id': entry_id,
        'timestamp': now.isoformat(),
        'agent': args.agent,
        'department': args.department,
        'phase': args.phase,
        'file': args.file,
        'action': args.action,
        'rationale': args.rationale,
        'critique_of': args.critique_of,
        'critique_pending': args.phase == 'primary',
        'critique_id': None,
        'refined_id': None,
    }

    if args.diff_summary:
        entry['diff_summary'] = args.diff_summary
    if args.success_criteria:
        entry['success_criteria'] = args.success_criteria

    entries.append(entry)
    save_log(entries)
    append_changelog(entry)

    print(f"Mycelium entry recorded: {entry_id}")
    print(f"  Agent: {args.agent} | Phase: {args.phase} | File: {args.file}")
    return entry_id


if __name__ == '__main__':
    main()
