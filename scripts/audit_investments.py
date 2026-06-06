
import os
import json
import csv

data_dir = '/Volumes/Samsam/Public/USIdata'
output_file = 'audit_report.csv'

def get_audit_info(data):
    audit = data.get('audit', {})
    created_at = audit.get('created_at', 'N/A')
    updated_at = audit.get('updated_at', 'N/A')
    
    # Heuristic for scraper version based on project history
    # v0.7.0 introduced strict ID-based saving (2026-05-21)
    scraper_version = 'pre-v0.7.0'
    if created_at != 'N/A':
        # Simple date comparison
        if created_at >= '2026-05-21':
            scraper_version = 'v0.7.0+'
            
    return created_at, updated_at, scraper_version

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
    print(f"Counts: {counts}")

if __name__ == "__main__":
    audit_investments()
