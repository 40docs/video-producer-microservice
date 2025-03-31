from flask import Flask, request, jsonify
from ffmpeg_service import produce_video

app = Flask(__name__)

@app.route("/create-video", methods=["POST"])
def create_video():
    data = request.get_json()
    output_name = data.get("output_name", "final_output")

    try:
        path = produce_video(output_name)
        return jsonify({"status": "ok", "video": path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return {"status": "ok"}
