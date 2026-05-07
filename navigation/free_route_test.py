import requests

def get_route(origin, destination):

    url = "https://router.project-osrm.org/route/v1/driving/"

    full_url = f"{url}{origin};{destination}"

    params = {
        "overview": "false",
        "steps": "true"
    }

    response = requests.get(full_url, params=params)

    return response.json()


# Example (longitude,latitude format!)
result = get_route(
    "126.9780,37.5665",  # Seoul
    "127.0276,37.4979"   # Gangnam
)

print(result)