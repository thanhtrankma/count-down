import { useMemo } from 'react'

import CountdownDisplay from './countdown-animations/CountdownDisplay'
import { resolveFontFamily } from '../fonts'
import { useCountdown } from '../hooks/useCountdown'
import type { RenderConfig } from '../types/config'
import { circleProgress } from '../utils/animation'
import { parseResolution } from '../utils/formatTime'

const PREVIEW_LOOP_SECONDS = 12

interface PreviewPlayerProps {
  config: RenderConfig
}

export default function PreviewPlayer({ config }: PreviewPlayerProps) {
  const { width, height } = useMemo(
    () => parseResolution(config.resolution),
    [config.resolution],
  )

  const counterMode = config.counter_mode ?? 'countdown'
  const { display, remainingSeconds, elapsedSeconds } = useCountdown({
    startTime: config.start_time,
    counterMode,
    active: true,
    loopDuration: PREVIEW_LOOP_SECONDS,
  })

  const previewFontSize = Math.max(16, Math.round((config.style.font_size / height) * 280))
  const previewTitleSize = Math.max(12, Math.round((config.style.title_font_size / height) * 280))
  const title = config.title?.trim()
  const fontFamily = resolveFontFamily(config.style)
  const animation = config.style.animation ?? 'none'
  const intensity = config.style.animation_intensity ?? 1.0
  const progress =
    counterMode === 'countup'
      ? circleProgress(elapsedSeconds, config.duration_seconds, 'countup')
      : circleProgress(remainingSeconds, config.duration_seconds, 'countdown')

  return (
    <div className="flex h-full flex-col">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-white">Preview</h2>
        <p className="mt-1 text-sm text-gray-400">
          Live preview loops every {PREVIEW_LOOP_SECONDS} seconds.
        </p>
      </div>

      <div className="flex flex-1 items-center justify-center">
        <div
          className="relative w-full max-w-full overflow-hidden rounded-xl border border-gray-800 shadow-2xl shadow-black/40"
          style={{
            aspectRatio: `${width} / ${height}`,
            maxHeight: 'min(70vh, 640px)',
            backgroundColor: config.background_color,
          }}
        >
          <div className="absolute inset-0 flex flex-col items-center justify-center px-4 text-center">
            {title && (
              <p
                className="mb-4 max-w-full truncate font-semibold leading-tight"
                style={{
                  color: config.style.color,
                  fontFamily,
                  fontSize: `${previewTitleSize}px`,
                }}
              >
                {title}
              </p>
            )}

            <CountdownDisplay
              animation={animation}
              display={display}
              color={config.style.color}
              fontFamily={fontFamily}
              fontSize={previewFontSize}
              intensity={intensity}
              progress={progress}
            />
          </div>

          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent px-3 py-2">
            <p className="text-xs text-gray-300">
              {config.resolution} · {PREVIEW_LOOP_SECONDS}s loop
              {animation !== 'none' ? ` · ${animation}` : ''}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
