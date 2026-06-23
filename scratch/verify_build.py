from python_worker.services.investment_identity import InvestmentIdentityResolver
from pathlib import Path

identity = InvestmentIdentityResolver(Path('/Volumes/Samsam/claude-py/usi-tracker/Public/USIdata'))
print("INV-29825:", identity.get_investment_resources('INV-29825'))
print("INV-29824:", identity.get_investment_resources('INV-29824'))
