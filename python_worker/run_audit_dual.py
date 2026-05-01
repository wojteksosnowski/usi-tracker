
import logging
from python_worker.csv_importer import audit_dual

logging.basicConfig(level=logging.INFO)

CSV_PATH = "reference-data/coda/USImaster.csv"

def run_audit():
    report = audit_dual(CSV_PATH)
    print("\n--- RAPORT AUDYTU REKORDÓW DUALNYCH W CSV ---")
    print(f"Suma wierszy w CSV: {report.get('total_rows')}")
    print(f"Rekordy z dwoma URLami: {report.get('dual_url')}")
    print(f"Rekordy z dwoma JSONami (gotowe do splitu): {report.get('dual_importable')}")
    print("\nTop 10 deweloperów z dualnymi rekordami:")
    for dev, count in report.get('by_developer_top10', []):
        print(f"- {dev}: {count}")

if __name__ == "__main__":
    run_audit()
