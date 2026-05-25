from python_worker.detect_similar_devs import normalize_name, fuzzy_match
import sys

n1 = "4Estates"
n2 = "4Estates"

norm1 = normalize_name(n1)
norm2 = normalize_name(n2)

print(f"Norm1: '{norm1}', Len: {len(norm1)}")
print(f"Norm2: '{norm2}', Len: {len(norm2)}")

if norm1 == norm2:
    print("Exact match.")
    if len(norm1) > 3:
        print("Length > 3. Should match!")
    else:
        print("Length <= 3. Ignored.")
else:
    print("Not exact.")
