"""不访问网络。"""

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from ytb_cc import (
    clean_entered_path,
    configured_output_dir,
    explorer_folder_uri,
    finder_folder_uri,
    main,
    output_file,
    save_output_dir,
    select_track,
)
from ytb_cc.setup import run_setup


def track(code: str, generated: bool, name: str | None = None):
    return SimpleNamespace(
        language_code=code,
        language=name or code,
        is_generated=generated,
    )


def picked(tracks) -> str:
    chosen = select_track(tracks)
    kind = "自动" if chosen.is_generated else "人工"
    return f"{chosen.language_code}/{kind}"


class LangPriorityTest(unittest.TestCase):
    def test_a_chinese_manual_beats_english(self):
        self.assertEqual(
            picked([
                track("en", False),
                track("zh-Hans", False),
                track("en", True),
            ]),
            "zh-Hans/人工",
        )
        self.assertEqual(
            picked([track("en-US", False), track("zh-Hant", False)]),
            "zh-Hant/人工",
        )

    def test_b_english_when_no_chinese_manual(self):
        self.assertEqual(
            picked([track("ja", False), track("en", True), track("zh-Hans", True)]),
            "en/自动",
        )
        self.assertEqual(
            picked([track("en", True), track("en-US", False)]),
            "en-US/人工",
        )

    def test_c_other_manual(self):
        self.assertEqual(
            picked([track("es", True), track("ja", False), track("de", False)]),
            "ja/人工",
        )

    def test_d_first_auto(self):
        self.assertEqual(
            picked([track("ja", True), track("es", True)]),
            "ja/自动",
        )

    def test_empty(self):
        with self.assertRaises(RuntimeError):
            select_track([])


class OutputTest(unittest.TestCase):
    def test_same_name(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = output_file(root, "TED-Ed", "Same Title")
            second = output_file(root, "TED-Ed", "Same Title")
            self.assertEqual(first, second)
            self.assertNotIn("[", first.name)
            first.parent.mkdir()
            first.write_text("旧\n", encoding="utf-8")
            second.write_text("新\n", encoding="utf-8")
            self.assertEqual(second.read_text(encoding="utf-8"), "新\n")
            self.assertEqual([p.name for p in first.parent.iterdir()], ["Same Title.txt"])

    def test_windows_uri_keeps_chinese(self):
        uri = explorer_folder_uri(r"E:\YouTube字幕\犬哥網站\a.txt")
        self.assertEqual(uri, "file:///E:/YouTube字幕/犬哥網站/")
        spaced = explorer_folder_uri(r"E:\YouTube字幕\Imran Siddiq\a.txt")
        self.assertIn("Imran%20Siddiq", spaced)
        self.assertIn("YouTube字幕", spaced)

    def test_mac_uri_encodes_chinese(self):
        uri = finder_folder_uri("/Users/me/字幕/a.txt")
        self.assertEqual(uri, "file:///Users/me/%E5%AD%97%E5%B9%95/")


class SetupTest(unittest.TestCase):
    def test_clean_quotes(self):
        self.assertEqual(clean_entered_path('  "/mnt/e/YouTube字幕"  '), "/mnt/e/YouTube字幕")

    def test_save_and_env_override(self):
        with TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.json"
            folder = Path(tmp) / "out"
            folder.mkdir()
            env = {"YTB_CC_CONFIG": str(cfg), "YTB_CC_DIR": ""}
            with patch.dict(os.environ, env, clear=False):
                os.environ.pop("YTB_CC_DIR", None)
                save_output_dir(folder)
                self.assertEqual(configured_output_dir(), folder)
                data = json.loads(cfg.read_text(encoding="utf-8"))
                self.assertEqual(data["output_dir"], str(folder))
                os.environ["YTB_CC_DIR"] = str(Path(tmp) / "other")
                self.assertEqual(configured_output_dir(), Path(tmp) / "other")

    def test_setup_creates_only_after_yes(self):
        with TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.json"
            dest = Path(tmp) / "字幕库"
            answers = iter([str(dest), "n"])
            with patch.dict(os.environ, {"YTB_CC_CONFIG": str(cfg)}, clear=False):
                code = run_setup(input_fn=lambda _prompt: next(answers), isatty=True, install=False)
            self.assertEqual(code, 1)
            self.assertFalse(dest.exists())
            self.assertFalse(cfg.exists())

    def test_setup_saves_existing_dir(self):
        with TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.json"
            dest = Path(tmp) / "字幕库"
            dest.mkdir()
            with patch.dict(os.environ, {"YTB_CC_CONFIG": str(cfg)}, clear=False):
                os.environ.pop("YTB_CC_DIR", None)
                code = run_setup(input_fn=lambda _prompt: str(dest), isatty=True, install=False)
                saved = configured_output_dir()
            self.assertEqual(code, 0)
            self.assertEqual(saved, dest.resolve())

    def test_no_tty(self):
        self.assertEqual(run_setup(isatty=False, install=False), 1)

    def test_main_without_config_does_not_fetch(self):
        with TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "missing.json"
            with patch.dict(os.environ, {"YTB_CC_CONFIG": str(cfg)}, clear=False):
                os.environ.pop("YTB_CC_DIR", None)
                with patch("sys.argv", ["ytb-cc", "dQw4w9WgXcQ"]):
                    code = main()
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
