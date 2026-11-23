---
name: sync-upstream
description: Bring the VoliKoN fork up to date with MaxGramser/homeassistant_espscreen - main from upstream main, hebrew from upstream dev, then hebrew-screen from hebrew - and get CI green. Use when Nevo asks to update the fork or pull upstream changes.
---

# Sync the fork with upstream

The order matters: `main`, then `hebrew`, then `hebrew-screen`. FORK.md explains each branch; read it first if you
haven't.

## 0. Set up

```sh
git remote get-url upstream 2>/dev/null || git remote add upstream https://github.com/MaxGramser/homeassistant_espscreen.git
git fetch origin && git fetch upstream
git rev-list --count origin/hebrew..upstream/dev     # how far behind
```

Use a git worktree per branch if you want them side by side. Never push to `upstream`.

## 1. main

```sh
git checkout main && git pull --ff-only origin main
git merge upstream/main            # not ff-only: main carries CLAUDE.md, FORK.md, .claude/skills and a .gitignore line
git push origin main               # starts CI on main (it runs on push to main)
```

A conflict can only be in `.gitignore`. Keep upstream's lines, and keep `/.claude/*` with `!/.claude/skills/`.

## 2. hebrew (upstream-clean)

```sh
git checkout hebrew && git pull --ff-only origin hebrew
git merge upstream/dev
```

Typical conflicts and how to resolve them:

- **`screen_manager/app/static/**`**: take either side, then rebuild with `cd web && npm ci && npm run build`. Add the
  whole `screen_manager/app/static` folder, deletions included (`git add -A screen_manager/app/static`).
- **`web/src/wasm/firmware_preview.wasm`, `web/wasm/generated/**`, `screen_manager/app/static/assets/firmware_preview-*.wasm`**:
  take upstream's (`git checkout --theirs`). CI's `preview.yml` rebuilds them with Hebrew after the push.
- **`web/src/**/*.vue`, `web/src/styles/app.css`**: upstream edits physical CSS properties that the fork changed to
  logical ones. Keep upstream's change in logical form: `left` becomes `inset-inline-start`, `margin-left` becomes
  `margin-inline-start`, and `text-align: left` becomes `start`. New screen mockups need `dir="ltr"` plus class
  `glass-ltr` (FORK.md section 2).
- **`packages/core.yaml`**: keep both. Upstream's new substitutions or fonts, plus the Hebrew ones. A **new text font**
  added upstream needs its own `NotoSansHebrew-<weight>.ttf` extra. `tests/test_script_glyphs.py` will say so.
- **`screen_manager/CHANGELOG.md`**: keep upstream's sections and the fork's Hebrew lines under `## Unreleased`.
  Once upstream released, the Hebrew lines stay under a fresh `## Unreleased`.
- **`.github/workflows/ci.yml`**: keep upstream's version and re-apply the cache key fix: the firmware job's
  setup-python step gets `id: python`, and both firmware cache keys include `${{ env.ImageOS }}` and
  `py${{ steps.python.outputs.python-version }}`. If upstream already did something equivalent, drop ours.
  **Check for duplicate YAML keys** before pushing. GitHub rejects them and PyYAML doesn't:

  ```python
  import yaml, sys
  class L(yaml.SafeLoader): pass
  def m(loader, node, deep=False):
      keys = [loader.construct_object(k, deep=deep) for k, _ in node.value]
      dup = {k for k in keys if keys.count(k) > 1}
      if dup: raise SystemExit(f'duplicate keys {dup} at line {node.start_mark.line + 1}')
      return yaml.SafeLoader.construct_mapping(loader, node, deep)
  L.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, m)
  for f in sys.argv[1:]: yaml.load(open(f), L)
  ```

Then:

1. Fill the new Hebrew texts with the `hebrew-translations` skill. `python3 tools/i18n.py check` must report
   0 problems, because CI refuses missing keys in a full language.
2. Run the checks:

   ```sh
   python3 -m pytest tests/test_script_glyphs.py -q
   python3 tools/i18n.py check && python3 tools/i18n.py lint && python3 tools/i18n.py header --check
   cd web && npm test && npm run build && cd ..
   ```

   `tools/check.sh` runs everything, but it is slow and needs the toolchains. In a cloud session,
   `tests/test_pictures.py` fails 6 tests even on clean upstream. Ignore those.
3. Commit the merge, then push it:

   ```sh
   git push origin hebrew
   ```

4. Wait for `preview.yml` ("Firmware preview: rebuilt for ...") to commit back. Then pull:

   ```sh
   git pull --ff-only origin hebrew
   ```

`hebrew` must never contain CLAUDE.md, FORK.md, `.claude/` or any `VoliKoN` URL.

## 3. hebrew-screen

```sh
git checkout hebrew-screen && git pull --ff-only origin hebrew-screen
git merge origin/hebrew
python3 tools/generate_entries.py              # re-point packages/ and checkout/ at the fork (the merge brings upstream's URLs back)
python3 tools/generate_entries.py --check
grep -L VoliKoN packages/*.yaml                # should list only packages/core.yaml
python3 -m pytest tests/test_easy_package.py tests/test_release_lint.py tests/test_script_glyphs.py -q
git commit -am "Fork only: entries point at this fork again after merging hebrew"   # if anything changed
git push origin hebrew-screen
```

Conflicts here are usually only in generated files and the fork-only files (FORK.md section 3). Keep the fork's
versions of `tools/generate_entries.py` (the `REPO` constant), `.github/workflows/fork-image.yml` and the
`preview.yml` dispatch step. For `screen_manager/config.yaml`, take upstream's version number and name.

What happens after the push:
- If `preview.yml` rebuilds the preview, it starts `fork-image.yml` itself.
- Otherwise `fork-image.yml` runs from the push (paths `screen_manager/**`).

Check the image run:

```sh
gh run list --branch hebrew-screen --limit 5
```

## 4. Full CI and the report

```sh
gh workflow run ci.yml --ref hebrew-screen
gh run list --workflow ci.yml --branch hebrew-screen --limit 1
```

`firmware (add-on)` can take close to 4 hours on a cold cache. Watch it, don't sit on it. For a failure, read the log:

```sh
gh api repos/VoliKoN/homeassistant_espscreen/actions/jobs/<job id>/logs
```

Then tell whether the cause is ours or upstream's. If upstream's, prove it by running CI on a temporary branch made
from `upstream/dev`, and delete that branch afterwards or ask Nevo to.

Tell Nevo:
- what came in, in a few lines from upstream's CHANGELOG
- whether CI passed
- the new image tag

On the Pi he runs `docker compose pull && docker compose up -d`, then updates the screen from the app.

Finally, update FORK.md section 1 (state and date) on both `main` and `hebrew-screen`.
