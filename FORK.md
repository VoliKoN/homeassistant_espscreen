# The VoliKoN fork: handover

Everything a new Claude session (or a person) needs to continue this fork without the conversations it came from.
Last written 2026-11-23. CLAUDE.md has the short rules; this file has the detail.

## 1. Purpose and status

The fork adds **Hebrew** to Tessera (ESP Screens): the screens draw Hebrew right to left, the app and editor are
translated, and the editor's UI turns right to left in Hebrew. Nevo runs the `hebrew-screen` branch on a Guition
screen. He confirmed on 2026-10-27 that the screen, the editor and the firmware preview all work.

State on 2026-11-23:

- `hebrew` is upstream `dev` as of about 2026-11-09 (app 0.4.97) with the Hebrew work merged in.
- `hebrew-screen` is `hebrew` plus the fork-only changes, and its image is published (section 4).
- `main` mirrors upstream `main` 0.4.97, plus the handover files.
- **The fork is behind upstream**: on 2026-11-23 upstream `dev` was about 390 commits ahead of `hebrew`, and upstream
  `main` about 395 ahead of the fork's `main` (upstream released 0.4.101 meanwhile). Use the `sync-upstream` skill.
- The last full CI run on `hebrew-screen` passed (2026-11-09, run 42684543060). That covered the checks, every board
  on the add-on's ESPHome, and every board on the packages' `min_version`. The newest-ESPHome job failed on 5
  ESP32-P4 boards because of upstream's `esp_audio_stack` and ESPHome 2026.10.2. That job is warn-only and not
  ours (section 5).

No pull request has been opened upstream. Nevo decides if and when.

## 2. What the Hebrew work changed (branch `hebrew`)

Design decision, chosen by Nevo: **per-language**. Only a screen built with `LANGUAGE` `he` carries the Hebrew
letters and LVGL's BiDi, so no other screen pays any flash.

### Firmware

- `packages/core.yaml`:
  - `SCRIPT_GLYPHS_HEBREW` holds the 27 letters plus maqaf, geresh, gershayim and ₪.
  - `SCRIPT_GLYPHS_NOTO` is `SCRIPT_GLYPHS_HEBREW` when `LANGUAGE.split("-")[0]` is `he`, otherwise empty.
  - `LVGL_BIDI` is 1 or 0 by the same test.
  - The build flags are `-DLV_USE_BIDI=${LVGL_BIDI}` and `-DLV_BIDI_BASE_DIR_DEF=LV_BASE_DIR_AUTO`. Each label
    takes its direction from its first strong letter, so Hebrew reads right to left and English left to right.
  - The five text fonts (headline, watch_value, label, sublabel, sublabel_big) each get one more `extras` entry:
    `${FONT_DIR}/NotoSansHebrew-<weight>.ttf` with `glyphs: ["${SCRIPT_GLYPHS_NOTO}"]`, at Roboto's weight for
    that font (400, 500 or 700).
- `fonts/NotoSansHebrew-400/500/700.ttf` are subsets of about 5 KB each, cut to exactly those letters, with
  `fonts/NotoSansHebrew-OFL.txt` as the licence.
  - To rebuild them, take Noto Sans Hebrew (OFL, Google Fonts) at weights 400, 500 and 700, for example with
    `fontTools.varLib.instancer` on the variable font.
  - Then run `pyftsubset` on each with `--text` set to the letters above.
  - `tests/test_script_glyphs.py` checks that every letter is present.
- **Layout stays left to right.** Only text direction is RTL. A mirrored layout on the physical screen was scoped
  but never built (section 7).

### App (screen_manager)

- `screen_manager/app/header_bar.py` adds a `'hebrew'` entry to `SCRIPT_GLYPHS`. `clean_text` drops characters the
  screen's fonts lack, and drops niqqud.
- `screen_manager/translations/he.json`:
  - It covers every text, about 3,550 on 2026-11-09.
  - Its `_meta` is `name` עברית, `english` Hebrew, `script` hebrew, `plural` one_other, `clock` 24, and `checked`
    false.
  - It is a machine-made draft. `checked` stays false until a Hebrew speaker reviews it all.
  - The scripts that first assembled it are gone, so **the JSON file itself is the source**.
- `screen_manager/CHANGELOG.md` has Hebrew lines under `## Unreleased`.
- `docs/TRANSLATING.md` has a Hebrew row and a paragraph on how the letters get in.

### Editor (web/)

- `web/src/i18n.ts`:
  - `RTL_SCRIPTS`, `isRtl` and `editorDir` are new.
  - `setEditorLanguage` sets `document.documentElement.dir`.
