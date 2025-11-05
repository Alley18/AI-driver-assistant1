import requests

embedded_ip = "172.19.14.245"
url = f'http://{embedded_ip}:5000/run-script'  # Update IP and endpoint as needed
response = requests.post(url)
print(response.json())
