# Contributing

Wingman is a personal experimental project. PRs and issues are welcome, but expect a relaxed review pace and occasional hard-no's on scope. If you're planning anything non-trivial, open an issue first so we don't both spend an evening on something that won't land.

## Dev setup

```bash
git clone https://github.com/siddharthprakash1/wingman.git
cd wingman
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]          # add ",all" for discord/slack/voice/browser extras
cp config.example.json ~/.wingman/config.json
cp .env.example .env           # add your API keys here
python -m src.main doctor      # sanity check
```

See [CLAUDE.md](CLAUDE.md) for a tour of the architecture — it's the fastest way to understand the three orthogonal axes (channel → gateway → agent / swarm / cross-cutting infra) before touching anything.

## Running locally

```bash
make agent         # interactive CLI chat
make gateway       # FastAPI + WebChat UI on 127.0.0.1:18789
make doctor        # health check
python run_swarm.py         # 10-bot Discord swarm (needs tokens)
python run_overnight.py     # Night Lab pipeline → ~/.wingman/briefs/<date>.md
```

## Testing

```bash
pytest                                   # full suite (asyncio_mode=auto, no decorator needed)
pytest tests/test_core.py                # one file
pytest tests/test_core.py::test_session_creation   # one test
pytest --cov=src --cov-report=html       # coverage
```

`tests/integration/` hits real embeddings and (optionally) a real OpenAI key — those are opt-in, not part of the default CI path.

If you're fixing a bug, add a test that fails on `main` and passes on your branch. If you're adding a feature, add something that exercises the happy path at minimum.

## Style

```bash
black src/ tests/                  # format (line length 100)
ruff check src/ tests/ --fix       # lint
mypy src/                          # type check
```

- Python 3.11+, type hints on public function signatures
- Async/await for I/O — don't sprinkle `asyncio.run` inside library code
- Don't write docstring novels. A one-line summary is almost always enough; save prose for the WHY when it's non-obvious
- Don't hardcode `~/.wingman` paths — import from `src/config/paths.py`
- Don't weaken sandboxing in `src/security/` or in per-tool `_resolve_*` helpers without a clear reason

## Commits

[Conventional Commits](https://www.conventionalcommits.org/) — not enforced by a hook, but reviewers expect it:

```
feat(swarm): add FIRE-framework validator to Night Lab
fix(providers): skip circuit-broken provider in round-robin
docs(readme): redo quickstart
chore(repo): move reference docs under docs/
```

Scope is whatever subpackage under `src/` you touched (`providers`, `gateway`, `swarm`, `tools`, etc.) or `repo` / `ci` for cross-cutting work. Keep subject lines ≤72 chars. Body optional — use it when the WHY won't survive code review otherwise.

## Pull requests

- Branch from `main`, rebase rather than merge if `main` moves
- One concern per PR — a bugfix + refactor + docs rewrite in one branch is a nightmare to review
- Run `pytest`, `black`, `ruff`, `mypy` before opening the PR
- Describe what changed and why. Screenshots for UI changes. A one-liner repro for bug fixes
- Draft PRs are fine for early feedback

## Security

Don't commit anything from `.env` or `~/.wingman/config.json` — both are gitignored for a reason. If you find a real security issue (sandbox bypass, secret exfiltration path, etc.), email me directly rather than opening a public issue: `siddharth.prakash@couchbase.com`.

## What not to send

- Large refactors that rename hundreds of files with no attached bug/feature
- Dependency bumps without a reason (`bump foo to x.y.z because the API we use is broken on x.y.z-1` is fine; `bump for latest` is not)
- Drive-by formatting PRs on files you otherwise didn't touch
- New features added to the swarm personalities without actually running an overnight cycle to see if they behave
