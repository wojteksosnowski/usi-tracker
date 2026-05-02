import requests
import sys
import json

def test_here_url(url):
    print(f"Testing URL: {url[:100]}...")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("✅ SUCCESS: HTTP 200 OK")
            print(f"Content Type: {response.headers.get('Content-Type')}")
            return True
        else:
            print(f"❌ ERROR: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"Details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response Body: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❗ CRITICAL ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_here_api.py <URL>")
        sys.exit(1)
    
    test_here_url(sys.argv[1])