- `web/src/App.vue` is wrapped in Reka UI's `<ConfigProvider :dir="dir">`, so menus, selects and popovers follow
  the direction.
- CSS across `web/src` moved to logical properties: `inset-inline-*`, `margin-inline-*`, `padding-inline-*`,
  `text-align: start/end`. A new style must use logical properties too, or it breaks in RTL.
- `web/src/components/ui/Icon.vue` gives directional icons (arrows, chevrons, undo, redo, dock-left) the class
  `ui-icon-dir`. `app.css` mirrors that class in RTL with `.ui-icon-dir:dir(rtl)`.
- `Sidebar.vue` and `Drawer.vue` measure resizing from the opposite edge in RTL and swap the arrow keys.
- **Screen mockups stay LTR.** They are marked `dir="ltr"` with class `glass-ltr`, and `.glass-ltr :where(*)`
  sets `unicode-bidi: plaintext` so each label orders itself, as on the real screen. That covers:
  - DevicePage, FirmwarePreview, PageMap and HomeView
  - AlertsView, the events AlertWizard, DoorbellView, SaverGlass and TileAnchor
  - A new mockup needs the same marking.
- The editor build output `screen_manager/app/static/` is committed with every `web/src` change.

### Firmware preview (WASM)

- `web/wasm/lv_conf.h` defines `LV_USE_BIDI 1` and `LV_BIDI_BASE_DIR_DEF LV_BASE_DIR_AUTO`.
- `web/wasm/generate_host_ui.py` sets `SCRIPT_GLYPHS_NOTO` to the Hebrew letters, so the preview always has them.
- CI's `preview.yml` rebuilds the WASM and commits it back as "Firmware preview: rebuilt for <sha>". It runs on a
  push to any branch that touches packages, components, fonts, web/wasm or `en.json`.
  - **Always pull before the next push.**
  - A Claude cloud session cannot build it locally, because the Emscripten download host is blocked there.

### Tests

`tests/test_script_glyphs.py` has a `HebrewLetters` class. It checks:
- the same letters in firmware and app
- a Noto extra at every font's weight
- letters and BiDi only for `he`
- translation files that say `script: hebrew`
- that Noto has every letter
- `clean_text`

### CI

`.github/workflows/ci.yml` has a cache key fix: the firmware caches include `${{ env.ImageOS }}` and the exact
Python version (`steps.python.outputs.python-version`). The cached CMake build stores the absolute path of ninja
under the hosted Python. When GitHub moved runners to a new image, the old cache pointed at a path that no longer
existed, which broke the fork's nightly builds. Upstream may want this fix too.

## 3. Fork-only changes (branch `hebrew-screen`)

- `tools/generate_entries.py` has `REPO = 'https://github.com/VoliKoN/homeassistant_espscreen'` and builds `RAW`
  and `FONT_DIR` from it. `packages/*.yaml` and `checkout/*.yaml` are regenerated from it.
  - After every merge of `hebrew`, run `python3 tools/generate_entries.py`. The merge brings upstream's URLs back.
- `tests/test_easy_package.py` reads `generate_entries.REPO` and `RAW` instead of hard-coding upstream.
  `tests/test_release_lint.py` accepts any owner in `FONT_URL`.
- `screen_manager/config.yaml` keeps upstream's name ("Tessera Screen Manager (dev)") and version. A rename broke
  tests, so it was reverted.
- `.github/workflows/fork-image.yml` publishes the image (section 4).
- `.github/workflows/preview.yml` gets `actions: write`. When it rebuilt a stale preview on `hebrew-screen`, it
  starts `fork-image.yml` with `gh workflow run`, because a push made with `GITHUB_TOKEN` starts no workflow.
- **Known gap:** `screen_manager/app/core.py` `REPO` still names upstream.
  - A screen set up anew from the app writes `url: <upstream>` into the screen's YAML, with `ref:` main (or
    `SCREEN_CHANNEL`).
  - Upstream main has no Hebrew, so such a screen builds without the Hebrew letters until its YAML points at this
    fork and `hebrew-screen`.
  - Nevo's existing screen works, so check its YAML on the Pi before changing anything.
  - The fix would be fork-only: `REPO` in `core.py`, plus `hebrew-screen` as an accepted channel.

## 4. How Nevo runs it

Docker Compose on a Raspberry Pi, next to a Home Assistant container. Not as a Home Assistant add-on. The service,
roughly:

```yaml
  esp-screens:
    image: ghcr.io/volikon/homeassistant_espscreen:hebrew   # was ghcr.io/maxgramser/homeassistant_espscreen:latest
    pull_policy: always
    network_mode: service:homeassistant
    volumes:
      - ./esphome:/config     # the screens' own YAML lives here
      - ./data:/data
    environment:
      SCREEN_DEV: "1"
```

