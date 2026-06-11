# Manual Test Checklist

Use this list before releasing or after significant changes.

## Environment

- [ ] `curl http://localhost:8000/api/health` returns `"ffmpeg": true`
- [ ] Frontend loads at http://localhost:5173
- [ ] Backend logs are JSON structured (one object per line)

## Custom Fonts

- [ ] `GET /api/fonts` lists manifest entries with `available` flag
- [ ] Font file + `fonts.json` entry appears in ConfigForm font dropdown
- [ ] Preview uses custom font family
- [ ] Rendered MP4 uses same font (with `fontsdir`)
- [ ] Missing font file falls back to Arial with warning toast

## Counter Mode

- [ ] **Count down** (default): preview counts from start_time toward 00:00:00
- [ ] **Count up**: preview counts from start_time upward each second
- [ ] Switching to count up suggests `00:00:00` start time (optional preset)
- [ ] Count up overflow (e.g. start `99:59:00`, duration 120s) disables submit with clear error
- [ ] Render 30s count-up from `00:00:00` → labels `00:00:00` … `00:00:29`
- [ ] Flip/fade/scale work with count-up labels
- [ ] Circle arc fills gradually (count-up) vs shrinks (count-down)
- [ ] Job without `counter_mode` in stored config behaves as countdown
- [ ] Render progress shows **Mode: Count up** / **Count down**
- [ ] Count-up thumbnail shows final label (not start_time at t=0)

## Configuration & Validation

- [ ] Invalid start time (e.g. `99:99:99`) disables **Generate Video**
- [ ] Invalid hex color disables submit and shows inline error
- [ ] Duration 0 or > 28800 disables submit
- [ ] Config persists after page refresh (localStorage)
- [ ] **Reset** restores defaults

## Countdown Animations

- [ ] Each animation preset (None, Fade, Scale, Slide, Flip, Circle) updates preview every second
- [ ] Intensity slider changes animation strength when animation ≠ None
- [ ] Render 15s sample per style; motion visible in output MP4
- [ ] Circle arc shrinks as countdown progresses
- [ ] Flip: only the changing HH/MM/SS segment flips each second (preview + video)
- [ ] Flip: render 15s 1920×1080 sample; panel layout and timing roughly match preview
- [ ] Title text is not animated

## Preview

- [ ] Preview countdown updates every second
- [ ] Title appears when set
- [ ] Format presets change preview aspect ratio (16:9, 9:16, 1:1)

## Short Render (60s)

- [ ] Submit 60s render from `00:01:00`
- [ ] Progress bar advances during render
- [ ] Job completes with download link
- [ ] Thumbnail preview: countdown shows first frame (start_time label); count-up shows last frame (final label)
- [ ] **Download Thumbnail** saves a valid JPG
- [ ] Downloaded MP4 shows countdown 00:01:00 → 00:00:01
- [ ] Labels change once per second

## Long Render (>1h)

- [ ] Selecting duration > 3600s shows browser confirm dialog
- [ ] Cancelling confirm does not start render
- [ ] Confirming starts render and shows progress

## Audio Tick

- [ ] Enable **Audio tick each second**
- [ ] Render 10–30s sample
- [ ] Output MP4 has audible tick at each second boundary

## Cancel

- [ ] Start a 5+ minute render
- [ ] Click **Cancel** — job status becomes `cancelled`
- [ ] No partial MP4 left in `backend/output/`

## Concurrent Limit

- [ ] Start a long render
- [ ] Second submit returns error toast (HTTP 429)
- [ ] Submit button disabled while job is active
- [ ] **Active Render Jobs** panel lists the blocking job (status, progress, config)
- [ ] Cancel from Active Render Jobs panel frees the slot for a new submit

## Error Handling

- [ ] Stop backend → submit shows error toast
- [ ] Failed job shows error in progress panel and toast
- [ ] Failed job → `GET /api/jobs/{id}/thumbnail` returns 404
- [ ] Thumbnail extract failure (if simulated) → video still downloadable via MP4 link

## API (curl)

- [ ] `POST /api/render` with valid JSON returns `jobId`
- [ ] `GET /api/jobs/{id}` returns status and progress
- [ ] `GET /api/jobs/{id}/download` works when completed
- [ ] `GET /api/jobs/{id}/thumbnail` returns `image/jpeg` when completed
- [ ] `GET /api/jobs/{id}/thumbnail` returns 409 while job is running
- [ ] `DELETE /api/jobs/{id}` cancels running job
