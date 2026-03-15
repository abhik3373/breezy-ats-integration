"""Quick test to verify keys and Breezy HR connection work."""
import os
from dotenv import load_dotenv
import requests

load_dotenv()

API_KEY = os.environ.get("BREEZY_API_KEY")
COMPANY_ID = os.environ.get("BREEZY_COMPANY_ID")
BASE_URL = os.environ.get("BREEZY_BASE_URL", "https://api.breezy.hr/v3")

headers = {"Authorization": API_KEY, "Content-Type": "application/json"}

print("🔍 Testing connection to Breezy HR...")
print(f"   API Key: {API_KEY[:8]}...{API_KEY[-4:]}")
print(f"   Company ID: {COMPANY_ID}")

# Test 1: Fetch jobs
url = f"{BASE_URL}/company/{COMPANY_ID}/positions"
resp = requests.get(url, headers=headers)

if resp.status_code == 200:
    jobs = resp.json()
    print(f"\n✅ SUCCESS! Found {len(jobs)} job(s):")
    for j in jobs:
        print(f"   - [{j.get('state')}] {j.get('name')} | ID: {j.get('_id')}")
    if not jobs:
        print("   (No jobs found — create one in Breezy HR dashboard first!)")
else:
    print(f"\n❌ FAILED! Status: {resp.status_code}")
    print(f"   Response: {resp.text}")
