# Custom Fonts

Place licensed `.ttf`, `.otf`, or `.woff2` files in this directory.

## Add a new font

1. Copy the font file here, e.g. `BebasNeue-Regular.ttf`
2. Add an entry to `fonts.json`:

```json
{
  "id": "bebas-neue",
  "file": "BebasNeue-Regular.ttf",
  "family": "Bebas Neue",
  "label": "Bebas Neue"
}
```

3. **`family` must match** the font's internal family name (used in ASS subtitles and CSS). If preview and render differ, check the name with `fc-query` or a font viewer.
4. Restart the frontend dev server so Vite picks up new files.

Only use fonts you have the right to embed in video output.

## Backend

The API reads fonts from this same folder (`FONTS_DIR` defaults to `../frontend/font`). No copy step is required for local development.

The UI serves font binaries at `/font-files/` (not `/font/`) so Vite can load `fonts.json` as a module without MIME conflicts.

Optional symlink for deployment:

```bash
ln -s ../frontend/font backend/fonts
```

Or set `FONTS_DIR=/absolute/path/to/frontend/font`.
