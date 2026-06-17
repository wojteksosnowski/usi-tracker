import json
from pathlib import Path
from python_worker.backfill_image_paths import run_backfill

def test_backfill_image_paths(tmp_path):
    data_dir = tmp_path / "USIdata"
    usi_dir = tmp_path / "USI"
    
    data_dir.mkdir()
    usi_dir.mkdir()
    
    dev_slug = "dev1"
    inv_slug = "inv1"
    
    inv_data_dir = data_dir / dev_slug / inv_slug
    inv_data_dir.mkdir(parents=True)
    
    inv_img_dir = usi_dir / dev_slug / inv_slug
    inv_img_dir.mkdir(parents=True)
    
    usi_file = inv_data_dir / "usi_rp_123.json"
    initial_data = {
        "image_urls": [
            "https://example.com/cdn/1.jpg",
            "/Public/USI/dev1/inv1/2.jpg"
        ],
        "image_paths": [],
        "images_count": 0
    }
    
    with open(usi_file, "w", encoding="utf-8") as f:
        json.dump(initial_data, f)
        
    (inv_img_dir / "photo1.jpg").touch()
    (inv_img_dir / "photo2.png").touch()
    (inv_img_dir / "not_an_image.txt").touch()
    
    updated, errors = run_backfill(data_dir, usi_dir)
    
    assert updated == 1
    assert errors == 0
    
    with open(usi_file, "r", encoding="utf-8") as f:
        result_data = json.load(f)
        
    assert result_data["image_urls"] == ["https://example.com/cdn/1.jpg"]
    
    expected_paths = [
        "/Public/USI/dev1/inv1/photo1.jpg",
        "/Public/USI/dev1/inv1/photo2.png"
    ]
    assert sorted(result_data["image_paths"]) == sorted(expected_paths)
    assert result_data["images_count"] == 2
