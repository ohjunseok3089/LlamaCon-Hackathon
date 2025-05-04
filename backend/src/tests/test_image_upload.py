import requests
import json
import base64

def string_to_base64(s):
    return base64.b64encode(s.encode('utf-8')).decode('utf-8')

# Test /upload_images
url = "http://0.0.0.0:1234/upload_images"
data = {
    "images": [string_to_base64("test image data"), string_to_base64("another test")],
    "metadata": {"location": "test", "timestamp": "2024-10-27"}
}
response = requests.post(url, json=data)
print(f"/upload_images response: {response.json()}")

# Test /upload_raw
url = "http://0.0.0.0:1234/upload_raw"
raw_data = {"images": ["raw1", "raw2", "raw3"]}
response = requests.post(url, json=raw_data)
print(f"/upload_raw response: {response.json()}")