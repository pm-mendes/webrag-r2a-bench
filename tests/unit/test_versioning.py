from webrag_bench.core.versioning import ENV_VAR, bench_version


def test_build_time_version_takes_precedence(monkeypatch):
    monkeypatch.setenv(ENV_VAR, "freeze-p-2026-09-26")
    assert bench_version() == "freeze-p-2026-09-26"


def test_git_version_otherwise(monkeypatch):
    monkeypatch.delenv(ENV_VAR, raising=False)
    assert bench_version()  # a commit id, a tag, or "untagged"
