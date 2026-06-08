import { FONT_CATALOG } from './index'

function formatFromFileName(fileName: string): string {
  const lower = fileName.toLowerCase()
  if (lower.endsWith('.woff2')) {
    return 'woff2'
  }
  if (lower.endsWith('.otf')) {
    return 'opentype'
  }
  return 'truetype'
}

async function fontFileExists(url: string): Promise<boolean> {
  try {
    const response = await fetch(url, { method: 'HEAD' })
    return response.ok
  } catch {
    return false
  }
}

export async function loadFonts(): Promise<void> {
  if (typeof document === 'undefined') {
    return
  }

  const availableFonts = await Promise.all(
    FONT_CATALOG.map(async (font) => ({
      font,
      exists: await fontFileExists(font.url),
    })),
  )

  const rules = availableFonts
    .filter((entry) => entry.exists)
    .map(
      ({ font }) => `
@font-face {
  font-family: '${font.family.replace(/'/g, "\\'")}';
  src: url('${font.url}') format('${formatFromFileName(font.fileName)}');
  font-display: swap;
}`,
    )

  if (rules.length === 0) {
    return
  }

  const style = document.createElement('style')
  style.setAttribute('data-countdown-fonts', 'true')
  style.textContent = rules.join('\n')
  document.head.appendChild(style)
}
