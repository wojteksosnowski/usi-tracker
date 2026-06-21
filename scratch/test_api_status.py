from python_worker.ui_server import app
with app.test_client() as client:
    resp = client.get("/api/investments?status=Brak")
    data = resp.get_json()
    if data and "data" in data:
        bad = [x for x in data["data"] if x.get("status") == "Niedostateczne dane"]
        print(f"Total Brak returned: {len(data['data'])}")
        print(f"Bad returned: {len(bad)}")
