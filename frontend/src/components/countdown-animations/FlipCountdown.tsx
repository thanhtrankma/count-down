import { Fragment } from 'react'

import type { AnimatedCountdownProps } from './types'
import SplitFlapPanel from './SplitFlapPanel'

export default function FlipCountdown({
  display,
  color,
  fontFamily,
  fontSize,
  intensity,
}: AnimatedCountdownProps) {
  const segments = display.split(':')

  return (
    <div className="flex items-center" style={{ gap: fontSize * 0.12 }}>
      {segments.map((segment, index) => (
        <Fragment key={index}>
          {index > 0 && (
            <span
              className="select-none font-bold"
              style={{
                color,
                fontFamily,
                fontSize: fontSize * 0.85,
                opacity: 0.9,
                lineHeight: 1,
                margin: `0 ${fontSize * 0.04}px`,
              }}
              aria-hidden
            >
              :
            </span>
          )}
          <SplitFlapPanel
            value={segment}
            fontFamily={fontFamily}
            fontSize={fontSize}
            textColor={color}
            intensity={intensity}
          />
        </Fragment>
      ))}
    </div>
  )
}
