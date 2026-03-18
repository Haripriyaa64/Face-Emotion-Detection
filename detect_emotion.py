import cv2
import numpy as np
from tensorflow.keras.models import load_model

# ── Load model ────────────────────────────────────────────────
model = load_model("model/emotion_model.hdf5", compile=False)

# Auto-detect input size from the model itself (handles 48x48 AND 64x64)
IMG_SIZE = model.input_shape[1]   # e.g. 64 if shape is (None,64,64,1)
print(f"[NeuralFace] Model input size detected: {IMG_SIZE}x{IMG_SIZE}")

# Warm up — eliminates the slow first-prediction TF graph-build delay
model.predict(np.zeros((1, IMG_SIZE, IMG_SIZE, 1)), verbose=0)
print("[NeuralFace] Model warmed up — ready!")

# ── Face detector ─────────────────────────────────────────────
face_cascade = cv2.CascadeClassifier(
    "haarcascade/haarcascade_frontalface_default.xml"
)

# ── Emotion metadata ──────────────────────────────────────────
EMOTION_LABELS = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]

EMOTION_COLORS = {
    "Happy":    (0,   220,  50),
    "Sad":      (230, 100,  40),
    "Angry":    (30,  30,  255),
    "Surprise": (0,   200, 255),
    "Fear":     (200,  50, 180),
    "Disgust":  (50,  200,  80),
    "Neutral":  (200, 200, 200),
}

# ── Shared state ──────────────────────────────────────────────
_last_result = {
    "emotion": "Neutral",
    "scores":  {e: 0.0 for e in EMOTION_LABELS},
}

# Predict every N frames — model.predict is the slow part.
# Cached result redraws on skipped frames so the box never flickers.
PREDICT_EVERY_N_FRAMES = 2
_frame_count  = 0
_cached_pred  = None   # (emotion, confidence, prediction_array, color)
_cached_faces = []     # face rects from last detection pass


def get_last_emotion():
    return dict(_last_result)


# ── Camera setup ──────────────────────────────────────────────
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
camera.set(cv2.CAP_PROP_FPS, 30)


# ── Drawing helpers ───────────────────────────────────────────
def draw_label_above(frame, text, x, y, color, font_scale=0.75, thickness=2):
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    pad_x, pad_y = 10, 6
    box_y1 = max(0, y - th - pad_y * 2 - baseline)
    cv2.rectangle(frame, (x, box_y1), (x + tw + pad_x * 2, y), color, -1)
    cv2.putText(frame, text, (x + pad_x, y - pad_y),
                font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)


def draw_face_box(frame, x, y, w, h, color, thickness=2):
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)


def draw_confidence_bar(frame, x, y, w, h, confidence, color):
    bar_y1 = y + h + 4
    bar_y2 = bar_y1 + 5
    cv2.rectangle(frame, (x, bar_y1), (x + w,              bar_y2), (40, 40, 40), -1)
    cv2.rectangle(frame, (x, bar_y1), (x + int(w * confidence), bar_y2), color,  -1)


# ── Main frame generator ──────────────────────────────────────
def generate_frames():
    global _last_result, _frame_count, _cached_pred, _cached_faces

    while True:
        success, frame = camera.read()
        if not success:
            break

        _frame_count += 1
        run_predict = (_frame_count % PREDICT_EVERY_N_FRAMES == 0)

        if run_predict:
            gray       = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Halve resolution before cascade — ~4x faster detection
            small_gray = cv2.resize(gray, (0, 0), fx=0.5, fy=0.5)

            faces_small = face_cascade.detectMultiScale(
                small_gray,
                scaleFactor=1.1,
                minNeighbors=3,
                minSize=(20, 20),
            )

            # Scale coords back to full frame size
            if len(faces_small) > 0:
                _cached_faces = [(x*2, y*2, w*2, h*2) for (x, y, w, h) in faces_small]
            else:
                _cached_faces = []

            if len(_cached_faces) > 0:
                x, y, w, h = _cached_faces[0]

                # Clamp to frame bounds to avoid slice errors
                x, y = max(0, x), max(0, y)
                w = min(w, frame.shape[1] - x)
                h = min(h, frame.shape[0] - y)

                face_roi = gray[y:y+h, x:x+w]
                # Use IMG_SIZE auto-detected from model (64 or 48)
                face_roi = cv2.resize(face_roi, (IMG_SIZE, IMG_SIZE))
                face_roi = face_roi.astype("float32") / 255.0
                face_roi = face_roi.reshape(1, IMG_SIZE, IMG_SIZE, 1)

                prediction    = model.predict(face_roi, verbose=0)[0]
                emotion_index = int(np.argmax(prediction))
                emotion       = EMOTION_LABELS[emotion_index]
                confidence    = float(prediction[emotion_index])
                color         = EMOTION_COLORS.get(emotion, (0, 255, 0))

                _cached_pred = (emotion, confidence, prediction, color)
                _last_result = {
                    "emotion": emotion,
                    "scores":  {EMOTION_LABELS[i]: float(prediction[i])
                                for i in range(len(EMOTION_LABELS))},
                }
            else:
                _cached_pred = None

        # Draw on every frame using cached data
        if _cached_pred and len(_cached_faces) > 0:
            emotion, confidence, prediction, color = _cached_pred
            for (x, y, w, h) in _cached_faces:
                draw_face_box(frame, x, y, w, h, color)
                draw_label_above(frame, f"{emotion}  {int(confidence*100)}%", x, y, color)
                draw_confidence_bar(frame, x, y, w, h, confidence, color)

        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + buffer.tobytes() +
            b'\r\n'
        )