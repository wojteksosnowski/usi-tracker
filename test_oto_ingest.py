import requests

resp = requests.post(
    "http://127.0.0.1:5000/api/investments/register-bulk",
    json={"portal": "oto", "items": ["https://www.otodom.pl/pl/oferta/nowa-czestochowa-malopolska-ID4BFOJ"]}
)
print(resp.json())
