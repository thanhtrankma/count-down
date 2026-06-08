export interface FontManifestEntry {
  id: string
  file: string
  family: string
  label: string
}

export interface FontCatalogEntry {
  id: string
  fileName: string
  family: string
  label: string
  url: string
}

export const SYSTEM_FONT_ID = '__system__'

export const SYSTEM_FONT: FontCatalogEntry = {
  id: SYSTEM_FONT_ID,
  fileName: '',
  family: 'Arial',
  label: 'System — Arial',
  url: '',
}