The screen's language is chosen in the app's screen settings. With `he.json` in the image, Hebrew is in the list.

### The published image

`fork-image.yml` runs on a push to `hebrew-screen` that touches `screen_manager/**`, or by hand. It builds amd64 and
arm64 to `ghcr.io/volikon/homeassistant_espscreen` with four tags:

| Tag | Meaning |
|---|---|
| `hebrew` | newest build |
| `<app version>-hebrew` | newest build on that app version |
| `<app version>-hebrew.<run number>` | one build, to pin or roll back to |
| `sha-<commit>` | one commit |

It first checks the WASM preview is current. If it is stale, it publishes nothing and `preview.yml` restarts it
after the rebuild.

The package is **public** (made public by Nevo on 2026-11-23), so the Pi pulls it without logging in.

Update on the Pi: `docker compose pull && docker compose up -d`.

## 5. CI on the fork

- `ci.yml` runs on a push to `main`, nightly on `main` (02:00 UTC), and by hand. To test another branch, run
  `gh workflow run ci.yml --ref hebrew-screen`, then `gh run list --branch hebrew-screen`.
- It has four jobs: `checks`, `firmware (add-on)`, `firmware (min_version)` and `firmware (latest)`.
  - `checks` takes about half an hour.
  - **`firmware (add-on)` takes about 3.5 to 4 hours on a cold cache**, with a 240-minute limit. That is every board,
    on the ESPHome of `screen_manager/Dockerfile`, the one that matters for the Pi.
  - `firmware (latest)` is warn-only. On 2026-11-09 it failed on the 5 P4 boards (tab5, wavesharep4, wavesharep47b,
    wavesharep47, waveshare101): `components/esp_audio_stack/audio_core_ring_buffer_caps.h` uses `this->handle_`,
    and ESPHome 2026.10.2 made that a method. That is upstream's code, so leave it to upstream and check whether a
    later sync fixed it.
- Forks start with scheduled workflows disabled. They were enabled on this fork.
- GitHub rejects a workflow with a duplicate YAML key, which PyYAML accepts silently. Before pushing a workflow edit,
  load it with a duplicate-key-checking loader (a 10-line `yaml.SafeLoader` subclass whose `construct_mapping`
  raises on repeats).
- When the fork's CI failed in the past, the cause was usually upstream `dev` itself. To prove that, push upstream
  `dev` unchanged to a temporary branch and run CI there (`ci-baseline-dev` was that).

## 6. Working from a Claude cloud session

What works:
- `git` over HTTPS to the fork, once the Claude GitHub App is installed on the fork with write access.
- `gh api repos/VoliKoN/homeassistant_espscreen/...` (REST, repository-scoped).
- `gh workflow run`, `gh run view`, and job logs via `gh api repos/.../actions/jobs/<id>/logs`.

What is blocked:
- GitHub GraphQL. So `gh pr`, `gh repo view` and some `gh run` fields fail. Use `gh api` REST.
- `ghcr.io`. So the published image can't be pulled or inspected from a session.
- User-level API paths, such as package visibility, and branch deletion through the API.
- The Emscripten download host. Let CI's `preview.yml` rebuild the preview.

Local Python tests: `tests/test_pictures.py` fails 6 tests in the cloud container on clean upstream too. That is an
environment quirk, and it passes in CI. Run the editor with `cd web && npm ci && npm test && npm run build`.

## 7. Open items and ideas

Still with Nevo:
- **Old branches**: delete `ci-hebrew-long` and `ci-baseline-dev`.

To do:
- **Sync with upstream**: about 390 commits behind on 2026-11-23. Use `.claude/skills/sync-upstream`.
- **Fix the `core.py` `REPO` gap** described in section 3, if new screens are to be set up from the fork's app.

Waiting for Nevo:
- **RTL layout on the physical screen**: page order, swipe direction, mirrored tiles, and the top bar. Only scoped.
  It waits for Nevo's go-ahead and his choice of swipe direction. It would touch `core.yaml` and `components/`
  (LVGL `base_dir` on the screen, plus mirrored grid placement), so it is a sizable firmware change.
- **Page visibility as Home Assistant entities**: an entity per page (shown or hidden) and a "current page" select,
  for a dynamic screen. For example, show the washer page while it runs, or bus and weather pages before work.
  Discussed on 2026-10-27, and Nevo said "no changes for now".
- **Review of the Hebrew translation** by a Hebrew speaker, then `"checked": true` in `he.json` `_meta`.
- **An upstream pull request** from `hebrew`, only when Nevo asks.
