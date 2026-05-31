import cv2
import mediapipe as mp
import winsound
import math

# 1. Setup - Direct and Easy
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

# 2. Distance Function - Using built-in math to avoid Syntax Errors
def get_dist(p1, p2):
    return math.dist([p1.x, p1.y], [p2.x, p2.y])

# 3. EAR calculation - Simplified
def get_ear(m, eye):
    v1 = get_dist(m[eye[1]], m[eye[5]])
    v2 = get_dist(m[eye[2]], m[eye[4]])
    h = get_dist(m[eye[0]], m[eye[3]])
    return (v1 + v2) / (2.0 * h)

cap = cv2.VideoCapture(0)
L_EYE = [33, 160, 158, 133, 153, 144]
R_EYE = [362, 385, 387, 263, 373, 380]
COUNT = 0

print("System Start... Press 'q' to stop.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    
    rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
    res = face_mesh.process(rgb)
    
    if res.multi_face_landmarks:
        for face in res.multi_face_landmarks:
            m = face.landmark
            ear = (get_ear(m, L_EYE) + get_ear(m, R_EYE)) / 2.0
            
            if ear < 0.22:
                COUNT += 1
                if COUNT >= 20:
                    cv2.putText(frame, "DROWSINESS ALERT!", (50, 50), 1, 2, (0,0,255), 2)
                    winsound.Beep(1000, 100)
            else:
                COUNT = 0

    cv2.imshow('Driver Monitor', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()