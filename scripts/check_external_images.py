
import os
import json

# Target directory
public_data_dir = "/Volumes/Samsam/Public/USIdata"

def find_external_images():
    external_image_investments = []
    
    # Walk through the directory to find all json files
    for root, dirs, files in os.walk(public_data_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # Inspect 'image_urls' or 'photos'
                        # As per analyzed file, these fields seem to hold URLs
                        urls = data.get('image_urls', [])
                        photos = data.get('photos', [])
                        
                        # Check if any element in these lists is an external URL
                        if any(isinstance(u, str) and u.startswith('http') for u in urls) or \
                           any(isinstance(p, str) and p.startswith('http') for p in photos):
                            external_image_investments.append(file_path)
                            
                except Exception as e:
                    pass # Skip unreadable files
    return external_image_investments

if __name__ == "__main__":
    results = find_external_images()
    for res in results:
        print(res)
