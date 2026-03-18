from flask import Flask, render_template, Response, jsonify
from detect_emotion import generate_frames, get_last_emotion

app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/video')
def video():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/emotion_data')
def emotion_data():
    """Returns the latest detected emotion + confidence scores as JSON."""
    return jsonify(get_last_emotion())


if __name__ == "__main__":
    app.run(debug=True)