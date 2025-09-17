# FoodFast Modular Monolith (Frontend templates + unified API)

## What was added
- User roles in feature1 (`customer` or `employee`) with lightweight DB migration
- Frontend pages in `templates/` and assets in `static/`:
  - `index.html`: login/register with client-side validation
  - `customer.html`: profile edit, create/list orders, long-poll status, SSE driver location with fake simulation, chat to support
  - `employee.html`: websocket chat list and conversation, SSE order notifications
- Unified root `app.py` to register all blueprints and serve templates/static
- `requirements.txt` for dependencies

## Central settings
All shared configuration is in `config/settings.py` and loaded by the monolith `app.py`:
- `SECRET_KEY`
- JWT: `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRES`, `JWT_REFRESH_TOKEN_EXPIRES`, `JWT_HEADER_TYPE`
- Database: `SQLALCHEMY_DATABASE_URI` (defaults to `sqlite:///instance/foodfast_accounts.db`)
- Security: `BCRYPT_LOG_ROUNDS`
- Orders: `LONG_POLL_TIMEOUT`, `ORDER_STATUSES`
- Redis: `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`

You can override these via environment variables (e.g., `$env:JWT_SECRET_KEY = '...'`).

## Run (Windows PowerShell)
```powershell
# 1) Create venv (optional)
python -m venv .venv; .\.venv\Scripts\Activate.ps1

# 2) Install deps
pip install -r requirements.txt

# 3) Set env (dev uses SQLite in ./instance/foodfast_accounts.db)
$env:FLASK_ENV = 'development'
$env:JWT_SECRET_KEY = 'dev-secret'    # change for production

# 4) Start the monolith API + templates
python app.py
# Open http://127.0.0.1:5000  (serves /templates/index.html)

# 5) (Optional) Start support chat (separate process/port 5005)
# Only needed if you want live chat; otherwise UI will fail to connect
python implementations/feature5_support_chat/app.py
```

## Key endpoints used by frontend
- Auth (feature1):
  - POST `/api/v1/account/register` {email, password, first_name, last_name, role}
  - POST `/api/v1/account/login` {email, password}
  - GET `/api/v1/account/profile` (Bearer access token)
  - PUT `/api/v1/account/profile` (Bearer)
  - POST `/api/v1/account/refresh` (Bearer refresh token)
- Orders (feature2):
  - POST `/api/v1/orders` {customer_id, items[], delivery_address, total_amount}
  - GET `/api/v1/orders/customer/{id}`
  - GET `/api/v1/orders/{order_id}/track?last_status=...&timeout=45` (long polling)
- Driver location (feature3):
  - GET `/api/v1/tracking/order/{order_id}/stream?customer_id={id}` (SSE)
  - POST `/api/v1/drivers/{driver_id}/online` {is_online, current_order_id}
  - POST `/api/v1/drivers/{driver_id}/location` {latitude, longitude}
- Notifications (feature4):
  - GET `/api/v1/orders/stream` (SSE Redis channel)
  - POST `/api/v1/orders` (publish)
- Support chat (feature5): Socket.IO on `http://localhost:5005`

## Notes
- All features share one SQLite database file at `instance/foodfast_accounts.db` (auto-created).
- The frontend saves access and refresh JWTs to cookies and retries with `/api/v1/account/refresh` when a 401 occurs.
- Driver location in the UI is simulated every 15s when you start stream.
- Order long-polling requests run continuously with a 45s server timeout per request.
- Employee can see chat list and receive live order notifications via SSE.
