import { scalePeak, transitionMs } from '../../utils/animation'
import type { AnimatedCountdownProps } from './types'

export default function ScaleCountdown({
  display,
  color,
  fontFamily,
  fontSize,
  intensity,
}: AnimatedCountdownProps) {
  const duration = transitionMs(intensity)
  const peak = scalePeak(intensity)

  return (
    <span
      key={display}
      className="inline-block font-bold tabular-nums tracking-tight"
      style={{
        color,
        fontFamily,
        fontSize,
        lineHeight: 1.1,
        animation: `countdown-scale ${duration}ms ease-out`,
        ['--countdown-scale-peak' as string]: peak,
      }}
    >
      {display}
    </span>
  )
}
