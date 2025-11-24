import requests

WEAVIATE_URL = ""
resp = requests.get(f"{WEAVIATE_URL}/v1/nodes?output=verbose")
resp.raise_for_status()
data = resp.json()
print(data)