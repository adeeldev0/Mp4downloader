from flask import Flask, request, jsonify
import yt_dlp
import logging

app = Flask(__name__)

# Constants
API_KEY = "digitalapex.me"
DEVELOPER = "Adeel Baloch"
VERSION = "6.0"

@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "version": VERSION,
        "developer": DEVELOPER,
        "message": "YouTube Video Downloader API is active."
    })

@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    key = request.args.get('key')

    # 1. Validation
    if not url:
        return jsonify({"status": "error", "message": "Missing URL parameter"}), 400
    if key != API_KEY:
        return jsonify({"status": "error", "message": "Invalid API Key"}), 403

    # 2. Options (Minimal for speed)
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best[ext=mp4]',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # 3. Professional JSON Response
            response_data = {
                "status": "success",
                "code": 200,
                "data": {
                    "title": info.get('title'),
                    "duration": info.get('duration'),
                    "thumbnail": info.get('thumbnail'),
                    "channel": info.get('uploader'),
                    "direct_url": info.get('url')
                },
                "meta": {
                    "version": VERSION,
                    "developer": DEVELOPER,
                    "website": "digitalapex.me"
                }
            }
            return jsonify(response_data)

    except Exception as e:
        return jsonify({
            "status": "error",
            "code": 500,
            "message": "Failed to fetch video",
            "details": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True)
