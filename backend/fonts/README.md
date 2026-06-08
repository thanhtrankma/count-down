# Backend fonts directory (optional)

By default the API uses `../frontend/font` as `FONTS_DIR` — the same folder as the frontend font catalog.

For deployments where the frontend tree is not present, either:

```bash
ln -s ../frontend/font backend/fonts
```

and set `FONTS_DIR` to this directory, or point `FONTS_DIR` at any folder containing `fonts.json` and font files.

See `frontend/font/README.md` for how to add fonts.
