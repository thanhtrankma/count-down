import { cpSync, createReadStream, existsSync, mkdirSync, statSync } from 'node:fs'
import { extname, join, resolve } from 'node:path'
import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const FONT_DIR = resolve(__dirname, 'font')
const FONT_MIME: Record<string, string> = {
  '.ttf': 'font/ttf',
  '.otf': 'font/otf',
  '.woff2': 'font/woff2',
}

const FONT_EXTENSIONS = new Set(['.ttf', '.otf', '.woff2'])

function fontAssetsPlugin(): Plugin {
  return {
    name: 'countdown-font-assets',
    configureServer(server) {
      // Serve only binary font files under /font-files/ — not /font/, which
      // conflicts with Vite serving frontend/font/fonts.json as an ES module.
      server.middlewares.use('/font-files', (req, res, next) => {
        const requestPath = req.url?.split('?')[0] ?? ''
        const fileName = decodeURIComponent(requestPath.replace(/^\//, ''))
        if (!fileName || fileName.includes('..')) {
          next()
          return
        }

        const ext = extname(fileName).toLowerCase()
        if (!FONT_EXTENSIONS.has(ext)) {
          next()
          return
        }

        const filePath = join(FONT_DIR, fileName)
        if (!existsSync(filePath) || !statSync(filePath).isFile()) {
          next()
          return
        }

        res.setHeader('Content-Type', FONT_MIME[ext] ?? 'application/octet-stream')
        createReadStream(filePath).pipe(res)
      })
    },
    closeBundle() {
      const outputDir = resolve(__dirname, 'dist/font-files')
      mkdirSync(outputDir, { recursive: true })
      cpSync(FONT_DIR, outputDir, {
        recursive: true,
        filter: (src) => {
          const base = src.split(/[/\\]/).pop() ?? ''
          return (
            !base.endsWith('.md') &&
            base !== 'fonts.json' &&
            FONT_EXTENSIONS.has(extname(base).toLowerCase())
          )
        },
      })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss(), fontAssetsPlugin()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
