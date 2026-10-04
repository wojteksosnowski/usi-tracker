import os
import time

from python_worker.main import _raw_age_hours


def test_raw_age_ignores_archives_and_handles_missing(tmp_path):
    assert _raw_age_hours(tmp_path) is None
    cur = tmp_path / "raw_rp_1.json"
    cur.write_text("{}")
    arch = tmp_path / "raw_rp_1_20200101_000000.json"
    arch.write_text("{}")
    old = time.time() - 10 * 3600
    os.utime(cur, (old, old))
    os.utime(arch, None)  # świeże archiwum nie może maskować wieku aktualnego pliku
    assert 9.9 < _raw_age_hours(tmp_path) < 10.1
