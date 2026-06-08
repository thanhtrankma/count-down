import type { CountdownAnimation } from '../../types/config'
import CircleCountdown from './CircleCountdown'
import FadeCountdown from './FadeCountdown'
import FlipCountdown from './FlipCountdown'
import ScaleCountdown from './ScaleCountdown'
import SlideUpCountdown from './SlideUpCountdown'
import StaticCountdown from './StaticCountdown'
import type { AnimatedCountdownProps } from './types'

interface CountdownDisplayProps extends AnimatedCountdownProps {
  animation: CountdownAnimation
}

export default function CountdownDisplay({
  animation,
  ...props
}: CountdownDisplayProps) {
  switch (animation) {
    case 'fade':
      return <FadeCountdown {...props} />
    case 'scale':
      return <ScaleCountdown {...props} />
    case 'slide_up':
      return <SlideUpCountdown {...props} />
    case 'flip':
      return <FlipCountdown {...props} />
    case 'circle':
      return <CircleCountdown {...props} />
    case 'none':
    default:
      return <StaticCountdown {...props} />
  }
}
