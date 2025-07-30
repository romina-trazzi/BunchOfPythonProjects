import requests

def get_exchange(base, target):
    url = f"https://api.frankfurter.app/latest?from={base}&to={target}"
    response = requests.get(url)
    data = response.json()
    return data["rates"].get(target, "N/A")
