import { slideOffsetPx, transitionMs } from '../../utils/animation'
import type { AnimatedCountdownProps } from './types'

export default function SlideUpCountdown({
  display,
  color,
  fontFamily,
  fontSize,
  intensity,
}: AnimatedCountdownProps) {
  const duration = transitionMs(intensity)
  const offset = slideOffsetPx(intensity, fontSize)

  return (
    <span
      key={display}
      className="inline-block font-bold tabular-nums tracking-tight"
      style={{
        color,
        fontFamily,
        fontSize,
        lineHeight: 1.1,
        animation: `countdown-slide-up ${duration}ms ease-out`,
        ['--countdown-slide-offset' as string]: `${offset}px`,
      }}
    >
      {display}
    </span>
  )
}
