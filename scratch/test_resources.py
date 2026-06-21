from python_worker.identity_resolver import IdentityResolver
from pathlib import Path
ident = IdentityResolver(Path("Public/USIdata"), Path("Public/USIdev"), Path("Public/USI"))
res = ident.get_investment_resources("oto_4BPpw")
print("images_dir:", res.get("images_dir"))
print("exists:", res.get("images_dir").exists() if res.get("images_dir") else "None")
