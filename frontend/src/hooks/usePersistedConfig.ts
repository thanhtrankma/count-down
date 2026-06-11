import { useCallback, useEffect, useState } from 'react'

import { DEFAULT_RENDER_CONFIG, type RenderConfig } from '../types/config'

const STORAGE_KEY = 'countdown-render-config'

function loadPersistedConfig(): RenderConfig {
  if (typeof window === 'undefined') {
    return DEFAULT_RENDER_CONFIG
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return DEFAULT_RENDER_CONFIG
    }

    const parsed = JSON.parse(raw) as Partial<RenderConfig>
    return {
      ...DEFAULT_RENDER_CONFIG,
      ...parsed,
      style: {
        ...DEFAULT_RENDER_CONFIG.style,
        ...parsed.style,
        font_id: parsed.style?.font_id ?? null,
        animation: parsed.style?.animation ?? 'none',
        animation_intensity: parsed.style?.animation_intensity ?? 1.0,
      },
      title: parsed.title ?? '',
      audio_tick: parsed.audio_tick ?? false,
      counter_mode: parsed.counter_mode ?? 'countdown',
    }
  } catch {
    return DEFAULT_RENDER_CONFIG
  }
}

export function usePersistedConfig() {
  const [config, setConfigState] = useState<RenderConfig>(loadPersistedConfig)

  const setConfig = useCallback((next: RenderConfig | ((prev: RenderConfig) => RenderConfig)) => {
    setConfigState(next)
  }, [])

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(config))
  }, [config])

  const resetConfig = useCallback(() => {
    setConfigState(DEFAULT_RENDER_CONFIG)
  }, [])

  return { config, setConfig, resetConfig }
}
