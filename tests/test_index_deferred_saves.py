from python_worker.investment_index import InvestmentIndex


def _fresh_index(tmp_path):
    # Instancja poza singletonem — nigdy nie dotykamy prawdziwego Public/USIdata/_index.json
    idx = object.__new__(InvestmentIndex)
    idx._initialized = False
    idx.__init__(data_dir=tmp_path, public_usi_dir=tmp_path)
    assert idx.index_path.parent == tmp_path
    return idx


def test_deferred_saves_writes_once(tmp_path, monkeypatch):
    idx = _fresh_index(tmp_path)
    calls = []
    orig = idx._save_to_disk
    monkeypatch.setattr(idx, "_save_to_disk", lambda force=False: (calls.append(force), orig(force=force))[1])
    with idx.deferred_saves():
        for i in range(5):
            idx.add_or_update(f"IN-{i}", {"developer_slug": "d", "investment_slug": f"s{i}"})
        assert "IN-0" not in idx.index_path.read_text(encoding="utf-8")
    assert calls.count(True) == 1
    assert "IN-4" in idx.index_path.read_text(encoding="utf-8")
