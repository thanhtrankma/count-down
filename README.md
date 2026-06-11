# COUNTDOWN Video Generator

A web application for creating long countdown videos (up to 8 hours) rendered locally with FFmpeg.

## Project Structure

```
count-down/
├── frontend/              # Vite + React + TypeScript + Tailwind CSS
├── backend/               # Python FastAPI
├── shared/                # Shared JSON Schema (config.schema.json)
└── docs/                  # Project planning documents
```

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Node.js | 18+ | For the frontend dev server |
| Python | 3.10+ | For the FastAPI backend |
| FFmpeg | recent | **Must include libass** for subtitle burn-in |

### FFmpeg (macOS)

Standard Homebrew `ffmpeg` may lack libass. Install the full build:

```bash
brew install ffmpeg-full
echo 'export PATH="/opt/homebrew/opt/ffmpeg-full/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Verify:

```bash
ffmpeg -filters 2>&1 | grep ass
ffmpeg -version
```

## Install & Run

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: http://localhost:8000

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: http://localhost:5173 (proxies `/api` to the backend)

## Custom Fonts

Add licensed `.ttf` / `.otf` / `.woff2` files to `frontend/font/` and register them in `frontend/font/fonts.json`. See [frontend/font/README.md](./frontend/font/README.md).

The backend reads the same directory (`FONTS_DIR`, default `../frontend/font`) and passes `fontsdir` to FFmpeg's ASS filter so rendered video matches the preview.

```bash
curl http://localhost:8000/api/fonts
```

## Counter Mode

`counter_mode` controls whether the on-screen label counts down or up. Default is `countdown` (backward compatible). `start_time` is always the label shown at t=0.

| Mode | `start_time` | 60s video labels |
|------|--------------|------------------|
| `countdown` | `01:00:00` | `01:00:00` → `00:59:59` → … → `00:59:01` |
| `countup` | `00:00:00` | `00:00:00` → `00:00:01` → … → `00:00:59` |
| `countup` | `00:30:00` | `00:30:00` → `00:30:01` → … → `00:30:59` |

Count-up validation: `start_seconds + (duration_seconds - 1)` must not exceed `99:59:59`.

## Countdown Animations

`RenderStyle.animation` controls per-second transitions (`none`, `fade`, `scale`, `slide_up`, `flip`, `circle`). Default is `none` (backward compatible).

| Style | Preview (CSS) | Video (ASS) |
|-------|---------------|-------------|
| `fade` | `@keyframes countdown-fade` opacity 0→1 (~350ms) | `\fad(in,out)` |
| `scale` | `transform: scale(peak→1)` | `\t` + `\fscx`/`\fscy` |
| `slide_up` | `translateY(offset→0)` | `\move(x,y1,x,y2)` |
| `flip` | Split-flap panels (HH \| MM \| SS), per-segment flip | 3 panel backgrounds (`\p1`) + per-panel `\clip` + `\frx` flap |
| `circle` | SVG `stroke-dashoffset` arc | Vector `\p1` arc on layer 0 + number on layer 1 |

Shared timing uses `animation_intensity` (0.5–1.5): higher = snappier/shorter transitions. Flip duration is defined in `shared/animation_timing.json` as `max(150, round(350 / intensity))` and used by both preview (`transitionMs`) and ASS (`flip_duration_ms`). Circle progress: countdown = `remaining / duration_seconds`; count-up = `elapsed / (duration_seconds - 1)` (clamped 0–1).

Flip parity: video output now mirrors preview layout (3 panels, static colons, segment-diff flips, dark panel chrome). libass `\frx` rotates 0→−90° in one tween (CSS uses `rotateX` 0→−180°), so the fold may look slightly different in FFmpeg output. Panel layout ratios live in `frontend/src/utils/flipLayout.ts` and `compute_flip_layout()` in the backend.

## API Examples

### Health check

```bash
curl http://localhost:8000/api/health
```

### Start a 60-second countdown render

```bash
curl -s -X POST http://localhost:8000/api/render \
  -H 'Content-Type: application/json' \
  -d '{
    "start_time": "00:01:00",
    "counter_mode": "countdown",
    "duration_seconds": 60,
    "resolution": "1920x1080",
    "background_color": "#000000",
    "style": {
      "font_name": "Arial",
      "font_size": 120,
      "color": "#FFFFFF",
      "title_font_size": 48
    },
    "title": "Demo",
    "audio_tick": false
  }'
```

Response:

```json
{
  "jobId": "…",
  "estimatedSizeMb": 0.03,
  "estimatedRenderMinutes": 0.1
}
```

### Start a 30-second count-up render

```bash
curl -s -X POST http://localhost:8000/api/render \
  -H 'Content-Type: application/json' \
  -d '{
    "start_time": "00:00:00",
    "counter_mode": "countup",
    "duration_seconds": 30,
    "resolution": "1920x1080",
    "background_color": "#000000",
    "style": {
      "font_name": "Arial",
      "font_size": 120,
      "color": "#FFFFFF",
      "title_font_size": 48
    }
  }'
```

### Poll job status

```bash
JOB_ID="<jobId from above>"
curl http://localhost:8000/api/jobs/$JOB_ID
```

### Download completed video

```bash
curl -OJ http://localhost:8000/api/jobs/$JOB_ID/download
```

### Download thumbnail

Countdown jobs use the first frame (t=0). Count-up jobs use the last frame (final label).

Auto-generated JPEG after each successful render (`backend/output/{job_id}.jpg`).

```bash
curl -OJ http://localhost:8000/api/jobs/$JOB_ID/thumbnail
```

Returns `image/jpeg`. If thumbnail extraction failed, the job still completes and this endpoint returns 404.

### Cancel a running job

```bash
curl -X DELETE http://localhost:8000/api/jobs/$JOB_ID
```

## Known Limits

| Limit | Value |
|-------|-------|
| Max duration | 8 hours (28,800 seconds) |
| Concurrent renders | **1** — second request returns HTTP 429 |
| Output location | `backend/output/{job_id}.mp4` + `{job_id}.jpg` thumbnail |
| Temp files | `backend/temp/` (ASS, tick audio) |
| Est. file size | ~0.5 MB per minute (CRF 23, 1080p) |
| Est. render time | ~6 seconds per minute of video (hardware dependent) |

Config is validated against `shared/config.schema.json` and mirrored in the backend Pydantic models.

## Tests

### Unit tests (fast)

```bash
cd backend
pytest -q
```

### Integration: 1-hour render (slow, requires FFmpeg)

```bash
cd backend
RUN_INTEGRATION_RENDER=1 pytest -m integration -v
```

Optional timeout override (default 900s):

```bash
INTEGRATION_RENDER_TIMEOUT=1200 RUN_INTEGRATION_RENDER=1 pytest -m integration -v
```

## Manual Test Checklist

See [MANUAL_TEST_CHECKLIST.md](./MANUAL_TEST_CHECKLIST.md).
