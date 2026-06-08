import { transitionMs } from '../../utils/animation'
import type { AnimatedCountdownProps } from './types'

export default function CircleCountdown({
  display,
  color,
  fontFamily,
  fontSize,
  intensity,
  progress,
}: AnimatedCountdownProps) {
  const duration = transitionMs(intensity)
  const size = Math.round(fontSize * 2.2)
  const stroke = Math.max(3, Math.round(fontSize * 0.05))
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const dashOffset = circumference * (1 - progress)

  return (
    <div
      key={display}
      className="relative inline-flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg
        className="absolute inset-0"
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        aria-hidden
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: `stroke-dashoffset ${duration}ms ease-out` }}
        />
      </svg>
      <span
        className="relative font-bold tabular-nums tracking-tight"
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
    </div>
  )
}
