from pathlib import Path
import tomllib
import unittest


class Authorship(unittest.TestCase):
    def test_original_author_and_packaged_notices_agree(self):
        root = Path(__file__).resolve().parents[1]
        notice = (root / "NOTICE").read_text(encoding="utf-8")
        license_text = (root / "LICENSE").read_text(encoding="utf-8")
        metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertIn("The code in this repository is original code by Axl Ibiza, MBA.", notice)
        self.assertIn("Copyright (c) 2026 Axl Ibiza, MBA", notice)
        self.assertIn("Copyright (c) 2026 Axl Ibiza, MBA", license_text)
        self.assertNotIn("Copyright (c) 2025 Nous Research", notice)
        self.assertEqual(metadata["project"]["authors"], [{"name": "Axl Ibiza, MBA"}])
        self.assertEqual(metadata["project"]["dependencies"], [])
