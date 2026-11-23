---
name: hebrew-translations
description: Fill in or fix Hebrew texts in screen_manager/translations/he.json (after an upstream sync adds keys, or when Nevo corrects wording) and verify them. Use for any Hebrew translation work in this fork.
---

# Hebrew translations

`screen_manager/translations/he.json` is the only source. No generator script exists any more. Read
`docs/TRANSLATING.md` for the format: nested keys, `{placeholders}`, and plural objects with `one` and `other`.

## Find what is missing

```sh
python3 tools/i18n.py check          # lists missing keys, wrong placeholders, letters screens can't draw
```

For a precise list of missing or stale keys, compare with English:

```python
import json
def flat(d, p=''):
    for k, v in d.items():
        if k == '_meta': continue
        if isinstance(v, dict) and not set(v) <= {'zero','one','two','few','many','other'}:
            yield from flat(v, f'{p}{k}.')
        else:
            yield f'{p}{k}', v
en = dict(flat(json.load(open('screen_manager/translations/en.json'))))
he = dict(flat(json.load(open('screen_manager/translations/he.json'))))
missing = [k for k in en if k not in he]
extra = [k for k in he if k not in en]
print(len(missing), 'missing;', len(extra), 'no longer in English')
```

Also look at the English texts upstream *changed* in the merge (`git diff <old>..upstream/dev -- screen_manager/translations/en.json`).
A changed English text means the Hebrew one may be stale too.

## Write them

- Keep the key order of `en.json`. Insert the new keys where English has them, and remove keys English dropped.
- Keep every `{placeholder}` exactly as written, and keep HTML or markdown that the English has.
- Plurals use `one` and `other` (`_meta.plural` is `one_other`).
- **Screen texts** (`screen.*`, `addon.screen.*`) must be short, about as long as the English, because they sit on a
  small display. `check` prints a note when one is much longer.
- **Use only letters the screens can draw**: the Hebrew letters in `SCRIPT_GLYPHS_HEBREW` (`packages/core.yaml`),
  with maqaf ־, geresh ׳, gershayim ״ and ₪, plus Latin, digits and common punctuation. No niqqud.
- Register: plain modern Hebrew, imperative for buttons (שמור, מחק), the same terms as Home Assistant's own Hebrew
  where it has one. Keep product and entity names (Home Assistant, ESPHome, Tessera, Wi-Fi) in Latin letters.
- Leave `_meta.checked` false. Only a human review sets it to true.

Write a helper script for a large batch if useful. It goes in the scratchpad, not in the repo.

## Verify

```sh
python3 tools/i18n.py check            # must end with 0 problems
python3 tools/i18n.py header --check   # unchanged unless en.json's screen keys changed
python3 -m pytest tests/test_script_glyphs.py -q
cd web && npm test && npm run build    # the editor bundles he.json: commit screen_manager/app/static too
```

To look at the result, run the app locally and screenshot the editor in Hebrew with Playwright. The editor's own
pages should read right to left, and screen mockups left to right with each label ordered by its own text.

Commit on `hebrew`, as `Hebrew: ...`. Then merge `hebrew` into `hebrew-screen` (sync-upstream skill, step 3).
