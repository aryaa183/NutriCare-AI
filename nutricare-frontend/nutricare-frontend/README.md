# NutriCare — Frontend

React + Vite + TypeScript + Tailwind v4 client for the NutriCare AI backend.

## Setup

```bash
npm install
cp .env.example .env   # adjust VITE_API_BASE_URL if your backend isn't on :8000
npm run dev
```

Open http://localhost:5173 (Vite's default dev port — the app assumes this
in the backend CORS config below, so don't change it without updating that
too).

## ⚠️ Required: enable CORS on the backend first

The backend as originally built has no CORS middleware, so your browser will
block every request from this frontend with a CORS error. Add this to
`backend/app/main.py`, right after the `app = FastAPI(...)` block and before
`app.include_router(...)`:

```python
from fastapi.middleware.cors import CORSMiddleware

# Dev CORS: allows the Vite frontend (localhost:5173) to call this API.
# Tighten allow_origins to your real frontend domain before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

(Don't forget the `from fastapi.middleware.cors import CORSMiddleware` import
at the top of the file.) Restart `uvicorn` after saving.

## What's built

- **Auth**: signup, login, logout (JWT stored in `localStorage`; auto-redirects
  to `/login` on a 401)
- **Onboarding**: first-time health profile setup (redirects here automatically
  if no profile exists yet)
- **Dashboard**: daily calorie/protein progress + today's logged meals
- **Recommendations**: per-meal-type tabs, like/dislike feedback, "log this
  meal"
- **Meal history**: past logged meals with recipe names resolved
- **Profile**: view/edit the health profile (age, goal, diet type, allergies,
  conditions, etc.)

## Project structure

```
src/
  api/          typed request/response shapes + endpoint functions + axios client
  store/        zustand stores (auth, profile)
  routes/       RequireAuth / RequireProfile guards
  components/   shared UI (form fields, buttons, nav shell, recipe row, etc.)
  pages/        one file per route
```

## Notes / known trade-offs

- **No token refresh flow**: the backend issues a refresh token at login but
  doesn't yet expose a `/auth/refresh` endpoint (see backend README — logout
  is a documented no-op for the same reason: stateless JWT). So on a 401 the
  client just signs the user out rather than silently refreshing. Add
  `POST /auth/refresh` on the backend first if you want this.
- **Meal history doesn't include recipe names from the API** (`GET
  /meals/history` only returns `recipe_id`), so the page resolves names with
  one `GET /recipes/{id}` call per unique recipe in the list. Fine at
  personal-history scale; would want the backend to join this itself if
  history grows large.
- Feedback (like/dislike) and "logged" state on the Recommendations page are
  client-side only for the current session — they reset on page reload, even
  though the backend does persist them. A refetch-and-merge on load would fix
  this if you want it to persist visually across reloads too.
