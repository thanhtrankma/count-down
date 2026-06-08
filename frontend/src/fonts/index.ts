import manifest from '../../font/fonts.json'

import {
  SYSTEM_FONT,
  SYSTEM_FONT_ID,
  type FontCatalogEntry,
  type FontManifestEntry,
} from './types'
import type { RenderStyle } from '../types/config'

function fontAssetUrl(fileName: string): string {
  return `/font-files/${encodeURIComponent(fileName)}`
}

/** Custom fonts listed in fonts.json (served from /font/ at dev and build). */
export const FONT_CATALOG: FontCatalogEntry[] = (manifest as FontManifestEntry[]).map(
  (entry) => ({
    id: entry.id,
    fileName: entry.file,
    family: entry.family,
    label: entry.label,
    url: fontAssetUrl(entry.file),
  }),
)

export function getFontById(fontId: string | null | undefined): FontCatalogEntry | null {
  if (!fontId || fontId === SYSTEM_FONT_ID) {
    return null
  }
  return FONT_CATALOG.find((font) => font.id === fontId) ?? null
}

export function resolveFontFamily(style: RenderStyle): string {
  const custom = getFontById(style.font_id)
  if (custom) {
    return custom.family
  }
  return style.font_name || SYSTEM_FONT.family
}

export function getFontSelectValue(style: RenderStyle): string {
  if (!style.font_id) {
    return SYSTEM_FONT_ID
  }
  return FONT_CATALOG.some((font) => font.id === style.font_id)
    ? style.font_id
    : SYSTEM_FONT_ID
}

export function applyFontSelection(fontSelectValue: string): Pick<RenderStyle, 'font_id' | 'font_name'> {
  if (fontSelectValue === SYSTEM_FONT_ID) {
    return { font_id: null, font_name: SYSTEM_FONT.family }
  }

  const font = FONT_CATALOG.find((entry) => entry.id === fontSelectValue)
  if (!font) {
    return { font_id: null, font_name: SYSTEM_FONT.family }
  }

  return { font_id: font.id, font_name: font.family }
}

export { SYSTEM_FONT, SYSTEM_FONT_ID }
