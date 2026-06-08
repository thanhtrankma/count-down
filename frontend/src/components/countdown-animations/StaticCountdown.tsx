import type { AnimatedCountdownProps } from './types'

export default function StaticCountdown({
  display,
  color,
  fontFamily,
  fontSize,
}: AnimatedCountdownProps) {
  return (
    <span
      className="font-bold tabular-nums tracking-tight"
      style={{ color, fontFamily, fontSize, lineHeight: 1.1 }}
    >
      {display}
    </span>
  )
}
