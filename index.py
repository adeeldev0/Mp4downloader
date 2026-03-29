from flask import Flask, request, jsonify, Response
import requests
import re
import json
import logging
from urllib.parse import unquote, quote

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

DEVELOPER = "Adeel Baloch"
TELEGRAM = "@sigmadev0"
API_KEY = "digitalapex.me"
VERSION = "5.1"

# Common Headers (Android + Web mimic)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.youtube.com/",
    "Origin": "https://www.youtube.com"
}

@app.route('/')
def home():
    welcome = {
        "status": "success",
        "name": "YouTube Downloader API (Requests Only)",
        "version": VERSION,
        "creator": DEVELOPER,
        "telegram": TELEGRAM,
        "note": "Limited support - only basic public videos may work"
    }
    return jsonify(welcome)

@app.route('/download')
def download_video():
    yt_url = request.args.get('url')
    key = request.args.get('key')

    if not yt_url:
        return jsonify({"status": "failed", "message": "URL missing"}), 400
    if key and key != API_KEY:
        return jsonify({"status": "failed", "message": "Invalid API Key"}), 401

    yt_url = unquote(yt_url).strip()

    try:
        # Step 1: Get video page
        session = requests.Session()
        resp = session.get(yt_url, headers=HEADERS, timeout=20)
        resp.raise_for_status()

        html = resp.text

        # Extract ytInitialPlayerResponse
        player_match = re.search(r'ytInitialPlayerResponse\s*=\s*(\{.+?\});', html, re.DOTALL)
        if not player_match:
            # Fallback: try ytInitialData
            data_match = re.search(r'ytInitialData\s*=\s*(\{.+?\});', html, re.DOTALL)
            if data_match:
                raw_data = data_match.group(1)
            else:
                return jsonify({"status": "failed", "message": "Could not parse YouTube data"}), 502
        else:
            raw_data = player_match.group(1)

        # Clean and parse JSON
        raw_data = re.sub(r'[\x00-\x1F\x7F]', '', raw_data)  # remove control chars
        data = json.loads(raw_data)

        # Extract basic info
        video_details = data.get('videoDetails', {})
        title = video_details.get('title', 'Unknown Video')
        thumbnail = video_details.get('thumbnail', {}).get('thumbnails', [{}])[-1].get('url', '')
        duration = int(video_details.get('lengthSeconds', 0))
        duration_str = f"{duration//60}:{duration%60:02d}"

        # Streaming URL (bahut cases mein nahi milega bina signature ke)
        streaming_url = None
        formats = data.get('streamingData', {}).get('formats', []) + data.get('streamingData', {}).get('adaptiveFormats', [])
        for fmt in formats:
            if fmt.get('mimeType', '').startswith('video/mp4'):
                streaming_url = fmt.get('url')
                break

        success = {
            "status": "success",
            "message": "Video details fetched (limited)",
            "title": title,
            "duration": duration_str,
            "thumbnail": thumbnail,
            "direct_download_link": streaming_url if streaming_url else None,
            "note": "If direct link is None, streaming may not work without advanced signature decryption",
            "creator": DEVELOPER,
            "telegram": TELEGRAM
        }

        return jsonify(success)

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({
            "status": "failed",
            "message": "Failed to fetch video",
            "reason": str(e)[:300]
        }), 502


# Stream route (agar direct link mil jaye toh)
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

        return Response(generate(), mimetype='video/mp4',
                        headers={'Content-Disposition': 'attachment; filename="video.mp4"'})

    except Exception:
        return jsonify({"status": "failed", "message": "Streaming failed"}), 502


application = app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
