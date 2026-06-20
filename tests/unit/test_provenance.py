from crypto_hedge_fund.provenance import UNKNOWN, canonical_config_hash, file_sha256, git_commit


def test_file_sha256(tmp_path) -> None:
    target = tmp_path / "sample.txt"
    target.write_text("abc", encoding="utf-8")

    assert file_sha256(target) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_canonical_config_hash_is_key_order_independent() -> None:
    left = {"b": 2, "a": {"x": 1}}
    right = {"a": {"x": 1}, "b": 2}

    assert canonical_config_hash(left) == canonical_config_hash(right)


def test_git_commit_returns_commit_or_unknown() -> None:
    commit = git_commit()

    assert commit == UNKNOWN or len(commit) == 40
