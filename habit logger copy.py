import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, filedialog
import json
import os
import datetime

FILE_NAME = "Habit"


# ---------- Data Functions ----------
def load_habits():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as file:
            data = json.load(file)
            # Backwards compatibility: older format was name -> list of dates
            if isinstance(data, dict):
                for k, v in list(data.items()):
                    if isinstance(v, list):
                        data[k] = {
                            "dates": v,
                            "category": "Default",
                            "schedule": [],
                            "reminder": None,
                            "target": 30
                        }
                return data
    return {}


def save_habits():
    with open(FILE_NAME, "w") as file:
        json.dump(habits, file, indent=4)


# ---------- Core Functions ----------
def add_habit():
    name = habit_entry.get().strip()
    if name == "":
        messagebox.showwarning("Warning", "Habit name cannot be empty!")
        return

    if name in habits:
        messagebox.showinfo("Info", "Habit already exists!")
        return

    category = simpledialog.askstring("Category", "Category for this habit (optional):", parent=root)
    schedule = simpledialog.askstring("Schedule", "Days allowed (e.g. Mon,Tue) or leave empty:", parent=root)
    reminder = simpledialog.askstring("Reminder", "Reminder time HH:MM (optional):", parent=root)
    target = simpledialog.askinteger("Target", "Target days (integer, default 30):", initialvalue=30, parent=root)

    schedule_list = []
    if schedule:
        mapping = {"mon":0, "tue":1, "wed":2, "thu":3, "fri":4, "sat":5, "sun":6}
        for token in schedule.split(','):
            t = token.strip().lower()[:3]
            if t in mapping:
                schedule_list.append(mapping[t])

    habits[name] = {
        "dates": [],
        "category": category or "Default",
        "schedule": schedule_list,
        "reminder": reminder or None,
        "target": int(target) if target else 30
    }
    save_habits()
    habit_entry.delete(0, tk.END)
    update_list()


def mark_done():
    selected = habit_list.curselection()
    if not selected:
        messagebox.showwarning("Warning", "Select a habit first!")
        return
    habit = habit_list.get(selected).split(" ✔")[0]
    today = str(datetime.date.today())

    schedule = habits[habit].get("schedule", [])
    weekday = datetime.date.today().weekday()
    if schedule and weekday not in schedule:
        if not messagebox.askyesno("Outside Schedule", "Today is outside the habit's schedule. Mark done anyway?"):
            return

    if today not in habits[habit]["dates"]:
        habits[habit]["dates"].append(today)
        save_habits()
        update_list()
        show_details(habit)
    else:
        messagebox.showinfo("Info", "Already completed today!")


def update_list():
    habit_list.delete(0, tk.END)
    for habit, data in habits.items():
        dates = data.get("dates", [])
        cat = data.get("category", "Default")
        habit_list.insert(tk.END, f"{habit} ✔ {len(dates)} days [{cat}]")


def show_details(habit):
    calendar_box.delete(0, tk.END)
    for date in sorted(habits[habit].get("dates", [])):
        calendar_box.insert(tk.END, date)

    dates = habits[habit].get("dates", [])
    target = habits[habit].get("target", 30)
    progress = min(len(dates), target)
    progress_bar["maximum"] = target
    progress_bar["value"] = progress
    progress_label.config(text=f"Progress: {progress}/{target} days")

    streak = get_streak(habit)
    longest = get_longest_streak(habit)
    rate = get_completion_rate(habit)
    stats_label.config(text=f"Streak: {streak} | Longest: {longest} | Completion Rate: {rate:.1f}%")


def on_select(event):
    selected = habit_list.curselection()
    if selected:
        habit = habit_list.get(selected).split(" ✔")[0]
        show_details(habit)

def delete_habit():
    selected = habit_list.curselection()
    if not selected:
        messagebox.showwarning("Warning", "Select a habit to delete!")
        return

    habit = habit_list.get(selected).split(" ✔")[0]

    confirm = messagebox.askyesno("Confirm Delete", f"Delete habit '{habit}'?")
    if confirm:
        habits.pop(habit)
        save_habits()
        update_list()
        calendar_box.delete(0, tk.END)
        progress_bar["value"] = 0
        progress_label.config(text="Progress: 0/30 days")

def edit_habit():
    selected = habit_list.curselection()
    if not selected:
        messagebox.showwarning("Warning", "Select a habit to edit!")
        return

    old_name = habit_list.get(selected).split(" ✔")[0]

    new_name = simpledialog.askstring("Edit Habit", f"Rename '{old_name}' to:", parent=root)

    if not new_name or new_name.strip() == "":
        return

    if new_name in habits:
        messagebox.showwarning("Warning", "Habit name already exists!")
        return

    habits[new_name] = habits.pop(old_name)
    save_habits()
    update_list()

def get_streak(habit):
    dates = sorted(habits[habit].get("dates", []))
    if not dates:
        return 0

    streak = 1
    for i in range(len(dates) - 1, 0, -1):
        today = datetime.date.fromisoformat(dates[i])
        prev = datetime.date.fromisoformat(dates[i - 1])
        if (today - prev).days == 1:
            streak += 1
        else:
            break

    if datetime.date.fromisoformat(dates[-1]) != datetime.date.today():
        return 0
    return streak

def get_longest_streak(habit):
    dates = sorted(habits[habit].get("dates", []))
    if not dates:
        return 0
    longest = 1
    current = 1
    for i in range(1, len(dates)):
        today = datetime.date.fromisoformat(dates[i])
        prev = datetime.date.fromisoformat(dates[i - 1])
        if (today - prev).days == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    return longest

