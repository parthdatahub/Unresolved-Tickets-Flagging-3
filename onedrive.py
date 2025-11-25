#pip install msal requests

import os, requests
from msal import ConfidentialClientApplication

TENANT_ID = "YOUR_TENANT_ID"
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
DRIVE_ID = "YOUR_DRIVE_ID"          # target drive id (e.g., SharePoint/OneDrive drive id)
DEST_PATH = "Folder/processed_incidents.csv"  # path inside drive
FILE_PATH = "processed_incidents.csv"
SCOPE = ["https://graph.microsoft.com/.default"]
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}"

app = ConfidentialClientApplication(CLIENT_ID, authority=TOKEN_URL, client_credential=CLIENT_SECRET)
token = app.acquire_token_for_client(scopes=SCOPE)
if "access_token" not in token:
    raise SystemExit("Failed to acquire access token: " + str(token))

headers = {"Authorization": "Bearer " + token["access_token"]}
filesize = os.path.getsize(FILE_PATH)

if filesize <= 4 * 1024 * 1024:
    url = f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/root:/{DEST_PATH}:/content"
    with open(FILE_PATH, "rb") as f:
        r = requests.put(url, headers=headers, data=f)
    r.raise_for_status()
    print("Uploaded (simple upload). File metadata:")
    print(r.json().get("webUrl") or r.json())
else:
    # create upload session
    session_url = f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/root:/{DEST_PATH}:/createUploadSession"
    r = requests.post(session_url, headers=headers, json={})
    r.raise_for_status()
    upload_url = r.json()["uploadUrl"]
    chunk_size = 3276800  # ~3.2MB
    with open(FILE_PATH, "rb") as f:
        start = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            end = start + len(chunk) - 1
            chunk_headers = {
                "Authorization": "Bearer " + token["access_token"],
                "Content-Length": str(len(chunk)),
                "Content-Range": f"bytes {start}-{end}/{filesize}"
            }
            resp = requests.put(upload_url, headers=chunk_headers, data=chunk)
            if resp.status_code not in (200, 201, 202):
                raise SystemExit("Chunk upload failed: " + resp.text)
            start = end + 1
    print("Uploaded (resumable). Final response:")
    print(resp.json().get("webUrl") or resp.json())
