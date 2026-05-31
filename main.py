from app_gui import setup_gui
import cv2
import mediapipe as mp
from scipy.spatial import distance
import numpy as np
from threading import Thread
import pyttsx3
import winsound
import csv
from datetime import datetime
import time

# -------- Speech Engine --------
engine = pyttsx3.init()
engine.setProperty('rate', 150)
speech_busy = False

def speak_alert(message):
    global speech_busy
    if speech_busy:
        return
    speech_busy = True
    try:
        engine.say(message)
        engine.runAndWait()
    except:
        pass
    finally:
        speech_busy = False

# -------- Mediapipe Setup --------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    refine_landmarks=True,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Landmarks
LEFT_EYE  = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
MOUTH     = [13, 14, 78, 308, 81, 178]

# Thresholds
EYE_THRESHOLD   = 0.25
MOUTH_THRESHOLD = 0.50
SPEED_LIMIT     = 100
ALERT_LIMIT     = 15
LOG_FILE        = "driver_activity_logs.csv"

# -------- Global States --------
CLOSED_FRAMES = 0

# ✅ FIX 1: Har alert ka alag cooldown
COOLDOWNS = {
    "drowsy": 4.0,
    "yawn":   5.0,
    "speed":  3.0,
    "score":  6.0,
}
last_alert_time = {
    "drowsy": 0.0,
    "yawn":   0.0,
    "speed":  0.0,
    "score":  0.0,
}

current_speed = 0

# -------- Blink Counter globals --------
blink_count    = 0
eye_was_closed = False
blink_times    = []
BLINK_WINDOW   = 60.0

# -------- Drowsiness Score globals --------
score              = 0
SCORE_EAR_WEIGHT   = 50
SCORE_MAR_WEIGHT   = 25
SCORE_BLINK_WEIGHT = 25

# -------- File Setup --------
try:
    with open(LOG_FILE, mode='x', newline='') as f:
        csv.writer(f).writerow(["Date", "Time", "Event", "EAR", "MAR", "Speed"])
except FileExistsError:
    pass

def log_event(event, ear, mar, speed):
    now = datetime.now()
    with open(LOG_FILE, mode='a', newline='') as f:
        csv.writer(f).writerow([
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S"),
            event, round(ear, 2), round(mar, 2), speed
        ])

# ✅ FIX 1: can_alert ab COOLDOWNS use karta hai
def can_alert(key):
    now = datetime.now().timestamp()
    if now - last_alert_time[key] >= COOLDOWNS[key]:
        last_alert_time[key] = now
        return True
    return False

def calculate_ratio(points, landmarks):
    v1 = distance.euclidean(landmarks[points[1]], landmarks[points[5]])
    v2 = distance.euclidean(landmarks[points[2]], landmarks[points[4]])
    h  = distance.euclidean(landmarks[points[0]], landmarks[points[3]])
    return (v1 + v2) / (2.0 * h)

# -------- Blink Counter --------
def update_blink(ear):
    global blink_count, eye_was_closed, blink_times
    now = time.time()
    if ear < EYE_THRESHOLD:
        eye_was_closed = True
    else:
        if eye_was_closed:
            blink_count += 1
            blink_times.append(now)
        eye_was_closed = False
    blink_times = [t for t in blink_times if now - t <= BLINK_WINDOW]
    return len(blink_times)

# -------- Drowsiness Score --------
def calculate_score(ear, mar, blinks_per_min):
    ear_score = 0
    if ear < EYE_THRESHOLD:
        ear_score = min(100, int((EYE_THRESHOLD - ear) / EYE_THRESHOLD * 100))
    mar_score = 0
    if mar > MOUTH_THRESHOLD:
        mar_score = min(100, int((mar - MOUTH_THRESHOLD) / MOUTH_THRESHOLD * 100))
    blink_score = 0
    if blinks_per_min < 10:
        blink_score = min(100, int((10 - blinks_per_min) * 10))
    elif blinks_per_min > 30:
        blink_score = min(100, int((blinks_per_min - 30) * 3))
    total = (
        ear_score   * SCORE_EAR_WEIGHT   // 100 +
        mar_score   * SCORE_MAR_WEIGHT   // 100 +
        blink_score * SCORE_BLINK_WEIGHT // 100
    )
    return min(100, total)

def get_score_color(score):
    if score < 30:   return (0, 255, 0)
    elif score < 60: return (0, 165, 255)
    else:            return (0, 0, 255)

def get_score_label(score):
    if score < 30:   return "ALERT"
    elif score < 60: return "TIRED"
    else:            return "DANGER"

