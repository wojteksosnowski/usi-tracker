import pytest

def test_segment_filtering_logic():
    # Simulate the robust filtering logic implemented in investments.py
    def filter_by_segment(inv, segments):
        inv_segment = inv.get("segment") or inv.get("specifications", {}).get("segment")
        if segments and inv_segment not in segments:
            return False
        return True

    # Case 1: Segment at top level (new format)
    inv1 = {"name": "Inv 1", "segment": "mieszkania deweloperskie"}
    assert filter_by_segment(inv1, {"mieszkania deweloperskie"}) is True
    assert filter_by_segment(inv1, {"lokale inwestycyjne"}) is False

    # Case 2: Segment nested in specifications (old format/index)
    inv2 = {"name": "Inv 2", "specifications": {"segment": "segmenty i domy"}}
    assert filter_by_segment(inv2, {"segmenty i domy"}) is True
    assert filter_by_segment(inv2, {"mieszkania deweloperskie"}) is False

    # Case 3: Both present (should prefer top level)
    inv3 = {"name": "Inv 3", "segment": "prs", "specifications": {"segment": "mieszkania deweloperskie"}}
    assert filter_by_segment(inv3, {"prs"}) is True
    assert filter_by_segment(inv3, {"mieszkania deweloperskie"}) is False

    # Case 4: No segment
    inv4 = {"name": "Inv 4"}
    assert filter_by_segment(inv4, {"prs"}) is False
    assert filter_by_segment(inv4, set()) is True # Empty segments filter = all pass
