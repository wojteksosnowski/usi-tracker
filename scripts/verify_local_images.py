
import os
import json
import hashlib

# Configuration
public_data_dir = "/Volumes/Samsam/Public/USIdata"
images_root_dir = "/Volumes/Samsam/Public/USI"

def get_url_hash(url):
    return hashlib.md5(url.encode('utf-8')).hexdigest()

def check_images_existence():
    stats = {"total_checked": 0, "found": 0, "missing": 0}
    
    # We will pick a few files to check as a sample instead of the whole dataset
    sample_files = [
        "/Volumes/Samsam/Public/USIdata/ziolkowski-s-c/oranzeria-bartnika-iii/usi_oto_4fQKi.json",
        "/Volumes/Samsam/Public/USIdata/022-investments/szalasa-5/usi_oto_4pcjZ.json"
    ]
    
    for file_path in sample_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Check 'image_urls' or 'photos'
            urls = data.get('image_urls', []) + data.get('photos', [])
            
            # The structure in USI folder often follows the developer/investment slug
            dev_slug = data.get('developer_slug')
            inv_slug = data.get('investment_slug')
            inv_images_dir = os.path.join(images_root_dir, dev_slug, inv_slug)
            
            print(f"Checking investment: {dev_slug}/{inv_slug}")
            
            for url in urls:
                if not isinstance(url, str) or not url.startswith('http'):
                    continue
                
                stats["total_checked"] += 1
                
                # We need to know how the system names images locally.
                # Often it's hash or filename from URL.
                url_hash = get_url_hash(url)
                
                # Check if any file in inv_images_dir matches
                found = False
                if os.path.exists(inv_images_dir):
                    for filename in os.listdir(inv_images_dir):
                        if url_hash in filename:
                            found = True
                            break
                            
                if found:
                    stats["found"] += 1
                    print(f"  FOUND: {url[:50]}...")
                else:
                    stats["missing"] += 1
                    print(f"  MISSING: {url[:50]}...")

    print(f"\nStats: {stats}")

if __name__ == "__main__":
    check_images_existence()
