import tkinter as tk
from tkinter import ttk
import csv
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use("TkAgg")

LOG_FILE = "driver_activity_logs.csv"

def load_data():
    rows = [] 
    try:
        with open(LOG_FILE, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        pass
    return rows

def build_dashboard():
    data = load_data()

    root = tk.Tk()
    root.title("Maha Driver Assistant — Dashboard")
    root.geometry("900x650")
    root.configure(bg="#1a1a1a")

    # ── Title ──
    tk.Label(root, text="DRIVER ACTIVITY DASHBOARD",
             font=("Helvetica", 16, "bold"),
             bg="#1a1a1a", fg="#00d2ff").pack(pady=10)

    if not data:
        tk.Label(root, text="Koi data nahi mila — pehle monitoring chalao!",
                 font=("Helvetica", 12), bg="#1a1a1a", fg="#e74c3c").pack(pady=40)
        root.mainloop()
        return

    # ── Stats cards ──
    events = [row["Event"] for row in data]
    counts = Counter(events)

    cards_frame = tk.Frame(root, bg="#1a1a1a")
    cards_frame.pack(pady=10)

    card_data = [
        ("Drowsy",    counts.get("Drowsy",    0), "#e74c3c"),
        ("Yawning",   counts.get("Yawning",   0), "#e67e22"),
        ("OverSpeed", counts.get("OverSpeed", 0), "#9b59b6"),
        ("Total",     len(data),                  "#2ecc71"),
    ]

    for label, val, color in card_data:
        f = tk.Frame(cards_frame, bg="#262626", width=160, height=80)
        f.pack(side="left", padx=10)
        f.pack_propagate(False)
        tk.Label(f, text=str(val), font=("Helvetica", 28, "bold"),
                 bg="#262626", fg=color).pack(pady=5)
        tk.Label(f, text=label, font=("Helvetica", 10),
                 bg="#262626", fg="#aaaaaa").pack()

    # ── Charts ──
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    fig.patch.set_facecolor("#1a1a1a")

    # Chart 1 — Event bar chart
    event_labels = list(counts.keys())
    event_vals   = list(counts.values())
    colors = ["#e74c3c", "#e67e22", "#9b59b6", "#3498db", "#2ecc71"]
    ax1.bar(event_labels, event_vals,
            color=colors[:len(event_labels)], edgecolor="none")
    ax1.set_xticks(range(len(event_labels)))
    ax1.set_xticklabels(event_labels, rotation=45, ha='right', fontsize=8)
    ax1.set_facecolor("#262626")
    ax1.set_title("Events Count", color="white", fontsize=11)
    ax1.tick_params(colors="white")
    ax1.spines[:].set_color("#444444")
    for spine in ax1.spines.values():
        spine.set_color("#444444")

    # Chart 2 — Events over time (by hour)
    hour_events = Counter()
    for row in data:
        try:
            t = datetime.strptime(row["Time"], "%H:%M:%S")
            hour_events[t.hour] += 1
        except:
            pass

    hours = sorted(hour_events.keys())
    vals  = [hour_events[h] for h in hours]
    ax2.plot([f"{h}:00" for h in hours], vals,
             color="#00d2ff", linewidth=2, marker="o", markersize=5)
    ax2.fill_between(range(len(hours)), vals, alpha=0.2, color="#00d2ff")
    ax2.set_facecolor("#262626")
    ax2.set_title("Events by Hour", color="white", fontsize=11)
    ax2.tick_params(colors="white")
    ax2.set_xticks(range(len(hours)))
    ax2.set_xticklabels([f"{h}:00" for h in hours],
                        rotation=45, color="white", fontsize=8)
    for spine in ax2.spines.values():
        spine.set_color("#444444")
    plt.subplots_adjust(bottom=0.25)
    plt.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(pady=10, padx=20, fill="both")

    # ── Recent events table ──
    tk.Label(root, text="Recent Events",
             font=("Helvetica", 11, "bold"),
             bg="#1a1a1a", fg="#00d2ff").pack(pady=(10, 2))

    table_frame = tk.Frame(root, bg="#1a1a1a")
    table_frame.pack(padx=20, fill="x")

    cols = ["Date", "Time", "Event", "EAR", "MAR", "Speed"]
    tree = ttk.Treeview(table_frame, columns=cols,
                        show="headings", height=5)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview",
                    background="#262626",
                    foreground="white",
                    fieldbackground="#262626",
                    rowheight=25)
    style.configure("Treeview.Heading",
                    background="#333333",
                    foreground="#00d2ff",
                    font=("Helvetica", 9, "bold"))

    for col in cols:  
        tree.heading(col, text=col)
        tree.column(col, width=120, anchor="center")

    # Last 10 events
    for row in data[-10:]:
        event = row.get("Event", "")
        color_tag = "drowsy" if event == "Drowsy" else \
                    "yawn"   if event == "Yawning" else \
                    "speed"  if event == "OverSpeed" else "normal"
        tree.insert("", "end", values=[
            row.get("Date",""), row.get("Time",""),
            event,
            row.get("EAR",""), row.get("MAR",""),
            row.get("Speed","0")
        ], tags=(color_tag,))

    tree.tag_configure("drowsy", foreground="#e74c3c")
    tree.tag_configure("yawn",   foreground="#e67e22")
    tree.tag_configure("speed",  foreground="#9b59b6")
    tree.tag_configure("normal", foreground="white")

    scrollbar = ttk.Scrollbar(table_frame,
                              orient="vertical",
                              command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="x", expand=True)
    scrollbar.pack(side="right", fill="y")

    # ── Refresh button ──
    def refresh():
        root.destroy()
        build_dashboard()

    tk.Button(root, text="REFRESH",
              font=("Helvetica", 10, "bold"),
              bg="#2ecc71", fg="white",
              activebackground="#27ae60",
              bd=0, padx=20, pady=6,
              command=refresh).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    build_dashboard()