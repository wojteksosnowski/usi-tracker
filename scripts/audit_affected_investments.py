
import os
import json
import csv

data_dir = '/Volumes/Samsam/Public/USIdata'
output_file = 'audit_report_affected.csv'

def get_audit_info(data):
    audit = data.get('audit', {})
    created_at = audit.get('created_at', 'N/A')
    updated_at = audit.get('updated_at', 'N/A')
    
    scraper_version = 'pre-v0.7.0'
    if created_at != 'N/A' and created_at >= '2026-05-21':
        scraper_version = 'v0.7.0+'
            
    return created_at, updated_at, scraper_version

def is_affected(data):
    # Check 'image_urls' or 'photos' for external HTTP URLs
    urls = data.get('image_urls', []) + data.get('photos', [])
    return any(isinstance(u, str) and u.startswith('http') for u in urls)

def audit_investments():
    report = []
    
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.startswith('usi_') and file.endswith('.json'):
                source = 'unknown'
                if '_rp_' in file: source = 'rp'
                elif '_oto_' in file: source = 'oto'
                elif '_to_' in file: source = 'to'
                
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if is_affected(data):
                            created_at, updated_at, scraper_version = get_audit_info(data)
                            report.append([source, file_path, created_at, updated_at, scraper_version])
                except Exception:
                    continue
                    
    # Summarize and write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['source', 'file_path', 'created_at', 'updated_at', 'scraper_version'])
        writer.writerows(report)
        
    # Print counts
    counts = {'rp': 0, 'oto': 0, 'to': 0, 'unknown': 0}
    for row in report:
        counts[row[0]] += 1
    print(f"Counts of affected investments: {counts}")

if __name__ == "__main__":
    audit_investments()
