# 🎨 BhashaLok — Frontend Web Application

Recommended structure for the Digital Heritage & Regional Language Archive frontend interface.

## 📁 Folder Structure

```
frontend/
├── index.html          # Main HTML entry page
├── script.js            # JavaScript functionality & DOM interactions
├── styles/
│   └── style.css        # Custom styling & responsive layouts
├── pages/              # Separate page components
├── components/         # Reusable UI component modules
├── assets/             # Static images, audio & icons
└── data/               # Mock/sample data & data utilities
```

## 🚀 Running the Frontend

Open `frontend/index.html` directly in any modern web browser, or serve it using an HTTP server (e.g. `python -m http.server 3000` inside the `frontend` folder).

It connects automatically with our **FastAPI Backend Server** running at `http://127.0.0.1:8000/api/v1`.
