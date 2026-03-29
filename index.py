from flask import Flask, request, jsonify, Response
import yt_dlp
import requests
import logging
from urllib.parse import unquote

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

DEVELOPER = "Adeel Baloch"
TELEGRAM = "@sigmadev0"
WHATSAPP_CHANNEL = "https://whatsapp.com/channel/0029Vb6sfZ6LikgCe1as3o21"
API_KEY = "digitalapex.me"
VERSION = "4.4"

WELCOME = {
    "api_key": API_KEY,
    "creator": {
        "name": DEVELOPER,
        "telegram": TELEGRAM,
        "whatsapp_channel": WHATSAPP_CHANNEL,
        "website": "digitalapex.me"
    },
    "description": "Download YouTube videos as high quality MP4 video only",
    "endpoints": {
        "download": {
            "description": "Fetch video details & get download link",
            "example": "https://mp4downloader-kaba.vercel.app/download?url=https://youtu.be/FvchYesgr6U&key=digitalapex.me",
            "method": "GET",
            "parameters": {"key": "API Key (digitalapex.me)", "url": "YouTube video URL"},
            "url": "/download"
        }
    },
    "features": ["✅ MP4 Video Only", "✅ High Quality", "✅ No Watermark", "✅ Fast Download"],
    "name": "YouTube Video Downloader API",
    "rate_limit": "Unlimited",
    "status": "success",
    "version": VERSION,
    "welcome": "🎬 Welcome to YouTube Video Downloader API by Adeel Baloch"
}

@app.route('/')
def home():
    return jsonify(WELCOME)

@app.route('/download')
def download_video():
    yt_url = request.args.get('url')
    key = request.args.get('key')

    if not yt_url:
        return jsonify({"status": "failed", "message": "URL missing!"}), 400

    if key and key != API_KEY:
        return jsonify({"status": "failed", "message": "Invalid API Key"}), 401

    yt_url = unquote(yt_url)

    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(yt_url, download=False)

        success = {
            "status": "success",
            "message": "Video fetched successfully!",
            "title": info.get('title', 'Unknown Video'),
            "duration": f"{info.get('duration', 0)//60}:{info.get('duration', 0)%60:02d}",
            "thumbnail": info.get('thumbnail', ''),
            "download_link": f"/stream?url={yt_url}",
            "creator": DEVELOPER,
            "telegram": TELEGRAM,
            "whatsapp_channel": WHATSAPP_CHANNEL
        }
        return jsonify(success)

    except Exception:
        return jsonify({"status": "failed", "message": "Failed to fetch video", "reason": "Video private, age-restricted or network issue"}), 502


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
            'merge_output_format': 'mp4'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(yt_url, download=False)
            stream_url = info['url']
            title = info.get('title', 'video').replace('/', '_').replace('"', '')

        filename = f"{title}.mp4"

        def generate():
            headers = {'User-Agent': 'Mozilla/5.0'}
            with requests.get(stream_url, headers=headers, stream=True, timeout=60) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=16384):
                    if chunk:
                        yield chunk

        return Response(generate(), 
                        mimetype='video/mp4',
                        headers={'Content-Disposition': f'attachment; filename="{filename}"'})

    except Exception:
        return jsonify({"status": "failed", "message": "Download failed"}), 502


# Vercel ke liye zaroori
application = app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
