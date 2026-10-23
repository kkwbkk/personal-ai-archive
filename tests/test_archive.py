import base64
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "archive.py"
spec = importlib.util.spec_from_file_location("archive_tool", MODULE_PATH)
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


class ArchiveTests(unittest.TestCase):
    def test_write_path_rejects_bypass(self):
        for path in ["memory/../identity/profile.md", "/memory/a.md", "memory//a.md", "memory/./a.md",
                     "memory/%2e%2e/a.md", "memory\\a.md", "identity/profile.md", "memory/.hidden/a.md",
                     "memory/a.md\n", "workflow/script.py"]:
            with self.subTest(path=path), self.assertRaises(archive.ArchiveError):
                archive.validate_write_path(path)
        self.assertEqual(archive.validate_write_path("memory/experiences.md"), "memory/experiences.md")

    def test_rejects_secrets_empty_and_large_content(self):
        for text in ["", " \n", "ghp_" + "a" * 36, "-----BEGIN " + "OPENSSH PRIVATE KEY-----", "a" * 40000]:
            with self.subTest(text=text[:30]), self.assertRaises(archive.ArchiveError):
                archive.check_public_text(text)
        archive.check_public_text("## 经验\n来源：用户授权。\n")

    def test_append_preserves_content_and_prevents_duplicate(self):
        existing = "# AI-WRITABLE: 经验\n\n旧条目\n"
        result = archive.append_entry(existing, "## 新条目\n来源：本次任务")
        self.assertTrue(result.startswith(existing))
        self.assertIn("旧条目", result)
        self.assertIn("新条目", result)
        with self.assertRaises(archive.ArchiveError):
            archive.append_entry(result, "## 新条目\n来源：本次任务")

    def test_ancestor_requires_main_merge_base(self):
        target = "a" * 40
        for status in ["ahead", "identical"]:
            self.assertTrue(archive.is_main_ancestor({"status": status, "merge_base_commit": {"sha": target}}, target))
        for value in [{"status": "diverged", "merge_base_commit": {"sha": target}},
                      {"status": "ahead", "merge_base_commit": {"sha": "b" * 40}}, {}]:
            self.assertFalse(archive.is_main_ancestor(value, target))

    def test_export_pins_one_snapshot_and_ignores_other_files(self):
        sha = "a" * 40
        calls = []
        def get(endpoint):
            calls.append(endpoint)
            if "/commits/" in endpoint:
                return {"sha": sha}
            if "/git/trees/" in endpoint:
                return {"tree": [{"path": "identity/profile.md", "type": "blob", "mode": "100644", "sha": "b" * 40},
                                 {"path": "scripts/ignore.md", "type": "blob", "mode": "100644", "sha": "c" * 40}]}
            return {"encoding": "base64", "content": base64.b64encode("# AI-READONLY: 身份\n{{职业}}".encode()).decode()}
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "bundle.md"
            result = archive.export_bundle("owner/repo", "main", target, get=get)
            self.assertEqual(result["files"], 1)
            self.assertIn(sha, target.read_text())
            self.assertIn("{{职业}}", target.read_text())
            self.assertNotIn("scripts/ignore.md", target.read_text())
        self.assertIn("repos/owner/repo/git/trees/" + sha + "?recursive=1", calls)

    def test_export_refuses_truncated_tree(self):
        def get(endpoint):
            return {"sha": "a" * 40} if "/commits/" in endpoint else {"truncated": True}
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(archive.ArchiveError):
            archive.export_bundle("owner/repo", "main", Path(folder) / "bundle.md", get=get)

    def test_propose_writes_branch_based_on_pinned_main(self):
        calls = []
        sha = "a" * 40
        def api(endpoint, method="GET", payload=None):
            calls.append((endpoint, method, payload))
            if endpoint.endswith("/commits/main"):
                return {"sha": sha}
            if "/git/trees/" in endpoint:
                return {"tree": [{"path": "memory/experiences.md", "type": "blob", "mode": "100644"}]}
            if "/contents/" in endpoint and method == "GET":
                self.assertTrue(endpoint.endswith("?ref=" + sha))
                return {"type": "file", "encoding": "base64", "sha": "b" * 40,
                        "content": base64.b64encode(b"# AI-WRITABLE: Existing\n").decode()}
            if method == "PUT":
                return {"commit": {"sha": "c" * 40}}
            if endpoint.endswith("/pulls"):
                return {"html_url": "https://github.com/owner/repo/pull/1"}
            return {}
        with tempfile.TemporaryDirectory() as folder:
            entry = Path(folder) / "entry.md"
            entry.write_text("## 新经验\n来源：授权任务", encoding="utf-8")
            result = archive.propose("owner/repo", "memory/experiences.md", entry, "记录新经验", api=api)
        self.assertEqual(result["status"], "proposed_not_merged")
        self.assertEqual(result["commit"], "c" * 40)
        write = next(call for call in calls if call[1] == "PUT")
        self.assertEqual(write[2]["sha"], "b" * 40)
        self.assertTrue(write[2]["branch"].startswith("ai/update-"))
        self.assertTrue(base64.b64decode(write[2]["content"]).startswith(b"# AI-WRITABLE: Existing\n"))

    def test_propose_refuses_readonly_tag_before_writing(self):
        calls = []
        def api(endpoint, method="GET", payload=None):
            calls.append((endpoint, method, payload))
            if endpoint.endswith("/commits/main"):
                return {"sha": "a" * 40}
            if "/git/trees/" in endpoint:
                return {"tree": [{"path": "memory/experiences.md", "type": "blob", "mode": "100644"}]}
            if "/contents/" in endpoint:
                return {"type": "file", "encoding": "base64", "sha": "b" * 40,
                        "content": base64.b64encode(b"# AI-READONLY: Locked\n").decode()}
            self.fail("Read-only document must not cause an API write")
        with tempfile.TemporaryDirectory() as folder:
            entry = Path(folder) / "entry.md"
            entry.write_text("## 新经验\n来源：授权任务", encoding="utf-8")
            with self.assertRaisesRegex(archive.ArchiveError, "AI-WRITABLE"):
                archive.propose("owner/repo", "memory/experiences.md", entry, "记录新经验", api=api)
        self.assertTrue(all(call[1] == "GET" for call in calls))

    def test_restore_preserves_main_parent_and_target_tree(self):
        target, head, tree, new_commit = [c * 40 for c in "abcd"]
        calls = []
        def api(endpoint, method="GET", payload=None):
            calls.append((endpoint, method, payload))
            if endpoint.endswith("/commits/main"):
                return {"sha": head}
            if "/compare/" in endpoint:
                return {"status": "ahead", "merge_base_commit": {"sha": target}}
            if endpoint.endswith("/git/commits/" + target):
                return {"tree": {"sha": tree}}
            if endpoint.endswith("/git/commits/" + head):
                return {"tree": {"sha": "e" * 40}}
            if endpoint.endswith("/git/commits"):
                return {"sha": new_commit}
            if endpoint.endswith("/pulls"):
                return {"html_url": "https://github.com/owner/repo/pull/2"}
            return {}
        result = archive.restore("owner/repo", target, "恢复已确认的历史快照", api=api)
        self.assertEqual(result["commit"], new_commit)
        commit = next(call for call in calls if call[0].endswith("/git/commits"))
        self.assertEqual(commit[2]["parents"], [head])
        self.assertEqual(commit[2]["tree"], tree)
        self.assertFalse(any(call[1] == "PATCH" for call in calls))


if __name__ == "__main__":
    unittest.main()
