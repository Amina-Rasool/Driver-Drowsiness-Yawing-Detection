import tkinter as tk
from tkinter import ttk
from threading import Thread

def setup_gui(start_callback, update_speed_callback):
    root = tk.Tk()
    root.title("Maha Driver Assistant PRO")
    root.geometry("500x600")
    root.configure(bg="#1a1a1a")

    # Header
    header = tk.Label(root, text="MAHA DRIVER ASSISTANT",
                      font=("Helvetica", 18, "bold"),
                      bg="#1a1a1a", fg="#00d2ff")
    header.pack(pady=30)

    # Status Card
    status_frame = tk.Frame(root, bg="#262626", bd=2, relief="flat")
    status_frame.pack(pady=10, padx=40, fill="x")

    lbl_status = tk.Label(status_frame, text="SYSTEM READY",
                          font=("Helvetica", 22, "bold"),
                          bg="#262626", fg="#2ecc71")
    lbl_status.pack(pady=30)

    # Stats Row
    stats_frame = tk.Frame(root, bg="#1a1a1a")
    stats_frame.pack(pady=20)

    lbl_ear = tk.Label(stats_frame, text="EAR: 0.00",
                       font=("Consolas", 14), bg="#1a1a1a", fg="#ecf0f1")
    lbl_ear.pack(side="left", padx=30)

    lbl_mar = tk.Label(stats_frame, text="MAR: 0.00",
                       font=("Consolas", 14), bg="#1a1a1a", fg="#ecf0f1")
    lbl_mar.pack(side="left", padx=30)

    # Speed Section
    tk.Label(root, text="SPEED SIMULATOR",
             font=("Helvetica", 10), bg="#1a1a1a", fg="#7f8c8d").pack()

    lbl_speed_val = tk.Label(root, text="0 km/h",
                             font=("Helvetica", 32, "bold"),
                             bg="#1a1a1a", fg="#00d2ff")
    lbl_speed_val.pack(pady=5)

    def on_slider_move(v):
        val = int(float(v))
        lbl_speed_val.config(text=f"{val} km/h")
        update_speed_callback(val)

    style = ttk.Style()
    style.configure("TScale", background="#1a1a1a")

    speed_slider = ttk.Scale(root, from_=0, to=160,
                             orient="horizontal",
                             command=on_slider_move,
                             style="TScale")
    speed_slider.pack(pady=10, padx=60, fill="x")

    # ✅ FIX: Button monitoring state track karta hai
    is_monitoring = [False]

    def on_start_click():
        if not is_monitoring[0]:               # Ek baar hi start ho
            is_monitoring[0] = True
            btn_start.config(text="MONITORING...", bg="#e67e22", state="disabled")
            lbl_status.config(text="MONITORING ACTIVE", fg="#e67e22")
            Thread(target=start_callback, daemon=True).start()  # ✅ Sirf target, koi args nahi
# Dashboard Button
    import subprocess
    btn_dash = tk.Button(root, text="VIEW DASHBOARD",
                         font=("Helvetica", 10, "bold"),
                         bg="#9b59b6", fg="white",
                         activebackground="#8e44ad",
                         width=20, height=1, bd=0, cursor="hand2",
                         command=lambda: subprocess.Popen(
                             ["python", "dashboard.py"]
                         ))
    btn_dash.pack(pady=5)
    btn_start = tk.Button(root, text="START MONITORING",
                          font=("Helvetica", 12, "bold"),
                          bg="#2ecc71", fg="white",
                          activebackground="#27ae60", activeforeground="white",
                          width=20, height=2, bd=0, cursor="hand2",
                          command=on_start_click)
    btn_start.pack(pady=40)

    # ✅ Helper functions taake main.py labels update kar sake
    def update_ear(val):
        lbl_ear.config(text=f"EAR: {val:.2f}")

    def update_mar(val):
        lbl_mar.config(text=f"MAR: {val:.2f}")

    def update_status(text, color="#2ecc71"):
        lbl_status.config(text=text, fg=color)

    root.update_ear = update_ear
    root.update_mar = update_mar
    root.update_status = update_status

    return root