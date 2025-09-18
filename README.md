# Communication Patterns by Feature

This project demonstrates multiple real-time and near-real-time communication patterns. Each feature focuses on one pattern:

1) Feature 1 — Account Management
- Pattern: Simple Request/Response (classic REST)
- Use: Registration, login, profile CRUD using standard HTTP.

2) Feature 2 — Order Tracking
- Pattern: Long Polling
- Use: Client polls the server with a timeout to receive order status updates as they occur.

3) Feature 3 — Driver Location
- Pattern: Server-Sent Events (SSE)
- Use: Continuous one-way stream from server to client for live driver location updates.

4) Feature 4 — Restaurant Notifications
- Pattern: SSE with Redis Pub/Sub
- Use: Backend subscribes to Redis channel(s) and pushes notifications to browsers over SSE.

5) Feature 5 — Support Chat
- Pattern: WebSocket
- Use: Bi-directional, low-latency messaging between client and server for live chat.

6) Feature 6 — Announcements
- Pattern: SSE with Redis Pub/Sub
- Use: Broadcast announcements to all connected clients via Redis-backed SSE stream.

7) Feature 7 — Image Upload Processing
- Pattern: Short Polling
- Use: Client uploads an image, then polls job status periodically to retrieve results when ready.

## How to run (Windows PowerShell)

1) Optional: create and activate a virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies
```powershell
pip install -r requirements.txt
```

3) Create a `.env` file in the project root with at least these values

4) Run the app
```powershell
python app.py
```

5) Open the UI in your browser
- http://127.0.0.1:5000

Notes
- `.gitignore` ignores only `.env` by design.
- If you plan to use Feature 7 (image upload), set `AZURE_STORAGE_CONNECTION_STRING` and `AZURE_CONTAINER` in `.env` before testing those endpoints.
- can test it via https://gsg-fgcfh9anhaeqaff9.uaenorth-01.azurewebsites.net/
