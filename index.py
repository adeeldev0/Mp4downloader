from flask import Flask, request, jsonify, Response
import requests
import re
import json
import logging
from urllib.parse import unquote

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

DEVELOPER = "Adeel Baloch"
TELEGRAM = "@sigmadev0"
WHATSAPP_CHANNEL = "https://whatsapp.com/channel/0029Vb6sfZ6LikgCe1as3o21"
API_KEY = "digitalapex.me"
VERSION = "5.3"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.youtube.com/",
    "Origin": "https://www.youtube.com"
}

@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "name": "YouTube Video Downloader API",
        "version": VERSION,
        "creator": DEVELOPER,
        "telegram": TELEGRAM,
        "whatsapp_channel": WHATSAPP_CHANNEL
    })

def extract_video_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.route('/download')
def download_video():
    yt_url = request.args.get('url')
    key = request.args.get('key')

    if not yt_url:
        return jsonify({"status": "failed", "message": "URL missing!"}), 400
    if key and key != API_KEY:
        return jsonify({"status": "failed", "message": "Invalid API Key"}), 401

    yt_url = unquote(yt_url).strip()
    video_id = extract_video_id(yt_url)
    if not video_id:
        return jsonify({"status": "failed", "message": "Invalid YouTube URL"}), 400

    try:
        # Step 1: Page se INNERTUBE_API_KEY nikaalo
        page_resp = requests.get(f"https://www.youtube.com/watch?v={video_id}", headers=HEADERS, timeout=20)
        page_resp.raise_for_status()

        api_key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', page_resp.text)
        innertube_key = api_key_match.group(1) if api_key_match else None

        if not innertube_key:
            return jsonify({"status": "failed", "message": "Could not extract API key"}), 502

        # Step 2: Improved Innertube Player API (2026 fixed payload)
        payload = {
            "context": {
                "client": {
                    "clientName": "ANDROID",
                    "clientVersion": "19.45.36",          # stable version 2026 mein
                    "androidSdkVersion": 34
                }
            },
            "videoId": video_id,
            "contentCheckOk": True,
            "racyCheckOk": True,
            "playbackContext": {
                "contentPlaybackContext": {
                    "html5Preference": "HTML5_PREF_WANTS"
                }
            }
        }

        api_url = f"https://www.youtube.com/youtubei/v1/player?key={innertube_key}"
        resp = requests.post(api_url, json=payload, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        # Video details (agar na mile toh fallback)
        video_details = data.get("videoDetails", {})
        title = video_details.get("title") or "Unknown Video"
        duration_sec = int(video_details.get("lengthSeconds") or 0)
        duration_str = f"{duration_sec//60}:{duration_sec%60:02d}"
        
        # Thumbnail
        thumbnails = video_details.get("thumbnail", {}).get("thumbnails", [])
        thumbnail = thumbnails[-1].get("url") if thumbnails else ""

        # Direct MP4 link (formats + adaptiveFormats)
        streaming_data = data.get("streamingData", {})
        direct_link = None
        for fmt in streaming_data.get("formats", []) + streaming_data.get("adaptiveFormats", []):
            if fmt.get("mimeType", "").startswith("video/mp4") and fmt.get("url"):
                direct_link = fmt.get("url")
                break

        success = {
            "status": "success",
            "message": "Video fetched successfully!",
            "title": title,
            "duration": duration_str,
            "thumbnail": thumbnail,
            "direct_download_link": direct_link,
            "download_link": f"/stream?url={direct_link}" if direct_link else None,
            "creator": DEVELOPER,
            "telegram": TELEGRAM,
            "whatsapp_channel": WHATSAPP_CHANNEL
        }
        return jsonify(success)

    except Exception as e:
        logging.error(f"Error for {yt_url}: {str(e)}")
        return jsonify({
            "status": "failed",
            "message": "Failed to fetch video",
            "reason": str(e)[:300]
        }), 502


@app.route('/stream')
def stream_video():
    direct_url = request.args.get('url')
    if not direct_url:
        return jsonify({"status": "failed", "message": "Direct URL missing"}), 400

    try:
        def generate():
            h = {'User-Agent': HEADERS['User-Agent']}
            with requests.get(direct_url, headers=h, stream=True, timeout=90) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        yield chunk

        return Response(generate(),
                        mimetype='video/mp4',
                        headers={'Content-Disposition': 'attachment; filename="video.mp4"'})

    except Exception as e:
        return jsonify({"status": "failed", "message": "Streaming failed", "reason": str(e)[:200]}), 502


application = app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
