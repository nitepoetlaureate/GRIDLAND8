"""Tests for the Mycelium v3 trailer-based recorder."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _run(*args, cwd=None, check=True, env=None):
    return subprocess.run(args, cwd=cwd, check=check, env=env, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path: Path):
    proj = Path(__file__).resolve().parents[1]
    sub = tmp_path / "repo"
    sub.mkdir()

    # mirror just the .mycelium/ scripts the recorder needs
    myc_src = proj / ".mycelium"
    myc_dst = sub / ".mycelium"
    myc_dst.mkdir()
    (myc_dst / "record.py").write_text((myc_src / "record.py").read_text())

    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "test"
    env["GIT_AUTHOR_EMAIL"] = "t@example.com"
    env["GIT_COMMITTER_NAME"] = "test"
    env["GIT_COMMITTER_EMAIL"] = "t@example.com"

    _run("git", "init", "-q", str(sub), env=env)
    _run("git", "-C", str(sub), "config", "commit.gpgSign", "false", env=env)
    yield sub, env


def _commit_with_trailers(repo_dir: Path, env, msg, file_contents: dict[str, str]):
    for path, body in file_contents.items():
        p = repo_dir / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
    _run("git", "-C", str(repo_dir), "add", "-A", env=env)
    _run("git", "-C", str(repo_dir), "commit", "-q", "-m", msg, env=env)
    sha = _run("git", "-C", str(repo_dir), "rev-parse", "HEAD", env=env).stdout.strip()
    return sha


def test_from_commit_records_one_entry_per_file(repo):
    repo_dir, env = repo
    msg = (
        "feat(test): add a thing\n\n"
        "Body line.\n\n"
        "Mycelium-Agent: builder\n"
        "Mycelium-Dept: discovery\n"
        "Mycelium-Phase: primary\n"
        "Mycelium-Rationale: adds two source files\n"
    )
    sha = _commit_with_trailers(repo_dir, env, msg, {
        "src/a.py": "a = 1\n",
        "src/b.py": "b = 2\n",
    })
    _run(sys.executable, ".mycelium/record.py", "from-commit", sha,
         cwd=str(repo_dir), env=env)
    log = json.loads((repo_dir / ".mycelium" / "log.json").read_text())
    files = {e["file"] for e in log}
    assert files == {"src/a.py", "src/b.py", ".mycelium/record.py"} or \
           {"src/a.py", "src/b.py"}.issubset(files)
    for e in log:
        if e["file"].startswith("src/"):
            assert e["agent"] == "builder"
            assert e["department"] == "discovery"
            assert e["phase"] == "primary"
            assert e["action"] == "created"
            assert e["commit"] == sha
            assert e["auto"] is True


def test_from_commit_without_trailers_is_noop(repo, capsys):
    repo_dir, env = repo
    sha = _commit_with_trailers(repo_dir, env, "no trailers here", {"x.txt": "x"})
    _run(sys.executable, ".mycelium/record.py", "from-commit", sha,
         cwd=str(repo_dir), env=env)
    log_path = repo_dir / ".mycelium" / "log.json"
    if log_path.exists():
        log = json.loads(log_path.read_text())
        # may have entries from earlier in the same fixture, but not for x.txt
        assert all(e["file"] != "x.txt" for e in log)
