from flask import Flask, request, jsonify, Response
import yt_dlp
import requests
import logging
from urllib.parse import unquote
import time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

DEVELOPER = "Adeel Baloch"
TELEGRAM = "@sigmadev0"
WHATSAPP_CHANNEL = "https://whatsapp.com/channel/0029Vb6sfZ6LikgCe1as3o21"
API_KEY = "digitalapex.me"
VERSION = "4.4"

WELCOME_JSON = { ... }   # pehle wala welcome JSON yahan paste kar do (same as before)

@app.route('/')
def home():
    return jsonify(WELCOME_JSON)

@app.route('/download')
def download_video():
    yt_url = request.args.get('url')
    provided_key = request.args.get('key')

    if not yt_url:
        error = WELCOME_JSON.copy()
        error.update({"status": "failed", "message": "URL parameter missing!"})
        return jsonify(error), 400

    if provided_key and provided_key != API_KEY:
        error = WELCOME_JSON.copy()
        error.update({"status": "failed", "message": "Invalid API Key"})
        return jsonify(error), 401

    yt_url = unquote(yt_url)

    start_time = time.time()

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'socket_timeout': 30,           # yt-dlp ke liye timeout
            'extractor_retries': 3
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(yt_url, download=False)

        processing_time = round(time.time() - start_time, 2)

        success_response = {
            "status": "success",
            "message": "Video fetched successfully!",
            "title": info.get('title', 'Unknown Video'),
            "duration": f"{info.get('duration', 0)//60}:{info.get('duration', 0)%60:02d}",
            "thumbnail": info.get('thumbnail', ''),
            "views": info.get('view_count'),
            "uploader": info.get('uploader', 'Unknown'),
            "processing_time_seconds": processing_time,
            "download_link": f"/stream?url={yt_url}",
            "creator": DEVELOPER,
            "telegram": TELEGRAM,
            "whatsapp_channel": WHATSAPP_CHANNEL,
            "api_key": API_KEY
        }

        return jsonify(success_response)

    except Exception as e:
        logging.error(str(e))
        error = WELCOME_JSON.copy()
        error.update({
            "status": "failed",
            "message": "Failed to fetch video",
            "reason": str(e)[:200] if "timeout" in str(e).lower() else "Video private, age-restricted, deleted, or network issue."
        })
        return jsonify(error), 502


@app.route('/stream')
def stream_video():
    yt_url = request.args.get('url')
    if not yt_url:
        return jsonify({"status": "failed", "message": "URL missing"}), 400

    yt_url = unquote(yt_url)

    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'merge_output_format': 'mp4',
            'socket_timeout': 30
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(yt_url, download=False)
            stream_url = info['url']
            title = info.get('title', 'youtube_video').replace('/', '_').replace('"', '')

        filename = f"{title}.mp4"

        def generate():
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            with requests.get(stream_url, headers=headers, stream=True, timeout=60) as r:   # 60 seconds timeout
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=16384):
                    if chunk:
                        yield chunk

        return Response(generate(),
                        mimetype='video/mp4',
                        headers={'Content-Disposition': f'attachment; filename="{filename}"'})

    except Exception as e:
        logging.error(str(e))
        return jsonify({"status": "failed", "message": "Download failed", "reason": "Timeout or network issue"}), 502


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
