import requests
from core.config import API_BASE_URL, CLUSTER_ID

def get(endpoint):
    url = f"{API_BASE_URL}/{endpoint}"
    print("Calling API:", url) # debug ?? URL
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()
