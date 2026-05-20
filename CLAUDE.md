# GRIDLAND — Working Notes

See `README.md` for setup and architecture. This file documents the conventions any agent must follow when editing the repository.

## Mycelium v3 — automatic via git trailers

Every commit must include Mycelium-* trailers in its message. The `commit-msg` git hook rejects commits without `Mycelium-Agent` and `Mycelium-Phase`. The `post-commit` hook reads the trailers and automatically appends one `.mycelium/log.json` entry per file touched in the commit. `CHANGELOG.md` is regenerated from the log.

Required trailers:

```
Mycelium-Agent: <name>
Mycelium-Dept:  discovery|visualization|pipeline|context|quality|none
Mycelium-Phase: primary|critique|refined|pm_review|qa_gate
Mycelium-Rationale: one or two lines explaining the why
```

Optional:

```
Mycelium-Action:      created|modified|archived|reviewed|verified   (default inferred from diff)
Mycelium-Critique-Of: myc_<id>                                       (for critic commits)
```

Install the hooks once per checkout: `make install-hooks` (also runs as part of `make setup`).

Bypass the hooks once (e.g., during an interactive rebase) with `GRIDLAND_SKIP_MYCELIUM=1 git ...`.

Manual single-file entries still work for ad-hoc cases:

```bash
python3 .mycelium/record.py --agent <name> --phase primary --file <path> \
  --action modified --rationale "..." --department <dept>
```

The `pre-push` hook blocks pushes to `main` that contain commits without `Mycelium-Agent` trailers.

## Conventions

- Python 3.11+. Use `from __future__ import annotations`. Type-annotate public functions.
- Source identifiers and normalized response field names live in `backend/shared/constants.py`. Use the constants, not literal strings.
- Every external HTTP call goes through `backend.shared.http.get_json` / `post_json` — they enforce timeout, retries, and the project User-Agent.
- Every new source module exports a `normalize(raw) -> list[Model]` pure function plus an `async` fetcher; tests mock the fetcher's HTTP and call `normalize` directly with fixture data.
- The compliance gate (`backend.compliance.guardrails.filter_compliant`) runs as the last step of any aggregator that produces `CameraResult`.
- Tests never reach the network. Use `monkeypatch` to replace `get_json` / `post_json` or the source's `fetch_*` function.

## Adding a discovery source

1. Create `src/backend/discovery/sources/<name>.py` with `async def fetch(...)` and `def normalize(raw) -> list[CameraResult]`.
2. Append to `coros` in `backend.discovery.service.search_area`.
3. Add the source identifier constant in `backend/shared/constants.py` and `SourceName` literal in `backend.discovery.models`.
4. Add `tests/test_discovery_<name>.py` with mocked upstream.
5. Record a Mycelium entry.

## Adding a context source

1. Create `src/backend/context/sources/<name>.py` with one or more `async` accessors returning plain dicts or list[dict].
2. Add it to the `asyncio.gather` call in `backend.context.service.gather` and unpack into the returned `ContextBundle`.
3. Add `tests/test_context.py` cases for normal, empty, and failing upstream.
4. Record a Mycelium entry.

## Adding a real-time entity

1. Add the entity model to `backend/pipeline/models.py`.
2. Create `src/backend/pipeline/sources/<name>.py` with `fetch` and `normalize`.
3. Add a snapshot function to `backend.pipeline.service`.
4. Extend `backend.api.realtime` to broadcast frames of the new `type`.
5. Add a frontend entity layer in `src/frontend/entities/<name>.js` matching the `AircraftLayer` pattern.