# ✅ FIX 2: Teenon beep alag alag functions mein
def speed_beep():
    for _ in range(3):
        winsound.Beep(2000, 300)   # High pitch, 3 baar

def drowsy_beep():
    winsound.Beep(600, 1000)       # Low pitch, lamba

def yawn_beep():
    winsound.Beep(800, 600)        # Medium pitch

# -------- Main Monitoring Loop --------
def start_monitoring():
    global CLOSED_FRAMES, current_speed, score

    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame   = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        rgb.flags.writeable = False
        results = face_mesh.process(rgb)
        rgb.flags.writeable = True

        ear, mar = 0.0, 0.0

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                landmarks = [
                    (int(lm.x * w), int(lm.y * h))
                    for lm in face_landmarks.landmark
                ]

                leftEAR  = calculate_ratio(LEFT_EYE,  landmarks)
                rightEAR = calculate_ratio(RIGHT_EYE, landmarks)
                ear = (leftEAR + rightEAR) / 2.0
                mar = calculate_ratio(MOUTH, landmarks)

                bpm     = update_blink(ear)
                score   = calculate_score(ear, mar, bpm)
                s_color = get_score_color(score)
                s_label = get_score_label(score)

                # Stats Line 1
                cv2.putText(frame,
                    f"EAR:{round(ear,2)}  MAR:{round(mar,2)}  Speed:{current_speed}km/h",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                # Stats Line 2
                cv2.putText(frame,
                    f"Blinks/min:{bpm}  Score:{score}  [{s_label}]",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, s_color, 2)

                # Score bar
                bar_x, bar_y, bar_w, bar_h = 10, 75, 200, 12
                cv2.rectangle(frame,
                    (bar_x, bar_y),
                    (bar_x + bar_w, bar_y + bar_h),
                    (50, 50, 50), -1)
                cv2.rectangle(frame,
                    (bar_x, bar_y),
                    (bar_x + int(bar_w * score / 100), bar_y + bar_h),
                    s_color, -1)

                # ── Speed ─────────────────────────────────────────
                if current_speed > SPEED_LIMIT:
                    cv2.putText(frame, "OVER SPEEDING!",
                        (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                    if can_alert("speed"):
                        log_event("OverSpeed", ear, mar, current_speed)
                        Thread(target=speed_beep, daemon=True).start()
                        Thread(target=speak_alert,
                               args=("Slow down! You are over speeding.",),
                               daemon=True).start()

                # ── Drowsiness ────────────────────────────────────
                if ear < EYE_THRESHOLD:
                    CLOSED_FRAMES += 1
                    if CLOSED_FRAMES > ALERT_LIMIT:
                        cv2.putText(frame, "DROWSINESS ALERT!",
                            (100, 140), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                        if can_alert("drowsy"):
                            log_event("Drowsy", ear, mar, current_speed)
                            # ✅ FIX 3: Beep alag thread mein
                            Thread(target=drowsy_beep, daemon=True).start()
                            Thread(target=speak_alert,
                                   args=("Warning! You are feeling drowsy.",),
                                   daemon=True).start()
                else:
                    CLOSED_FRAMES = 0

                # ── Yawning ───────────────────────────────────────
                if mar > MOUTH_THRESHOLD:
                    cv2.putText(frame, "YAWNING DETECTED!",
                        (100, 180), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 3)
                    if can_alert("yawn"):
                        log_event("Yawning", ear, mar, current_speed)
                        # ✅ FIX 3: Yawning ka apna beep
                        Thread(target=yawn_beep, daemon=True).start()
                        Thread(target=speak_alert,
                               args=("Please take a break, you are yawning.",),
                               daemon=True).start()

                # ── High Score Alert ──────────────────────────────
                if score >= 60:
                    cv2.putText(frame, "HIGH DROWSINESS SCORE!",
                        (100, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    if can_alert("score"):
                        log_event("HighScore", ear, mar, current_speed)
                        Thread(target=speak_alert,
                               args=("Danger! Your drowsiness level is very high. Please stop and rest.",),
                               daemon=True).start()

        cv2.imshow("Driver Monitoring System", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

# -------- GUI wiring --------
def update_speed(val):
    global current_speed
    current_speed = int(val)

if __name__ == "__main__":

    def update_current_speed(val):
        global current_speed
        current_speed = int(val)

    def run_monitor():
        Thread(target=start_monitoring, daemon=True).start()

    app = setup_gui(run_monitor, update_current_speed)
    app.mainloop()