def get_completion_rate(habit):
    dates = habits[habit].get('dates', [])
    target = habits[habit].get('target', 30)
    if target == 0:
        return 0.0
    return (len(dates) / target) * 100

def edit_history_remove_date():
    sel_h = habit_list.curselection()
    sel_d = calendar_box.curselection()
    if not sel_h or not sel_d:
        messagebox.showwarning("Warning", "Select a habit and a date to remove!")
        return
    habit = habit_list.get(sel_h).split(" ✔")[0]
    date = calendar_box.get(sel_d)
    if messagebox.askyesno("Confirm", f"Remove {date} from '{habit}'?"):
        try:
            habits[habit]["dates"].remove(date)
            save_habits()
            show_details(habit)
            update_list()
        except ValueError:
            pass

def export_habits():
    path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON', '*.json')])
    if path:
        with open(path, 'w') as f:
            json.dump(habits, f, indent=4)
        messagebox.showinfo('Exported', f'Exported to {path}')

def import_habits():
    path = filedialog.askopenfilename(filetypes=[('JSON', '*.json')])
    if path:
        with open(path, 'r') as f:
            data = json.load(f)
            for k, v in data.items():
                habits[k] = v
            save_habits()
            update_list()
        messagebox.showinfo('Imported', f'Imported from {path}')

def search_habits(term):
    term = term.strip().lower()
    habit_list.delete(0, tk.END)
    for habit, data in habits.items():
        if term in habit.lower():
            dates = data.get('dates', [])
            cat = data.get('category', 'Default')
            habit_list.insert(tk.END, f"{habit} ✔ {len(dates)} days [{cat}]")

def reset_search():
    search_entry.delete(0, tk.END)
    update_list()



# ---------- Load Data ----------
habits = load_habits()

# ---------- GUI (Dark Mode) ----------
root = tk.Tk()
root.title("Habit Logger")
root.geometry("680x640")
root.configure(bg="#1e1e1e")
root.resizable(False, False)

style = ttk.Style()
style.theme_use("default")

style.configure("TButton",
                background="#3c3f41",
                foreground="white",
                padding=6,
                font=("Arial", 10, "bold"))

style.map("TButton",
          background=[("active", "#505354")])

style.configure("TProgressbar",
                troughcolor="#3c3c3c",
                background="#00c853")

# Title
tk.Label(root, text="HABIT LOGGER", font=("Arial", 20, "bold"),
         bg="#1e1e1e", fg="#00e676").pack(pady=15)

# Input Frame
input_frame = tk.Frame(root, bg="#1e1e1e")
input_frame.pack(pady=10)

habit_entry = tk.Entry(input_frame, font=("Arial", 12), width=28,
                       bg="#2d2d2d", fg="white", insertbackground="white")
habit_entry.grid(row=0, column=0, padx=10)

ttk.Button(input_frame, text="Add Habit", command=add_habit).grid(row=0, column=1, padx=5)
 
search_entry = tk.Entry(input_frame, font=("Arial", 10), width=18)
search_entry.grid(row=0, column=2, padx=8)
ttk.Button(input_frame, text="Search", command=lambda: search_habits(search_entry.get())).grid(row=0, column=3, padx=3)
ttk.Button(input_frame, text="Reset", command=reset_search).grid(row=0, column=4, padx=3)

# Action Button
ttk.Button(root, text="Mark as Done Today", command=mark_done).pack(pady=10)

# Habit List Frame
tk.Label(root, text="Your Habits", font=("Arial", 12, "bold"),
         bg="#1e1e1e", fg="white").pack()

habit_list = tk.Listbox(root, width=70, height=8,
                        bg="#2d2d2d", fg="white",
                        font=("Arial", 11))
habit_list.pack(pady=8)
habit_list.bind("<<ListboxSelect>>", on_select)

# Progress Section
progress_label = tk.Label(root, text="Progress: 0/30 days", font=("Arial", 11),
                          bg="#1e1e1e", fg="#00e676")
progress_label.pack()

progress_bar = ttk.Progressbar(root, length=500, maximum=30)
progress_bar.pack(pady=5)

# Calendar Section
tk.Label(root, text="Completed Dates", font=("Arial", 12, "bold"),
         bg="#1e1e1e", fg="white").pack(pady=10)

calendar_box = tk.Listbox(root, width=50, height=8,
                          bg="#2d2d2d", fg="white",
                          font=("Arial", 11))
calendar_box.pack()

# Stats label
stats_label = tk.Label(root, text="", font=("Arial", 10), bg="#1e1e1e", fg="#00e676")
stats_label.pack(pady=6)

# Bottom action buttons
bottom_frame = tk.Frame(root, bg="#1e1e1e")
bottom_frame.pack(pady=8)

ttk.Button(bottom_frame, text="Delete Habit", command=delete_habit).grid(row=0, column=0, padx=6)
ttk.Button(bottom_frame, text="Edit Habit", command=edit_habit).grid(row=0, column=1, padx=6)
ttk.Button(bottom_frame, text="Remove Date", command=edit_history_remove_date).grid(row=0, column=2, padx=6)
ttk.Button(bottom_frame, text="Export", command=export_habits).grid(row=0, column=3, padx=6)
ttk.Button(bottom_frame, text="Import", command=import_habits).grid(row=0, column=4, padx=6)

# Load existing habits
update_list()

# Check for reminders at startup (simple check)
now = datetime.datetime.now().strftime('%H:%M')
for h, d in habits.items():
    r = d.get('reminder')
    if r == now:
        messagebox.showinfo('Reminder', f"Reminder: {h} at {r}")

root.mainloop()
