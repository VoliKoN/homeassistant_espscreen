"""The letters of a language written in another script (docs/TRANSLATING.md, "Letters"): only a screen built in such a
language carries them in its five text fonts, and the app keeps them only in what it sends to such a screen.

- packages/core.yaml has one list per script (SCRIPT_GLYPHS_CYRILLIC) and SCRIPT_GLYPHS picks it by LANGUAGE; the text
  fonts end on "${SCRIPT_GLYPHS}", empty for every other language, so no other screen spends flash on them.
- header_bar.SCRIPT_GLYPHS has the same letters, and clean_text keeps them for a screen whose language's `_meta.script`
  names that script; every other screen gets them dropped, as before.
- The languages SCRIPT_GLYPHS takes are exactly the translation files that say `"script": "cyrillic"`.
"""
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'screen_manager/app'))
import profiles  # noqa: E402
import header_bar  # noqa: E402
import i18n  # noqa: E402

CORE = (ROOT / 'packages/core.yaml').read_text(encoding='utf-8')
TEXT_FONTS = ('headline', 'watch_value', 'label', 'sublabel', 'sublabel_big')


def core_list(script):
    return re.search(r'(?m)^  SCRIPT_GLYPHS_' + script.upper() + r': "([^"]*)"', CORE).group(1)


class FirmwareLetters(unittest.TestCase):
    def test_the_app_and_the_firmware_name_the_same_letters(self):
        self.assertEqual(set(core_list('cyrillic')), set(header_bar.SCRIPT_GLYPHS['cyrillic']))
        self.assertEqual(len(core_list('cyrillic')), len(set(core_list('cyrillic'))), 'a letter twice')
        # None of them is a Latin glyph already in the fonts, which ESPHome refuses as a duplicate.
        self.assertFalse(set(core_list('cyrillic')) & set(header_bar.GLYPHS))

    def test_every_text_font_takes_the_letters_of_its_language_last(self):
        for font in TEXT_FONTS:
            start = CORE.index('    id: ' + font + '\n')
            glyphs = CORE[CORE.index('    glyphs: [', start):]
            glyphs = glyphs[:glyphs.index(']\n') + 1]
            self.assertTrue(glyphs.endswith('"${SCRIPT_GLYPHS}"]'), font)

    def test_the_letters_go_only_into_a_screen_built_in_such_a_language(self):
        expression = re.search(r"(?m)^  SCRIPT_GLYPHS: '(.*)'$", CORE).group(1)
        for language, carried in (('en', ''), ('nl', ''), ('pt-BR', ''), ('ru', core_list('cyrillic'))):
            with self.subTest(language=language):
                values = {'LANGUAGE': language, 'SCRIPT_GLYPHS_CYRILLIC': core_list('cyrillic')}
                self.assertEqual(profiles.resolve(expression, values), carried)

    def test_the_languages_it_takes_are_the_cyrillic_translation_files(self):
        named = set(re.findall(r'"([a-z]{2,3})"', re.search(r'(?m)^  SCRIPT_GLYPHS: (.*)$', CORE).group(1)))
        files = {path.stem for path in (ROOT / 'screen_manager/translations').glob('*.json')
                 if json.loads(path.read_text(encoding='utf-8')).get('_meta', {}).get('script') == 'cyrillic'}
        self.assertEqual(named, files)


class AppLetters(unittest.TestCase):
    def tearDown(self):
        i18n.SCREEN.set(None)

    def test_a_russian_screen_keeps_its_letters_and_any_other_drops_them(self):
        i18n.SCREEN.set({'language': 'ru', 'legacy': False})
        self.assertEqual(i18n.screen_script(), 'cyrillic')
        self.assertEqual(header_bar.clean_text('Кухня, свет 2'), 'Кухня, свет 2')
        i18n.SCREEN.set({'language': 'nl', 'legacy': False})
        self.assertEqual(i18n.screen_script(), 'latin')
        self.assertEqual(header_bar.clean_text('Свет 2'), '2')
        # Firmware from before the languages draws the old letters only, whatever the language.
        i18n.SCREEN.set({'language': 'ru', 'legacy': True})
        self.assertEqual(header_bar.clean_text('Кухня'), '')



