import sys
import subprocess
import json

# --- 1. AUTO-INSTALLER ---
# If you don't have the 'requests' tool, this installs it automatically.
try:
    import requests
except ImportError:
    print("Installing 'requests' library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# --- 2. CONFIGURATION ---
# !!! PASTE YOUR KEY BELOW INSIDE THE QUOTES !!!
api_key = "8fe8ee3a04b802df823d740526e2023e0539c25f" 

# --- 3. THE TEST ---
def run_test():
    if "PASTE" in api_key:
        print("\n[ERROR] You didn't update the API Key! Please paste your key in line 16.\n")
        return

    print(f"--- Testing Serper API Key... ---")
    
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": "Apple Inc", "gl": "us"})
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        
        if response.status_code == 200:
            print("\n✅ SUCCESS! API is working.")
            print(f"Sample Result: {response.json().get('organic', [{}])[0].get('title')}")
        elif response.status_code == 401:
            print("\n❌ ERROR: API Key Rejected. Check if you copied it correctly.")
        else:
            print(f"\n⚠️ ERROR: Status Code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")

if __name__ == "__main__":
    run_test()