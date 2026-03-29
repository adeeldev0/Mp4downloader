from flask import Flask, request, jsonify, Response
import yt_dlp
import requests

app = Flask(__name__)

# Sabse strong user agent jo YouTube ko "Mobile App" lagta hai
USER_AGENT = "Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"

def get_ydl_opts():
    return {
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,  # Location restriction hatane ke liye
        'extractor_args': {
            'youtube': {
                'player_client': ['android'], # Android client best hai
                'player_skip': ['webpage'],
            }
        },
        'format': 'best[ext=mp4]/best',
        'http_headers': {
            'User-Agent': USER_AGENT,
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/', # Referer change kiya
        }
    }

@app.route('/download')
def download_video():
    yt_url = request.args.get('url')
    if not yt_url: return jsonify({"status": "failed", "message": "No URL"}), 400

    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            # Info nikalne ka tareeka
            info = ydl.extract_info(yt_url, download=False)
            return jsonify({
                "status": "success",
                "title": info.get('title'),
                "url": info.get('url') # Yeh direct link hai
            })
    except Exception as e:
        return jsonify({"status": "failed", "reason": str(e)}), 502

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
