"""Transcricao com timestamp por palavra (gemini-3.5-transcribe)."""
import os, json, time, mimetypes, urllib.request
from config import load_key, BASE, MODEL_ASR

def _req(url, data=None, headers=None, method=None):
    h = {"x-goog-api-key": load_key()}
    h.update(headers or {})
    return urllib.request.urlopen(
        urllib.request.Request(url, data=data, headers=h, method=method), timeout=180)

def upload(path):
    mime = mimetypes.guess_type(path)[0] or "audio/mpeg"
    blob = open(path, "rb").read()
    start = _req(f"{BASE}/upload/v1beta/files",
        data=json.dumps({"file": {"display_name": os.path.basename(path)}}).encode(),
        headers={"X-Goog-Upload-Protocol": "resumable", "X-Goog-Upload-Command": "start",
                 "X-Goog-Upload-Header-Content-Length": str(len(blob)),
                 "X-Goog-Upload-Header-Content-Type": mime,
                 "Content-Type": "application/json"})
    up = start.headers.get("X-Goog-Upload-URL")
    res = _req(up, data=blob, headers={"Content-Length": str(len(blob)),
               "X-Goog-Upload-Offset": "0", "X-Goog-Upload-Command": "upload, finalize"})
    f = json.load(res)["file"]
    while f.get("state") == "PROCESSING":
        time.sleep(1)
        f = json.load(_req(f"{BASE}/v1beta/{f['name']}"))
    return f["uri"], mime

def transcribe(path):
    uri, mime = upload(path)
    body = {"model": MODEL_ASR,
            "input": [{"type": "audio", "uri": uri, "mime_type": mime}],
            "generation_config": {"transcription_config": {
                "mode": {"type": "verbatim", "timestamp_granularities": ["word"]}}}}
    return json.load(_req(f"{BASE}/v1beta/interactions", data=json.dumps(body).encode(),
                          headers={"Content-Type": "application/json"}))
