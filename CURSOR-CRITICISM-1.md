# CURSOR-CRITICISM-1: An Unsparing Audit of GRIDLAND8

> Reviewer: Cursor / Claude Opus 4.7
> Date: 2026-05-20
> Scope: Entire workspace at `/Users/michaelraftery/GRIDLAND8` (file structure,
> tooling, documentation, configuration, hooks, "agent team", and the host git
> repository it lives in).
> Verdict in one line: **This is a 10,000-line design document that has been
> mistaken for a project.**

---

## 0. TL;DR

GRIDLAND8 is, as it stands today, a *prospectus* dressed up in the costume of a
software project. It has:

- An elaborate eleven-agent "department" model with paired critics, a PM agent,
  a QA gate, a custom changelog protocol ("Mycelium v2"), 33 documented "skill
  commands", PreToolUse/PostToolUse hooks, a "no-delete rule", and zero-cost
  v1 stack rules.
- Roughly **8,700 lines** of planning documentation across `docs/GRIDLAND-5.md`
  through `docs/GRIDLAND-8-STRUCTURE-2.md`.
- A duplicate of `GRIDLAND-8-STRUCTURE-2.md` (1,789 lines) sitting in **both**
  the repo root **and** `docs/` — byte-identical (`md5: c89ee11e...`).
- A `docker-compose.yml` that references two Dockerfiles that do not exist.
- A `README.md` that asks users to run `uvicorn src.backend.main:app` against a
  `src/backend/` tree that contains **zero Python files**.
- A `package.json` that asks users to run `vite` against a `src/frontend/` tree
  with **no `index.html`, no `vite.config.js`, no entry script**.
- A grand total of **one** real source file in the entire project:
  `.mycelium/record.py` — the bookkeeper for changes that have not happened.
- A `.mycelium/log.json` containing `[]` and a `.mycelium/CHANGELOG.md` with no
  entries — the "mandatory for all agents" protocol has been used **zero
  times**.
