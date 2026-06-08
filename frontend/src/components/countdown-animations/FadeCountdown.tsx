import { transitionMs } from '../../utils/animation'
import type { AnimatedCountdownProps } from './types'

export default function FadeCountdown({
  display,
  color,
  fontFamily,
  fontSize,
  intensity,
}: AnimatedCountdownProps) {
  const duration = transitionMs(intensity)

  return (
    <span
      key={display}
      className="font-bold tabular-nums tracking-tight"
      style={{
        color,
        fontFamily,
        fontSize,
        lineHeight: 1.1,
        animation: `countdown-fade ${duration}ms ease-out`,
      }}
    >
      {display}
    </span>
  )
}
