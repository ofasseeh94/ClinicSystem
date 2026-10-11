import importlib.util
import unittest
from pathlib import Path


class ScaffoldTests(unittest.TestCase):
    def test_required_repository_paths_exist(self):
        path = Path(__file__).resolve().parents[2] / "scripts" / "check_structure.py"
        spec = importlib.util.spec_from_file_location("structure", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.missing_paths(), [])
