import { Fragment } from 'react'

import {
  flipColonWidth,
  flipGap,
  FLIP_COLON_MARGIN_RATIO,
  FLIP_COLON_SIZE_RATIO,
} from '../../utils/flipLayout'
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
    <div className="flex items-center" style={{ gap: flipGap(fontSize) }}>
      {segments.map((segment, index) => (
        <Fragment key={index}>
          {index > 0 && (
            <span
              className="select-none font-bold"
              style={{
                color,
                fontFamily,
                fontSize: fontSize * FLIP_COLON_SIZE_RATIO,
                opacity: 0.9,
                lineHeight: 1,
                margin: `0 ${fontSize * FLIP_COLON_MARGIN_RATIO}px`,
                width: flipColonWidth(fontSize),
                textAlign: 'center',
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
