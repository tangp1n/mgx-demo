#!/usr/bin/env python3
"""Simple script to test the /health endpoint."""
import urllib.request
import urllib.error
import json
import sys

def test_health_endpoint():
    """Test the /health endpoint."""
    url = "http://localhost:8000/health"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.getcode()
            data = json.loads(response.read().decode())

            print(f"✅ Success! Status Code: {status_code}")
            print(f"Response: {data}")
            return True
    except urllib.error.URLError as e:
        if "Connection refused" in str(e) or "cannot connect" in str(e).lower():
            print("❌ Error: Could not connect to server. Is the server running?")
            print("   Start the server with: uv run uvicorn src.main:app --reload --port 8000")
        else:
            print(f"❌ Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_health_endpoint()
    sys.exit(0 if success else 1)