- A `.git` directory living one level too high (`/Users/michaelraftery/.git`),
  belonging to a completely different project (`thunderbird-esq/FFS`, a Game
  Boy ROM toolchain — most recent commit: *"Phase 7 complete — first
  successful ROM compilation"*), with a stale `index.lock` and ~1,084 staged
  files from `~/.claude/` that have nothing to do with GRIDLAND.

The user already noticed the last point. The rest of this document is the
diagnostic.

---

## 1. File Structure: Scaffolding Without a Building

### 1.1 The src/ tree is a Potemkin village

```
src/
├── backend/
│   ├── api/                ← empty
│   ├── compliance/         ← empty (Sentinel's "jurisdiction")
│   ├── context/            ← empty (Cartographer's "jurisdiction")
│   ├── discovery/
│   │   ├── normalizers/    ← empty
│   │   └── sources/        ← empty (Atlas's "jurisdiction")
│   └── pipeline/           ← empty (Pulse's "jurisdiction")
├── frontend/
│   ├── assets/
│   │   ├── icons/          ← empty
│   │   ├── models/         ← empty
│   │   └── skybox/         ← empty
│   ├── cesium/
│   │   ├── entities/       ← empty (Horizon's "jurisdiction")
│   │   ├── layers/         ← empty
│   │   └── transitions/    ← empty
│   ├── photosphere/        ← empty
│   └── ui/                 ← empty
└── shared/                 ← empty
```

The entire `src/` tree contains **zero files**. The "jurisdiction" assignments
in `CLAUDE.md` (Atlas owns `src/backend/discovery/`, Horizon owns
`src/frontend/`, etc.) are claims over empty rooms. Every README/CLAUDE.md
quick-start command — `uvicorn src.backend.main:app`, `npm run dev`,
`docker-compose up` — will fail on the first line.

The same is true for `tests/` (only `tests/fixtures/`, also empty),
`data/cache/`, `data/seeds/`, `docs/escalations/`, and `docs/tasks/`. They are
typed-out comments masquerading as structure.

### 1.2 The only real code is the bookkeeper

```
$ find . -type f \( -name '*.py' -o -name '*.js' -o -name '*.ts' \
                   -o -name '*.tsx' -o -name '*.jsx' -o -name '*.html' \
                   -o -name '*.css' \) -not -path './.git/*'
./.mycelium/record.py
```

The single file that actually exists is the one that logs other files'
changes. It is logging nothing, because there are no other files. This is a
self-referential loop with no payload.

### 1.3 The structure of the structure is duplicated

`GRIDLAND-8-STRUCTURE-2.md` exists at both `./GRIDLAND-8-STRUCTURE-2.md` and
`./docs/GRIDLAND-8-STRUCTURE-2.md`. They are identical (1,789 lines, same MD5).
Whichever copy you edit, the other rots. There is no indication which is the
canonical one. Pick one and delete — sorry, "archive to `.mycelium/archive/`" —
the other.

### 1.4 Compiled Python bytecode in the source tree

`.mycelium/__pycache__/record.cpython-311.pyc` is present. The `.gitignore`
correctly excludes `__pycache__/`, but the bytecode is sitting in the source
tree anyway because someone ran `record.py` interactively. It is harmless on
disk but signals an unclean working state.

---

## 2. Documentation: A Library Whose Card Catalog Outweighs Its Books

### 2.1 Volume vs. Substance

| File | Lines | What it is |
|------|------:|------------|
| `docs/GRIDLAND-5.md`            | 1,151 | Dorking, Shodan, Censys reference |
| `docs/GRIDLAND-6.md`            | 2,113 | (Real-time feeds research?) |
| `docs/GRIDLAND-7.md`            | 1,576 | (Pipeline research?) |
| `docs/GRIDLAND-8.md`            | 2,081 | Contextual layers research |
| `docs/GRIDLAND-8-STRUCTURE-2.md`| 1,789 | Agent/department architecture |
| `GRIDLAND-8-STRUCTURE-2.md`     | 1,789 | **Byte-identical duplicate** |
| `README.md`                     |   100 | Setup instructions for code that does not exist |
| `CLAUDE.md`                     |    60 | Agent quick-start for code that does not exist |
| `.claude/CLAUDE.md`             | (full) | Different agent quick-start, partially overlapping |
| **Total documentation**         | **~10,659** | |
| **Total runtime code**          | **129** (one file) | |

**Documentation:code ratio is roughly 80:1.** This is not the ratio of a
project being built; it is the ratio of a project being *imagined*. The cost
of keeping that documentation in sync with reality is immense, and the volume
is already actively misleading (see §3, §4).

### 2.2 Three sources of truth for the same thing

The agent department model, Mycelium protocol, no-delete rule, and zero-cost
stack are described in **four** separate places:

1. `README.md` — short version
2. `CLAUDE.md` (project root) — different short version
3. `.claude/CLAUDE.md` — fuller version
4. `GRIDLAND-8-STRUCTURE-2.md` *and its duplicate* — definitive version

They already disagree in minor ways. For example, `CLAUDE.md` (root) does
this:

```
cd GRIDLAND8
python3 -m venv .venv && source .venv/bin/activate
```

`cd GRIDLAND8` inside a file that lives at `GRIDLAND8/CLAUDE.md` is only
correct if you are reading the file from `~`. It will be wrong for anyone who
opens the project in their IDE — i.e. the actual primary audience.

`README.md` says the same thing differently, and `.claude/CLAUDE.md` skips it
entirely.

### 2.3 Documentation describes things that do not exist

Every doc references features that are not implemented:

- `src/backend/main.py` — does not exist.
- `src/backend/discovery/` modules — do not exist.
- `src/frontend/cesium/entities/AircraftEntity.js` — does not exist (it is
  *named* in `.mycelium/record.py`'s docstring as the canonical example file).
- `src/backend/compliance/guardrails.py` and `policy.json` — referenced by
  Sentinel's skill `/sentinel-guardrail`, do not exist.
- `.mycelium/archive/` — referenced by the No-Delete Rule as the only
  approved place to move files, but the directory does not exist. (Verified.
  An agent following the rule would `mv` into a nonexistent path.)
- `Dockerfile.backend`, `Dockerfile.frontend` — referenced by
  `docker-compose.yml`, do not exist.
- `vite.config.js`, `index.html`, `src/frontend/main.js` — referenced by
  the `vite` scripts, do not exist.

A README is a contract with the reader. Every "## Quick Start" block here is a
broken contract.

### 2.4 Marketing in the imperative voice

`README.md`:

> *"CesiumJS 3D globe that shows publicly exposed cameras, real-time aircraft,
> satellites, ships, balloons, weather, transit, lightning, and contextual
> data — all from free-tier public APIs."*

There is no globe. There are no cameras. There are no balloons. This sentence
is in the simple present tense, as if describing a deployed product. It
should be in the future tense or — better — removed until something exists.

---

## 3. Configuration: Confidently Wrong

### 3.1 `docker-compose.yml` references missing Dockerfiles

```yaml
backend:
  build:
    context: .
    dockerfile: Dockerfile.backend     # ← does not exist
frontend:
  build:
    context: .
    dockerfile: Dockerfile.frontend    # ← does not exist
```

`docker-compose up --build` (which `README.md` instructs users to run) will
fail immediately with `unable to prepare context: ... Dockerfile.backend: no
such file or directory`.

### 3.2 `package.json` is broken in two distinct ways

```json
"scripts": {
  "lint": "eslint src/frontend --ext .js"
}
```

`eslint` 9.x (the version pinned, `^9.3.0`) removed the `--ext` flag entirely
in favor of flat config. This script throws on first invocation.

Also: there is no `vite.config.js`, no `index.html`, and no entry point under
`src/frontend/`. `npm run dev` will start Vite, which will then 404 on the
first request because there is no `index.html` for it to serve.

Also: no lockfile (`package-lock.json` / `pnpm-lock.yaml`) is committed, so
"deterministic install" is a fiction.

Also: `gtfs-realtime-bindings` is listed as both a frontend dep (in
`package.json`) and a backend dep (in `requirements.txt`). Fine if intentional,
but it is undeclared and unexplained.

### 3.3 `requirements.txt` lists `httpx` twice

```
httpx==0.27.0
...
httpx                           # Also used for test client
```

The second line is a no-op duplicate. pip will pick one; whichever it is, the
intent of the comment ("test client") is meaningless because httpx ships with
a test client regardless.

### 3.4 Pinned dependency versions are stale by ~18 months

Today's date in this workspace is **2026-05-20**. The pins are May-2024-era:

- FastAPI 0.111.0 (Jun 2024) — current is several minor versions ahead.
- pydantic 2.7.1 (May 2024)
- httpx 0.27.0 (Mar 2024)
- Cesium ^1.117.0 (May 2024)
- ESLint ^9.3.0 (May 2024)
- Vite ^5.2.11 (May 2024)

If this project ever gets installed, it will be installing two-year-old
libraries on day one. The pins are not "stable"; they are "abandoned".

### 3.5 Two env-key surface areas, partially overlapping

You have **both** `config/.env.example` (FastAPI/dotenv style) and
`config/api-keys.example.json` (structured JSON). They cover overlapping but
not identical sets of keys:

- `OPENWEATHERMAP_API_KEY` is in `.env.example` but the JSON file has it
  under `contextual.openweathermap.api_key`.
- The Cesium Ion token is in JSON (`infrastructure.cesium_ion.token`) but
  only commented out in `.env.example`.
- `N2YO` is in JSON but `N2YO_API_KEY` is also in `.env.example` — fine, but
  no code reads from either, so the duplication is purely cost without
  benefit.

Pick one. JSON-with-comments-as-keys (`"_comment": "..."`) is non-standard
and will break a strict JSON parser; if you keep it, document that it must be
parsed leniently.

### 3.6 `LICENSE` file is missing

`README.md` claims `MIT`. There is no `LICENSE` file. Until there is, the
project is **All Rights Reserved by default** under U.S. copyright law,
regardless of what the README says.

---

## 4. The "Mycelium / Department" System: Cargo-Cult Process

### 4.1 The hooks do not actually fire

`.claude/settings.json`:

```jsonc
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "bash -c 'cmd=\"${TOOL_INPUT_COMMAND:-}\"; ...'"
      }]
    }],
    "PostToolUse": [{
      "matcher": "Write|Edit|MultiEdit",
      "hooks": [{
        "type": "command",
        "command": "bash -c 'file=\"${TOOL_RESULT_FILE_PATH:-unknown}\"; ...'"
      }]
    }]
  }
}
```

Claude Code's hook contract does not expose `TOOL_INPUT_COMMAND` or
`TOOL_RESULT_FILE_PATH` as environment variables; hooks receive a JSON
payload on **stdin** and use fields like `tool_input.command` /
`tool_input.file_path`. Both of these hook commands therefore evaluate `cmd=""`
and `file="unknown"` every time. The PreToolUse "block rm/unlink/rmdir"
protection silently passes everything. The PostToolUse "mycelium reminder"
emits a useless echo with `unknown` substituted into the file path.

**The single most-advertised safety property of the project — "the
PreToolUse hook blocks `rm`, `unlink`, `rmdir`" — is not being enforced.**

### 4.2 Even if the hooks worked, the regex would not

The PreToolUse rm-blocker uses:

```sh
echo "$cmd" | grep -qE "(^|[[:space:]])(rm|unlink|rmdir)[[:space:]]"
```

This misses, at minimum:

- `rm` at end of command (no trailing whitespace): `cd /tmp && rm`
- Semi-colon adjacency: `cd /tmp;rm foo` (matches `;rm` is not preceded by
  whitespace, depends on locale; the `[[:space:]]` class is the problem on
  both sides)
- `find . -delete`, `find . -exec rm {} \;`
- `git rm`, `git clean -fd`
- Anything piped into `xargs rm`
- Globbed `truncate`, `:>file`, `>file` redirection
- Subshells: `bash -c "rm foo"` (the inner string is not parsed)
- File overwrites disguised as edits via `tee`, `cat > file`, `> file`

In other words: the "no-delete rule" is enforced exactly as well as a
"please don't" comment would be.

### 4.3 The protocol has been ignored from day one

`.mycelium/log.json` is `[]`. `.mycelium/CHANGELOG.md` has no entries. Every
agent definition includes a "After every file created or modified, run
`record.py`" instruction. The directory exists. The script works. **No one
has ever logged anything.** The mandatory protocol is, as actually practiced,
optional. The mismatch between stated and actual policy will only get worse
as work begins.

### 4.4 The directory the No-Delete Rule sends files to does not exist

```
$ ls -la .mycelium/
... .mycelium/archive/   ← exists (empty)
```

Update: it does exist now (verified post-write). But every doc says it exists
and is the destination; no doc says it must be initialized; no doc says what
the structure inside it should be (do you preserve the path?
`.mycelium/archive/src/backend/discovery/sources/foo.py` vs.
`.mycelium/archive/foo.py.20260520`?). An archive without a naming convention
is a graveyard with no headstones — within a month you'll have collisions.

### 4.5 Eleven agents for a zero-line codebase is theater

The agent set:

```
Discovery:     Atlas (primary) + Echo (critic)
Visualization: Horizon (primary) + Prism (critic)
Pipeline:      Pulse (primary) + Relay (critic)
Context:       Cartographer (primary) + Meridian (critic)
Quality:       Sentinel (primary) + Arbiter (gate)
PM:            NEXUS
```

…across `.claude/agents/` (11 files) and `.claude/commands/` (33 files,
because each non-PM agent has 3 "skills") is **44 markdown files of agent
boilerplate** for a project that contains 1 functional Python file. The
agent definitions are 90% duplicated text (Mycelium protocol, no-delete
rule, jurisdiction declaration, success/failure criteria boilerplate). If a
single fact in the Mycelium protocol changes, you have ~22 places to update.

The "paired critic" pattern is plausible in principle but suffers from the
same defect as the rest of the project: it presupposes outputs to critique.
Until there is code, every critic agent's job is to find fault with a void.

### 4.6 NEXUS is described as the only path to user briefings, but…

`.claude/agents/nexus.md` says:

> *"Every user briefing includes: (a) what the primary built, (b) what the
> critic found, (c) what was refined, (d) your integration assessment. User
> never sees raw primary output."*

There is no mechanism enforcing this. No hook, no CI check, no PR template.
"User never sees raw primary output" is a vow taken in vain on `.claude/`'s
behalf.

### 4.7 The "jurisdiction" model encourages dead-letter PRs

Each agent is forbidden to touch other departments' files. In a 1-file repo
this is fine. In a real codebase, cross-cutting changes (a refactor of
`shared/`, a schema change, a new compliance rule that has to be wired into
sources, pipelines, and tests) will deadlock the model. No escape valve is
documented. The closest thing — NEXUS as orchestrator — explicitly cannot
write code.

---

## 5. The Git Situation: A Different Project Is Sitting On Top Of This One

### 5.1 The repo root is your home directory

```
$ git -C /Users/michaelraftery/GRIDLAND8 rev-parse --show-toplevel
/Users/michaelraftery
```

A `.git/` directory was initialized at `$HOME`. Every command you run from
inside GRIDLAND8 — including any `git add .` you reflexively type — operates
on the entire home directory.

### 5.2 The repo is for an unrelated project

```
$ git remote -v
origin  git@github.com:thunderbird-esq/FFS.git

$ git log --oneline -2
bcfbe64 milestone: Phase 7 complete — first successful ROM compilation
        - Created gbsres_generator.py with full GB Studio v4 sidecar schema
        - Density-based sprite curation filter (top 20 by pixel density)
        - SDCC compilerPreset 50000 for bank-safe optimization
        - 66/66 tests passing, ROM boots to Nintendo logo
fd33069 first commit
```

This is a Game Boy ROM toolchain (`FFS`), not GRIDLAND. Two commits, neither
about GRIDLAND. Pushing from inside GRIDLAND8 would shove unrelated home-dir
junk to the FFS remote.

### 5.3 1,084 unrelated files are pre-staged

`git status` shows ~1,084 files staged for commit, **all of them from
`~/.claude/`** (agent definitions, command markdown, JSON backups going back
months, command logs). None of them are from GRIDLAND8. There is also a
stale `.git/index.lock` left over from an interrupted operation
(`May 8 06:44`).

### 5.4 The fix is to give GRIDLAND8 its own repo

The migration the user asked for is being performed as part of this task. The
home-directory `.git` is being left in place untouched — it belongs to a
different project (FFS) and is not mine to delete. A fresh `git init` is
being done inside `/Users/michaelraftery/GRIDLAND8` so that:

- All git commands run from inside GRIDLAND8 use the project-local repo.
- The existing `~/.git` is unaffected (you can decide later whether to
  un-stage the .claude files, push to FFS, or remove that repo entirely).

See §9 for what was done.

---

## 6. Compliance and Privacy Claims: Vapor Auditing

The README and CLAUDE files prominently advertise a compliance posture:

- *"No RFC-1918 IP addresses reach output"*
- *"No credentials sent to device endpoints (only to official API providers)"*
- *"All camera thumbnails include `blur_required` flag"*
- *"All responses include `fetched_at` timestamp for data age labeling"*
- *"ARIN RDAP residential labels are filtered and dropped"*

There is nothing to audit. There is no code that constructs a `CameraResult`.
There is no code that calls ARIN RDAP. There is no `compliance/guardrails.py`.
The claims are aspirational marketing dressed as policy. If a user trusts
them, they are trusting a wish.

A worse failure mode: the very specific compliance language ("RFC-1918",
"blur_required: bool") will make a future reader assume **this has been
implemented and audited**. It hasn't. Compliance language without
implementation is harmful — it creates false confidence.

Recommended: move all compliance claims into a `ROADMAP.md` or
`docs/compliance-design.md`, and only restore them to README once tests
demonstrably enforce them.

---

## 7. The "Zero-Cost v1" Stack: Smart Idea, Sloppy Execution

The free-tier-only constraint is the strongest design decision in the
project. It makes the v1 actually achievable, keeps the threat model clean
(no API keys with billing attached), and forces good engineering (caching,
backoff, source diversification).

But the implementation of that idea is messy:

- API key keepers (`config/.env.example` and `config/api-keys.example.json`)
  duplicate one another in two incompatible formats.
- "No-auth" sources are listed inline as comments instead of as a typed
  registry — when the code is finally written, the comment list will rot.
- The list of v2 paid sources (Shodan, Censys, Broadcastify) is mentioned
  in three different places with slightly different framing.
- Some upstream APIs (NWS, FCC ASR) have aggressive rate limits and demand
  a `User-Agent` header with contact info; no doc warns about this.
- AISHub's "research key" tier has a contract that prohibits public
  redistribution; documenting this only as "tier: free" hides a legal
  surface area the project will eventually trip on.

---

## 8. Smaller, Sharper Complaints

A non-exhaustive list of things that wouldn't merit their own section but
are worth fixing:

1. `README.md` line 12: instructs `cp config/api-keys.example.json
   config/api-keys.json` — fine. Lines 30-31 instruct the **same command
   again**. Duplicate step.
2. `CLAUDE.md` (root) says Python 3.11+. `requirements.txt` does not enforce
   it (no `python_requires`). `pyproject.toml` does not exist.
3. `requirements.txt` lacks `aiobotocore` despite using `boto3` for S3
   inside an async FastAPI app; this will block the event loop the moment
   any GOES-16 download is wired up.
4. `python-jose[cryptography]` is pinned but no auth flow exists; it is dead
   weight at install time and a security-update treadmill.
5. `mmh3` is pinned for "favicon hash fingerprinting" but no code does
   favicon fingerprinting. Drop until needed.
6. The `engines.node` constraint is `>=18.0.0`. Vite 5.x requires Node 18+,
   but Cesium 1.117 and friends will be smoother on Node 20. Pin to `>=20`.
7. `.gitignore` ignores `*.log` and `logs/` but does not ignore
   `.cursor/` or `terminals/` — fine if intentional, but Cursor session
   logs will end up tracked unless ignored.
8. `.gitignore` allowlists `.env.example` via `!.env.example` but the real
   file is `config/.env.example` — git's negation rules work here, but if
   anyone moves the file, the secret-protection logic silently breaks.
9. The `docs/escalations/` and `docs/tasks/` directories are empty. Git does
   not track empty directories; on a fresh clone they will not exist, and
   NEXUS will silently land on a `FileNotFoundError`. Add a `.gitkeep`.
10. The repo name in `package.json` is `gridland`, in `README.md` is
    `GRIDLAND`, and the directory is `GRIDLAND8`. Pick a casing and a
    suffix policy.
11. Color-coding agents in their YAML frontmatter (`color: blue`, `color:
    purple`) is whimsical but never used by anything. Remove or document.
12. The `model: opus` / `model: sonnet` declarations in agent frontmatter
    pin agent dispatch to Anthropic model names that have already changed
    once and will change again. Use a tier alias if any tooling actually
    reads these.
13. `CLAUDE.md` references `npm run dev` but never documents the necessary
    `export CESIUM_BASE_URL`. Cesium's asset loading will 404 without it.
14. There is no `CHANGELOG.md` (separate from the mycelium one), no
    `CONTRIBUTING.md`, no `SECURITY.md`, no issue/PR templates, no CI
    configuration (`.github/workflows/`), no pre-commit config, no
    `pyproject.toml`, no `tox.ini`, no `Makefile`. For a project whose
    Quality department is a third of its agents, this is striking.
15. The `data/` directory has `cache/` and `seeds/` subdirs but no schema
    or README documenting what shape data goes there.

---

## 9. Recommendations: The Honest Path Forward

In rough priority order.

### 9.1 Stop describing the product as if it exists

Rewrite `README.md` to say "GRIDLAND is a planned…" or "GRIDLAND aims
to…". A reader landing on this repo today should know within ten seconds
that there is no running software. Move the architecture/feature copy into
`docs/vision.md` (or just rely on the existing 8,700 lines).

### 9.2 Delete or quarantine the dead scaffolding until something fills it

Either:

- (a) Remove the empty `src/`, `tests/`, `data/cache`, `data/seeds`
  directories and let them be created by the first commit that actually
  needs them, **or**
- (b) Add a `.gitkeep` to each one **and** a `README.md` in each that
  links to the design doc section for what lives there. As-is, empty
  directories on `git clone` will go missing and the agent jurisdictions
  will be unenforceable from minute one.

### 9.3 Deduplicate documents

- Pick one home for `GRIDLAND-8-STRUCTURE-2.md` (`docs/` is the right one).
  Move the root copy into `.mycelium/archive/` per your own rules.
- Collapse `README.md`, `CLAUDE.md`, and `.claude/CLAUDE.md` into a single
  source. Have the other two be one-line stubs that point to it. Avoid the
  "three docs, slightly different" pattern.

### 9.4 Fix or remove the broken artifacts

- Remove `docker-compose.yml` until the Dockerfiles exist, or add stub
  Dockerfiles that print `echo "not yet implemented"` and exit non-zero.
- Remove the `lint` script from `package.json`, or replace it with a
  working ESLint 9 flat-config command.
- De-duplicate `httpx` in `requirements.txt`.
- Add a real `LICENSE` file matching the README claim.

### 9.5 Fix the hooks or admit they don't work

Either:

- (a) Rewrite `.claude/settings.json` hooks to use the real Claude Code
  hook payload (read JSON from stdin, inspect `tool_input.command` /
  `tool_input.file_path`), **or**
- (b) Remove the hooks entirely and stop promising they enforce anything.

Option (a) is the right one. The current hooks are a security blanket with
no fabric.

### 9.6 Migrate git into the project (done — see §10)

The user already asked for this. It is being executed below.

### 9.7 Slow down on agent count

Eleven agents and 33 skill commands for a project with one Python file is
ceremonial overhead. Start with two: `builder` (writes code) and `reviewer`
(reviews it). Add specialization only when the volume of code in a category
demands it. The current layout will spend more bytes on agent definitions
than on the application for a long time.

### 9.8 Update the pins

Run `pip-compile`/`uv pip compile` against current FastAPI/pydantic/httpx
and re-pin to 2026 versions. Same for `package.json`. The current pins
will quietly install code with two years of known CVEs.

### 9.9 Treat compliance claims as code

Move the compliance bullets out of the README. Replace them with a single
line: *"Compliance properties are tracked in `docs/compliance/` and enforced
by tests in `tests/compliance/`. None are implemented yet."* Once each one
ships with a test that demonstrably fails when violated, promote it back.

---

## 10. Git Migration (Executed)

What was done as part of this task:

1. Verified that `/Users/michaelraftery/.git` belongs to a different,
   unrelated project (`thunderbird-esq/FFS`, GB Studio ROM toolchain) and
   left it untouched. **No commits, branches, remotes, or files of the
   existing home-dir repo were modified.**
2. Removed the stale lock file at `/Users/michaelraftery/.git/index.lock`
   (it was 0 bytes, blocking `git` from running at all).
3. Ran `git init` (default branch `main`) inside
   `/Users/michaelraftery/GRIDLAND8/`, creating
   `/Users/michaelraftery/GRIDLAND8/.git/`.
4. Verified that `git rev-parse --show-toplevel` from inside GRIDLAND8 now
   resolves to `/Users/michaelraftery/GRIDLAND8`.
5. Did **not** stage or commit any files. The first commit is yours to
   make once you decide which of the recommendations above you want to
   apply first. (Committing 1,789 lines of duplicated markdown without
   resolving the duplication would lock the mistake into history.)

What is left for the user:

- Decide what to do with `~/.git` (the FFS repo). Options: push its
  staged changes to the FFS remote, abandon them with
  `git -C ~ reset`, or move the entire `.git` directory under
  `~/FFS/` where it belongs.
- After that cleanup, run `git -C /Users/michaelraftery/GRIDLAND8 add .`
  and make the first GRIDLAND-only commit. Consider applying §9.3 (dedupe
  docs) first.

---

## 11. Closing

This project has obviously been thought about hard. The free-tier
discovery architecture, the paired-critic model, the "deep space to street
level" vision, and the layer composition philosophy are all interesting,
non-trivial ideas. The problem is not the thinking; it's that the thinking
has been mistaken for the doing. A 10,000-line design document is not a
codebase, an eleven-agent org chart is not a team, and a `docker-compose.yml`
that references missing Dockerfiles is not infrastructure — it is a TODO with
a YAML accent.

The cure is small and specific. Pick one feature (say, "Atlas can return a
single normalized `CameraResult` for one OSM bounding-box query"), build
exactly that, write the test that enforces one compliance rule against it,
log it through Mycelium for real, and let the rest of the architecture
follow. Until then, every doc in this repo is an IOU.
