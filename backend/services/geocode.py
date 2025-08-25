import requests

def geocode_address(address):
    try:
        from config import config
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": address, "key": config.google_api_key}
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                location = data["results"][0]["geometry"]["location"]
                return location["lat"], location["lng"]
        return None, None
    except Exception:
        return None, None