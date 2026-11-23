# Claude instructions for this fork (VoliKoN/homeassistant_espscreen)

This repository is **Nevo's fork** (GitHub `VoliKoN`) of [MaxGramser/homeassistant_espscreen](https://github.com/MaxGramser/homeassistant_espscreen)
(Tessera / ESP Screens). The fork exists for one purpose: **Hebrew on the screens and in the editor**, run on Nevo's own
Guition screen from a Docker install on a Raspberry Pi. You are working for Nevo, not for the upstream maintainer.

Read these before doing anything:

1. **FORK.md**: the full handover. What was built, the branches, how the image is published, CI quirks, open items.
2. **AGENTS.md**: upstream's guide to the codebase (layers, rules, where things live). Its codebase rules apply here.
   Its sections about the maintainer's own workflow do **not** apply (see below).

@AGENTS.md

## What in AGENTS.md does not apply to this fork

- **"Branches and releases"**: this fork has no `dev` branch and makes no releases. Never run `tools/release.py`,
  never bump the app version or the firmware number yourself, never tag. The fork's branch model is below.
- **"Checks", the bench part**: there is no bench, no Mac mini, no deploy-home skill, no `.esphome/owner-access.md`.
  The proof on this fork is GitHub Actions plus Nevo looking at his own screen.
- **"Replying to issues and pull requests"**: never comment on upstream issues or pull requests, and never add
  the maintainer's signature anywhere.
- **"Owner's machine"**: Nevo's Pi and screen are not reachable from a Claude session unless he links his computer.

## Branches (the most important part)

| Branch | What it is | Rules |
|---|---|---|
| `main` | Mirror of upstream `main`, plus this file, FORK.md and `.claude/skills/` | Update only by merging `upstream/main`. Nightly CI runs here. |
| `hebrew` | The Hebrew work on top of upstream `dev`. **This is the branch a future upstream pull request would come from.** | Must stay upstream-clean: no fork-only changes, no CLAUDE.md, FORK.md or `.claude/`. |
| `hebrew-screen` | `hebrew` + fork-only changes (packages point at this fork, the fork's Docker image workflow). **This is what Nevo runs.** | Gets `hebrew` merged in, never the other way round. |
| `ci-hebrew-long`, `ci-baseline-dev` | Old temporary CI experiments | Safe to delete. |

Remotes: `origin` = the fork, `upstream` = `https://github.com/MaxGramser/homeassistant_espscreen.git` (add it if missing).

## Hard rules

- **Never open a pull request to upstream, and never push to upstream**, unless Nevo explicitly asks in so many words.
- Do not put Nevo's email address, IPs, tokens or other personal details into files in this repo. It is public.
- Fork-only changes go on `hebrew-screen` (or `main` for these handover files), never on `hebrew`.
- When you change CLAUDE.md, FORK.md or `.claude/skills/`, make the same change on both `main` and `hebrew-screen`
  (commit on one, `git cherry-pick` onto the other) so they don't drift.
- Commit messages follow upstream's style: `Area: what changed, in plain words`. Fork-only commits start with
  `Fork only:`.
- Generated files are never edited by hand: `packages/<key>.yaml` and `checkout/` come from `tools/generate_entries.py`,
  `screen_manager/app/static/` from `cd web && npm run build`, the WASM preview from CI's `preview.yml`.

## Skills in this repo

- `.claude/skills/sync-upstream/`: bring the fork up to date with upstream (main, hebrew, hebrew-screen), step by step.
- `.claude/skills/hebrew-translations/`: fill and check the Hebrew texts after upstream adds new ones.

## Quick checks

```sh
python3 -m pytest tests/test_script_glyphs.py -q      # the Hebrew letters, fonts and BiDi wiring
python3 tools/i18n.py check                            # every language, Hebrew included: must say "0 problems"
python3 tools/i18n.py lint && python3 tools/i18n.py header --check
python3 tools/generate_entries.py --check              # entries current (on hebrew-screen they point at this fork)
cd web && npm ci && npm test && npm run build          # the editor; commit screen_manager/app/static with it
gh workflow run ci.yml --ref hebrew-screen             # full CI on a branch (push alone only runs it on main)
```