class HebrewLetters(unittest.TestCase):
    """Hebrew (no Roboto letters): its letters come from NotoSansHebrew as each text font's last extra, filled by
    SCRIPT_GLYPHS_NOTO on a screen built in Hebrew only, and LVGL's BiDi is built in on such a screen alone."""

    def expression(self, name):
        return re.search(r"(?m)^  " + name + r": '(.*)'$", CORE).group(1)

    def tearDown(self):
        i18n.SCREEN.set(None)

    def test_the_app_and_the_firmware_name_the_same_letters(self):
        self.assertEqual(set(core_list('hebrew')), set(header_bar.SCRIPT_GLYPHS['hebrew']))
        self.assertEqual(len(core_list('hebrew')), len(set(core_list('hebrew'))), 'a letter twice')
        self.assertFalse(set(core_list('hebrew')) & set(header_bar.GLYPHS))

    def test_every_text_font_takes_them_from_noto_at_its_own_weight(self):
        for font in TEXT_FONTS:
            start = CORE.index('    id: ' + font + '\n')
            end = re.compile(r'(?m)^  - file: |^\S').search(CORE, start)
            block = CORE[CORE.rindex('\n  - file: ', 0, start):end.start() if end else None]
            weight = re.search(r'Roboto-(\d+)\.ttf', block).group(1)
            self.assertIn('      - file: "${FONT_DIR}/NotoSansHebrew-' + weight + '.ttf"\n'
                          '        glyphs: ["${SCRIPT_GLYPHS_NOTO}"]', block, font)
            self.assertTrue((ROOT / 'fonts' / f'NotoSansHebrew-{weight}.ttf').exists())

    def test_the_letters_and_bidi_go_only_into_a_screen_built_in_hebrew(self):
        for language, letters, bidi in (('en', '', '0'), ('ru', '', '0'), ('he', core_list('hebrew'), '1')):
            with self.subTest(language=language):
                values = {'LANGUAGE': language, 'SCRIPT_GLYPHS_HEBREW': core_list('hebrew')}
                self.assertEqual(profiles.resolve(self.expression('SCRIPT_GLYPHS_NOTO'), values), letters)
                self.assertEqual(profiles.resolve(self.expression('LVGL_BIDI'), values), bidi)
        self.assertIn('- -DLV_USE_BIDI=${LVGL_BIDI}', CORE)

    def test_the_languages_it_takes_are_the_hebrew_translation_files(self):
        named = set(re.findall(r'"([a-z]{2,3})"', self.expression('SCRIPT_GLYPHS_NOTO')))
        files = {path.stem for path in (ROOT / 'screen_manager/translations').glob('*.json')
                 if json.loads(path.read_text(encoding='utf-8')).get('_meta', {}).get('script') == 'hebrew'}
        self.assertEqual(named, files)

    def test_noto_carries_every_letter(self):
        from fontTools.ttLib import TTFont
        for weight in ('400', '500', '700'):
            cmap = TTFont(ROOT / 'fonts' / f'NotoSansHebrew-{weight}.ttf').getBestCmap()
            self.assertLessEqual({ord(char) for char in core_list('hebrew')}, set(cmap), weight)

    def test_a_hebrew_screen_keeps_its_letters_without_points_and_any_other_drops_them(self):
        i18n.SCREEN.set({'language': 'he', 'legacy': False})
        self.assertEqual(i18n.screen_script(), 'hebrew')
        self.assertEqual(header_bar.clean_text('אור בסלון 2'), 'אור בסלון 2')
        self.assertEqual(header_bar.clean_text('שָׁלוֹם ₪5'), 'שלום ₪5')
        i18n.SCREEN.set({'language': 'en', 'legacy': False})
        self.assertEqual(header_bar.clean_text('סלון 2'), '2')

if __name__ == '__main__':
    unittest.main()
