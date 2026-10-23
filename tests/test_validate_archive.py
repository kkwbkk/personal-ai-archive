import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location("validate_archive", Path(__file__).resolve().parents[1] / "scripts" / "validate_archive.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class ArchiveValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.paths = []
        for relative in validator.REQUIRED_TEMPLATES:
            path = self.root / relative
            path.parent.mkdir(exist_ok=True)
            path.write_text("# AI-WRITABLE: Example\n\n{{placeholder}}\n", encoding="utf-8")
            self.paths.append(path.relative_to(self.root).as_posix())

    def test_valid_five_directory_scaffold(self):
        self.assertEqual(validator.validate_paths(self.root, self.paths), [])

    def test_missing_directory_and_tag_reported_together(self):
        (self.root / "workflow/preferences.md").write_text("# No AI tag\n", encoding="utf-8")
        errors = validator.validate_paths(self.root, [path for path in self.paths if not path.startswith("skills/")])
        self.assertTrue(any("first line" in error for error in errors))
        self.assertTrue(any(error.startswith("skills/") for error in errors))

    def test_symlink_is_never_followed(self):
        link = self.root / "memory/external.md"
        link.symlink_to(self.root / "identity/profile.md")
        errors = validator.validate_paths(self.root, self.paths + ["memory/external.md"])
        self.assertTrue(any("symbolic links" in error for error in errors))

    def test_secret_and_private_key_patterns(self):
        # Assemble fixtures so the repository's own publication check stays useful.
        for sample in ["ghp_" + "A" * 36, "github_" + "pat_" + "A" * 30,
                       "sk-" + "proj-" + "a" * 32, "-----BEGIN " + "PRIVATE KEY-----"]:
            self.assertTrue(validator.has_obvious_secret(sample))
        self.assertFalse(validator.has_obvious_secret("{{GitHub令牌（不要填入仓库）}}"))

    def test_oversized_markdown_is_rejected(self):
        (self.root / "memory/experiences.md").write_bytes(b"x" * (validator.MAX_FILE_BYTES + 1))
        self.assertTrue(any("exceeds" in error for error in validator.validate_paths(self.root, self.paths)))

    def test_path_traversal_is_rejected(self):
        self.assertTrue(any("unsafe" in error for error in validator.validate_paths(self.root, self.paths + ["../outside.md"])))

    def test_deletion_check_uses_git_history(self):
        def git(*args):
            return subprocess.run(["git", "-C", str(self.root), *args], text=True, capture_output=True, check=True).stdout.strip()
        git("init", "-q")
        git("config", "user.name", "Validation test")
        git("config", "user.email", "test@example.invalid")
        git("add", ".")
        git("commit", "-qm", "initial scaffold")
        base = git("rev-parse", "HEAD")
        (self.root / "memory/experiences.md").unlink()
        git("add", "-A")
        git("commit", "-qm", "delete core document")
        errors = validator.check_deletions(self.root, base)
        self.assertEqual(len(errors), 1)
        self.assertIn("memory/experiences.md", errors[0])
        self.assertIn("40-character", validator.check_deletions(self.root, "--option")[0])

    def test_new_documents_can_be_removed_during_historical_restore(self):
        def git(*args):
            return subprocess.run(["git", "-C", str(self.root), *args], text=True, capture_output=True, check=True).stdout.strip()
        git("init", "-q")
        git("config", "user.name", "Validation test")
        git("config", "user.email", "test@example.invalid")
        extra = self.root / "memory/later-experience.md"
        extra.write_text("# AI-WRITABLE: Later experience\n", encoding="utf-8")
        git("add", ".")
        git("commit", "-qm", "newer snapshot")
        base = git("rev-parse", "HEAD")
        extra.unlink()
        git("add", "-A")
        git("commit", "-qm", "restore earlier snapshot")
        self.assertEqual(validator.check_deletions(self.root, base), [])
        self.assertEqual(validator.validate_paths(self.root, self.paths), [])

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], text=True,
                              capture_output=True, check=True).stdout.strip()

    def restore_history(self):
        self.git("init", "-q")
        self.git("config", "user.name", "Validation test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("add", ".")
        self.git("commit", "-qm", "initial archive")
        target = self.git("rev-parse", "HEAD")
        (self.root / "memory/experiences.md").write_text("# AI-WRITABLE: Updated experience\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "later main")
        base = self.git("rev-parse", "HEAD")
        tree = self.git("rev-parse", target + "^{tree}")
        head = self.git("commit-tree", tree, "-p", base, "-m", "restore: snapshot " + target)
        return target, base, tree, head

    def test_fresh_restore_exactly_matches_historical_tree(self):
        _target, base, _tree, head = self.restore_history()
        self.assertEqual(validator.check_restore(self.root, base, head), [])

    def test_stale_restore_requires_regeneration(self):
        _target, _base, _tree, head = self.restore_history()
        (self.root / "memory/preferences.md").write_text("# AI-WRITABLE: Newer preference\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "main advanced after restore PR")
        latest_base = self.git("rev-parse", "HEAD")
        self.assertTrue(any("stale" in error for error in validator.check_restore(self.root, latest_base, head)))

    def test_update_branch_merge_cannot_bypass_restore_check(self):
        _target, base, tree, head = self.restore_history()
        updated = self.git("commit-tree", tree, "-p", head, "-p", base,
                           "-m", "Merge branch main into ai/restore-example")
        errors = validator.check_restore(self.root, base, updated)
        self.assertTrue(any("stale" in error for error in errors))
        self.assertTrue(any("original" in error for error in errors))

    def test_restore_marker_alone_cannot_hide_different_content(self):
        target, base, _tree, _head = self.restore_history()
        wrong_tree = self.git("rev-parse", base + "^{tree}")
        wrong_head = self.git("commit-tree", wrong_tree, "-p", base, "-m", "restore: snapshot " + target)
        errors = validator.check_restore(self.root, base, wrong_head)
        self.assertTrue(any("exactly match" in error for error in errors))

    def test_restore_rejects_invalid_commit_arguments(self):
        errors = validator.check_restore(self.root, "--option", "a" * 40)
        self.assertIn("40-character", errors[0])


if __name__ == "__main__":
    unittest.main()
