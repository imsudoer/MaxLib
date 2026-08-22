from curl_cffi import requests
import json
import gzip

# Define the request URL
url = "https://firebaseinstallations.googleapis.com/v1/projects/max-messenger-app/installations"

# Define the request headers
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Content-Encoding": "gzip",
    "Cache-Control": "no-cache",
    "X-Android-Package": "ru.oneme.app",
    "x-firebase-client": "H4sIAAAAAAAAAKtWykhNLCpJSk0sKVayio7VUSpLLSrOzM9TslIyUqoFAFyivEQfAAAA",
    "X-Android-Cert": "A1:B2:C3:D4:E5:F6:G7:H8:I9:J0:K1:L2:M3:N4:O5:P6:Q7:R8:S9:T0",
    "x-goog-api-key": "AIzaSyABuDYeeDXIOrKTXLkUj30Ii143ofPe63Q",
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; Redmi Note 10S Build/TQ3A.230805.001)",
    "Host": "firebaseinstallations.googleapis.com",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip"
}

# Define the request body
body = {
    "fid": "fNoH2117T5-MxB9hnNEW41",
    "appId": "1:659634599081:android:9605285443b661167225b8",
    "authVersion": "FIS_v2",
    "sdkVersion": "a:18.0.0"
}

# Convert the body to JSON and compress it with gzip
json_body = json.dumps(body).encode('utf-8')
compressed_body = gzip.compress(json_body)

# Make the POST request using curl_cffi
response = requests.post(
    url,
    headers=headers,
    data=compressed_body,
    impersonate="chrome"  # Emulates a Chrome browser; adjust if needed
)

# Check the response
print("Status Code:", response.status_code)
print("Response Headers:", response.headers)
print("Response Body:", response.text)