from flask import Flask, request, jsonify, Response
import yt_dlp
import logging
from urllib.parse import unquote

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# API Details
DEVELOPER = "Adeel Baloch"
TELEGRAM = "@sigmadev0"
WHATSAPP_CHANNEL = "https://whatsapp.com/channel/0029Vb6sfZ6LikgCe1as3o21"
API_KEY = "digitalapex.me"
VERSION = "6.0"

def get_ydl_opts():
    return {
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android']}},
        'format': 'best[ext=mp4]/best',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36',
        },
    }

@app.route('/')
def home():
    return jsonify({
        "api_key": API_KEY,
        "creator": {"name": DEVELOPER, "telegram": TELEGRAM, "whatsapp_channel": WHATSAPP_CHANNEL},
        "status": "success",
        "version": VERSION,
        "welcome": "🎬 Welcome to YouTube Video Downloader API by Adeel Baloch"
    })

@app.route('/download')
def download_video():
    yt_url = request.args.get('url')
    key = request.args.get('key')

    if not yt_url:
        return jsonify({"status": "failed", "message": "URL missing!"}), 400
    if key != API_KEY:
        return jsonify({"status": "failed", "message": "Invalid API Key"}), 401

    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(unquote(yt_url).strip(), download=False)
            
            return jsonify({
                "status": "success",
                "title": info.get('title'),
                "duration": info.get('duration'),
                "thumbnail": info.get('thumbnail'),
                "direct_download_link": info.get('url'),
                "creator": DEVELOPER,
                "telegram": TELEGRAM
            })
    except Exception as e:
        return jsonify({"status": "failed", "message": "Failed to fetch video", "reason": str(e)}), 502

# Vercel requirement
application = app
