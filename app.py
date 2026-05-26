from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import subprocess
import uuid

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"status": "ClipForge Backend is running!"})

@app.route('/api/video-info', methods=['POST'])
def get_video_info():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "title": info.get('title'),
                "duration": info.get('duration'),
                "thumbnail": info.get('thumbnail'),
                "uploader": info.get('uploader'),
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clip', methods=['POST'])
def clip_video():
    data = request.get_json()
    url = data.get('url')
    start = data.get('start', 0)
    end = data.get('end', 30)

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        clip_id = str(uuid.uuid4())[:8]
        output_path = f"/tmp/{clip_id}.mp4"

        ydl_opts = {
            'quiet': True,
            'format': 'mp4',
            'outtmpl': f'/tmp/{clip_id}_full.mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        subprocess.run([
            'ffmpeg', '-i', f'/tmp/{clip_id}_full.mp4',
            '-ss', str(start), '-to', str(end),
            '-c', 'copy', output_path, '-y'
        ], check=True)

        return send_file(output_path, as_attachment=True, download_name='clip.mp4')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)