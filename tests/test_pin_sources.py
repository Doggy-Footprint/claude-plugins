import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import pin_sources  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
A = "a" * 40
B = "b" * 40


def marketplace():
    return {
        "name": "m",
        "owner": {"name": "o"},
        "plugins": [
            {"name": "one", "source": {"source": "github", "repo": "o/one", "ref": "main"}},
            {"name": "two", "source": {"source": "github", "repo": "o/two", "sha": A}},
            {"name": "local", "source": "./plugins/local"},
            {"name": "url", "source": {"source": "url", "url": "https://example.com/x.git"}},
        ],
    }


class PinTest(unittest.TestCase):
    def test_sets_sha_for_github_sources_only(self):
        calls = []

        def resolve(repo, ref):
            calls.append((repo, ref))
            return B

        data = marketplace()
        changes = pin_sources.pin(data, resolve)
        self.assertEqual(calls, [("o/one", "main"), ("o/two", None)])
        self.assertEqual(changes, ["one none -> bbbbbbbbbbbb", "two aaaaaaaaaaaa -> bbbbbbbbbbbb"])
        self.assertEqual(data["plugins"][0]["source"], {"source": "github", "repo": "o/one", "ref": "main", "sha": B})
        self.assertEqual(data["plugins"][2]["source"], "./plugins/local")
        self.assertNotIn("sha", data["plugins"][3]["source"])

    def test_no_change_when_sha_is_current(self):
        data = marketplace()
        data["plugins"][0]["source"]["sha"] = A
        self.assertEqual(pin_sources.pin(data, lambda repo, ref: A), [])

    def test_main_writes_only_when_changed(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "marketplace.json"
            data = marketplace()
            data["plugins"][0]["source"]["sha"] = A
            text = json.dumps(data, indent=2) + "\n"
            path.write_text(text, encoding="utf-8")
            self.assertEqual(pin_sources.main([str(path)], resolve=lambda repo, ref: A), 0)
            self.assertEqual(path.read_text(encoding="utf-8"), text)
            self.assertEqual(pin_sources.main([str(path)], resolve=lambda repo, ref: B), 0)
            written = path.read_text(encoding="utf-8")
            self.assertTrue(written.endswith("}\n"))
            self.assertEqual(json.loads(written)["plugins"][1]["source"]["sha"], B)

    def test_main_reports_unresolvable_ref(self):
        def resolve(repo, ref):
            raise LookupError(f"{repo}: ref {ref} not found")

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "marketplace.json"
            path.write_text(json.dumps(marketplace()), encoding="utf-8")
            before = path.read_text(encoding="utf-8")
            self.assertEqual(pin_sources.main([str(path)], resolve=resolve), 2)
            self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_ls_remote_picks_branch_then_peeled_tag(self):
        out = f"{A}\trefs/tags/v1\n{B}\trefs/tags/v1^{{}}\n"
        with mock.patch.object(subprocess, "run", return_value=mock.Mock(stdout=out)) as run:
            self.assertEqual(pin_sources.ls_remote("o/r", "v1"), B)
        self.assertEqual(run.call_args.args[0][:3], ["git", "ls-remote", "https://github.com/o/r"])
        with mock.patch.object(subprocess, "run", return_value=mock.Mock(stdout=f"{A}\tHEAD\n")):
            self.assertEqual(pin_sources.ls_remote("o/r", None), A)
        with mock.patch.object(subprocess, "run", return_value=mock.Mock(stdout="")):
            with self.assertRaises(LookupError):
                pin_sources.ls_remote("o/r", "gone")


class MarketplaceTest(unittest.TestCase):
    def test_every_github_source_is_pinned_to_a_full_sha(self):
        data = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        for entry in data["plugins"]:
            source = entry["source"]
            if isinstance(source, dict) and source.get("source") == "github":
                self.assertRegex(source.get("sha", ""), r"^[0-9a-f]{40}$", entry["name"])


if __name__ == "__main__":
    unittest.main()
