# EV Diagnostic Assistant — Frontend

React 18 + Vite SPA with a dark navy/blue theme matching the EVVV.jpeg mockup.

## Quick Start

### 1. Start the Flask REST API

```bash
cd backend
python flask_api.py
# Runs on http://localhost:5000
```

### 2. Start the React dev server

```bash
cd frontend
npm run dev
# Runs on http://localhost:5173
```

Open http://localhost:5173 in your browser.

## Environment Variables

`frontend/.env` (already created):
```
VITE_API_BASE_URL=http://localhost:5000
```

`backend/.env` (already exists):
```
GROQ_API_KEY=...
JWT_SECRET=...   # optional, defaults to a dev secret
```

## Tech Stack

- React 18 + Vite
- Tailwind CSS (custom dark theme)
- React Router v6
- Axios (with auth interceptors)
- react-markdown (chat responses)
- lucide-react (icons)

## Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page (public) |
| `/login` | Login form |
| `/register` | Registration form |
| `/dashboard` | Dashboard with nav cards |
| `/chat` | EV diagnostic chat |
| `/history` | Conversation history |
| `/upload` | PDF manual upload |

## Running Tests

```bash
cd frontend
npm test          # single run
npm run test:watch  # watch mode
```
