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
VERSION = "4.5"   # version badha di

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
            "example": "https://your-app.vercel.app/download?url=https://youtu.be/FvchYesgr6U&key=digitalapex.me",
            "method": "GET",
            "parameters": {"key": "API Key (digitalapex.me)", "url": "YouTube video URL"},
            "url": "/download"
        }
    },
    "features": ["✅ MP4 Video Only", "✅ High Quality (up to 1080p+)", "✅ No Watermark", "✅ Fast & Optimized"],
    "name": "YouTube Video Downloader API",
    "rate_limit": "Unlimited",
    "status": "success",
    "version": VERSION,
    "welcome": "🎬 Welcome to YouTube Video Downloader API by Adeel Baloch"
}

@app.route('/')
def home():
    return jsonify(WELCOME)

# Common yt-dlp options (2026 optimized)
def get_ydl_opts():
    return {
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web_embedded', 'ios'],  # android best for servers
            }
        },
        'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

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
        ydl_opts = get_ydl_opts()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(yt_url, download=False)

        duration = info.get('duration', 0)
        success = {
            "status": "success",
            "message": "Video fetched successfully!",
            "title": info.get('title', 'Unknown Video'),
            "duration": f"{duration//60}:{duration%60:02d}",
            "thumbnail": info.get('thumbnail', ''),
            "download_link": f"/stream?url={yt_url}",
            "creator": DEVELOPER,
            "telegram": TELEGRAM,
            "whatsapp_channel": WHATSAPP_CHANNEL,
            "views": info.get('view_count'),
            "uploader": info.get('uploader')
        }
        return jsonify(success)

    except Exception as e:
        logging.error(f"Download error for {yt_url}: {str(e)}")
        return jsonify({
            "status": "failed", 
            "message": "Failed to fetch video",
            "reason": str(e)[:300]   # asli error dikhega
        }), 502


@app.route('/stream')
def stream_video():
    yt_url = request.args.get('url')
    if not yt_url:
        return jsonify({"status": "failed", "message": "URL missing"}), 400

    yt_url = unquote(yt_url)

    try:
        ydl_opts = get_ydl_opts()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(yt_url, download=False)
            stream_url = info.get('url')
            
            if not stream_url:
                raise Exception("No direct stream URL found")

            title = info.get('title', 'video').replace('/', '_').replace('"', '').replace("'", "")[:100]
        
        filename = f"{title}.mp4"

        def generate():
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            with requests.get(stream_url, headers=headers, stream=True, timeout=120) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=32768):  # larger chunk for better speed
                    if chunk:
                        yield chunk

        return Response(
            generate(), 
            mimetype='video/mp4',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': info.get('filesize') or info.get('filesize_approx') or ''
            }
        )

    except Exception as e:
        logging.error(f"Stream error for {yt_url}: {str(e)}")
        return jsonify({
            "status": "failed", 
            "message": "Download failed",
            "reason": str(e)[:300]
        }), 502


# Vercel ke liye
application = app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
