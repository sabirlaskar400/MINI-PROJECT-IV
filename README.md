# AI Object Analytics System
### BCA Semester Project — Computer Vision Dashboard

A professional desktop application built with **PyQt6 + YOLOv8 + Supervision**.
Detects objects via webcam, counts IN/OUT crossings, and displays live analytics.

---

## 📁 Project Structure

```
ai_analytics/
│
├── main.py                  ← Run this file to launch the app
│
├── ui/
│   ├── theme.py             ← Colors, fonts, reusable widgets
│   ├── dashboard.py         ← Home panel (stats + clock)
│   ├── camera_view.py       ← Live feed + detection worker thread
│   ├── analytics.py         ← Charts (matplotlib)
│   ├── reports.py           ← Table view + export
│   └── settings.py          ← Theme toggle + preferences
│
├── core/
│   ├── detector.py          ← YOLOv8 model wrapper
│   ├── tracker.py           ← LineZone + annotators
│   └── data_manager.py      ← File I/O + session history
│
├── requirements.txt
└── project_report.txt       ← Auto-generated session log
```

---

## ⚙️ Setup

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python main.py
```

The first time you click **▶ START CAMERA**, YOLOv8 will automatically
download the `yolov8n.pt` model (~6 MB). An internet connection is required
for this one-time download.

---

## 🎮 How to Use

| Step | Action |
|------|--------|
| 1 | Launch: `python main.py` |
| 2 | Click **Live Camera** in the sidebar |
| 3 | Press **▶ START CAMERA** |
| 4 | Move a **bottle**, **scissors**, or **cell phone** across the blue line |
| 5 | Watch IN/OUT counters update in real-time |
| 6 | Visit **Analytics** for charts |
| 7 | Visit **Reports** to view and export the movement log |
| 8 | Press **💾 Save Session** to write `project_report.txt` |

---

## 🎨 Features

- **Dark / Light mode toggle** (Settings page)
- **Start / Stop camera** with loading animation
- **Error handling** if webcam not found
- **Live matplotlib charts** (IN/OUT timeline + category distribution)
- **Searchable table** with CSV/TXT export
- **Status bar**: Camera status · System ready · Live clock · Event counter
- **Modular architecture**: UI and AI logic fully separated

---

## 🧠 Tracked Object Classes (YOLOv8)

| ID | Class |
|----|-------|
| 39 | bottle |
| 41 | scissors |
| 67 | cell phone |

To add more classes, edit `TRACKED_CLASSES` in `core/detector.py`.

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| `Camera not found` | Connect a webcam; try Camera Index 1 or 2 in Settings |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| Slow detection | Use a smaller model: change `yolov8n.pt` → `yolov8n.pt` is already the smallest |
| Charts not showing | Make sure `matplotlib` is installed: `pip install matplotlib` |
