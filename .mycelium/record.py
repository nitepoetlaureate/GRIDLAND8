#!/usr/bin/env python3
"""Mycelium v3 — change log writer.

Two ways to record an entry:

  1. Per-file (legacy):
     python3 .mycelium/record.py --agent X --phase primary --file path \
       --action created --rationale "..." [--department ...] [--commit SHA]

  2. From a single commit's trailers (called by the post-commit hook):
     python3 .mycelium/record.py from-commit <sha>

     Reads Mycelium-* git trailers and writes ONE entry per file in the
     commit's diff. Trailers recognized:
       Mycelium-Agent
       Mycelium-Dept
       Mycelium-Phase
       Mycelium-Action            (default: modified)
       Mycelium-Rationale         (multiline allowed)
       Mycelium-Critique-Of       (id of primary being critiqued)

The log file (.mycelium/log.json) is the source of truth. CHANGELOG.md is
regenerated from it.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "log.json"
MD = ROOT / "CHANGELOG.md"

VALID_PHASES = {"primary", "critique", "refined", "pm_review", "qa_gate"}


def load_log() -> list[dict]:
    if not LOG.exists():
        return []
    try:
        with LOG.open() as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_log(entries: list[dict]) -> None:
    with LOG.open("w") as f:
        json.dump(entries, f, indent=2)


def rebuild_changelog(entries: list[dict]) -> None:
    header = ("# GRIDLAND Mycelium Changelog\n\n"
              "Generated from .mycelium/log.json. Do not edit by hand.\n\n---\n")
    lines = [header]
    for e in entries:
        critique = (f"\n**Critiques:** {e['critique_of']}"
                    if e.get("critique_of") else "")
        commit = f" [{e['commit'][:7]}]" if e.get("commit") else ""
        lines.append(
            f"\n### {e['timestamp']} — {e['agent']} ({e['phase']}) — "
            f"`{os.path.basename(e['file'])}`{commit}\n"
            f"**Entry ID:** {e['id']}{critique}\n"
            f"{e.get('rationale', '').strip()}\n"
            f"---\n"
        )
    MD.write_text("".join(lines))


def append(entry: dict) -> str:
    entries = load_log()
    now = datetime.now(timezone.utc)
    entry["id"] = entry.get("id") or f"myc_{now.strftime('%Y%m%d%H%M%S')}{len(entries):04d}"
    entry["timestamp"] = entry.get("timestamp") or now.isoformat()
    if entry.get("phase") not in VALID_PHASES:
        raise SystemExit(f"invalid phase: {entry.get('phase')!r}")
    entries.append(entry)
    save_log(entries)
    rebuild_changelog(entries)
    return entry["id"]


# ── from-commit mode ─────────────────────────────────────────────────────────

def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def _trailers(sha: str) -> dict[str, str]:
    """Parse Mycelium-* trailers using `git interpret-trailers --parse` against
    the commit body — works on git >= 2.13.
    """
    body = _git("show", "-s", "--format=%B", sha)
    if not body.strip():
        return {}
    parsed = subprocess.check_output(
        ["git", "interpret-trailers", "--parse"], input=body, text=True
    ).strip()
    trailers: dict[str, str] = {}
    current_key: str | None = None
    for line in parsed.splitlines():
        if not line:
            current_key = None
            continue
        # New trailer lines look like "Key: value"; continuation lines start
        # with whitespace.
        if line[:1] in (" ", "\t") and current_key is not None:
            trailers[current_key] += "\n" + line.strip()
            continue
        if ":" not in line:
            current_key = None
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        trailers.setdefault(key, value)
        current_key = key
    return trailers


def _files_in_commit(sha: str) -> list[tuple[str, str]]:
    out = _git("show", "--name-status", "--format=", sha)
    rows: list[tuple[str, str]] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t", 2)
        if len(parts) < 2:
            continue
        status = parts[0]
        path = parts[-1]
        rows.append((status, path))
    return rows


_STATUS_TO_ACTION = {
    "A": "created",
    "M": "modified",
    "D": "archived",
    "R": "modified",
    "C": "modified",
}


def from_commit(sha: str) -> None:
    trailers = _trailers(sha)
    agent = trailers.get("Mycelium-Agent")
    phase = trailers.get("Mycelium-Phase")
    if not agent or not phase:
        print("mycelium: commit missing Mycelium-Agent/Phase trailers; skip",
              file=sys.stderr)
        return
    dept = trailers.get("Mycelium-Dept", "none")
    action_default = trailers.get("Mycelium-Action") or None
    rationale = trailers.get("Mycelium-Rationale", "")
    critique_of = trailers.get("Mycelium-Critique-Of") or None
    timestamp = _git("show", "-s", "--format=%cI", sha)

    files = _files_in_commit(sha)
    if not files:
        return
    for status, path in files:
        action = action_default or _STATUS_TO_ACTION.get(status[0], "modified")
        append({
            "agent": agent,
            "department": dept,
            "phase": phase,
            "action": action,
            "file": path,
            "rationale": rationale,
            "critique_of": critique_of,
            "commit": sha,
            "timestamp": timestamp,
            "auto": True,
        })


# ── per-file CLI ────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] == "from-commit":
        if len(sys.argv) < 3:
            raise SystemExit("usage: record.py from-commit <sha>")
        from_commit(sys.argv[2])
        return

    p = argparse.ArgumentParser()
    p.add_argument("--agent", required=True)
    p.add_argument("--phase", required=True, choices=sorted(VALID_PHASES))
    p.add_argument("--file", required=True)
    p.add_argument("--action", required=True)
    p.add_argument("--rationale", required=True)
    p.add_argument("--critique_of", "--critique-of", dest="critique_of", default=None)
    p.add_argument("--department", "--dept", dest="department", default="none")
    p.add_argument("--commit", default=None)
    args = p.parse_args()
    entry = {
        "agent": args.agent,
        "department": args.department,
        "phase": args.phase,
        "file": args.file,
        "action": args.action,
        "rationale": args.rationale,
        "critique_of": args.critique_of,
        "commit": args.commit,
        "auto": False,
    }
    entry_id = append(entry)
    print(entry_id)


if __name__ == "__main__":
    main()
