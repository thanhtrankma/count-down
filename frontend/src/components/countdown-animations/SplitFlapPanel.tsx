import { useEffect, useState } from 'react'

import { transitionMs } from '../../utils/animation'

interface SplitFlapPanelProps {
  value: string
  fontFamily: string
  fontSize: number
  textColor: string
  intensity: number
}

export default function SplitFlapPanel({
  value,
  fontFamily,
  fontSize,
  textColor,
  intensity,
}: SplitFlapPanelProps) {
  const [shown, setShown] = useState(value)
  const [prev, setPrev] = useState(value)
  const [flipping, setFlipping] = useState(false)
  const duration = transitionMs(intensity)

  useEffect(() => {
    if (value === shown) {
      return
    }
    setPrev(shown)
    setFlipping(true)
    const timer = window.setTimeout(() => {
      setShown(value)
      setFlipping(false)
    }, duration)
    return () => window.clearTimeout(timer)
  }, [value, shown, duration])

  const panelWidth = fontSize * 1.65
  const panelHeight = fontSize * 1.4
  const radius = fontSize * 0.14

  const textStyle = {
    fontFamily,
    fontSize,
    color: textColor,
    fontWeight: 700 as const,
    letterSpacing: '0.04em',
    lineHeight: 1,
  }

  const fullText = (text: string) => (
    <div
      className="absolute left-0 flex w-full items-center justify-center"
      style={{ height: panelHeight, top: 0 }}
    >
      <span style={textStyle}>{text}</span>
    </div>
  )

  return (
    <div
      className="relative"
      style={{
        width: panelWidth,
        height: panelHeight,
        perspective: `${fontSize * 5}px`,
      }}
    >
      <div
        className="relative h-full w-full overflow-hidden"
        style={{
          borderRadius: radius,
          background:
            'linear-gradient(180deg, #3a3a3a 0%, #2a2a2a 46%, #1c1c1c 54%, #262626 100%)',
          boxShadow:
            '0 6px 16px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.1), inset 0 -1px 0 rgba(0,0,0,0.35)',
        }}
      >
        {/* Incoming top half (revealed behind flap) */}
        <div
          className="absolute left-0 right-0 top-0 overflow-hidden"
          style={{ height: '50%', zIndex: 1 }}
        >
          {fullText(flipping ? value : shown)}
        </div>

        {/* Static bottom half */}
        <div
          className="absolute bottom-0 left-0 right-0 overflow-hidden"
          style={{ height: '50%', zIndex: 1 }}
        >
          <div className="relative" style={{ height: panelHeight, top: -panelHeight / 2 }}>
            {fullText(flipping ? prev : shown)}
          </div>
        </div>

        {/* Top flap — old value folding down */}
        {flipping && (
          <div
            className="absolute left-0 right-0 top-0 overflow-hidden"
            style={{
              height: '50%',
              zIndex: 3,
              transformOrigin: 'center bottom',
              transformStyle: 'preserve-3d',
              animation: `flip-clock-flap ${duration}ms ease-in forwards`,
              backfaceVisibility: 'hidden',
            }}
          >
            {fullText(prev)}
            <div
              className="pointer-events-none absolute inset-0"
              style={{
                background:
                  'linear-gradient(180deg, transparent 55%, rgba(0,0,0,0.35) 100%)',
              }}
            />
          </div>
        )}

        {/* Hinge */}
        <div
          className="pointer-events-none absolute left-0 right-0"
          style={{
            top: '50%',
            zIndex: 5,
            height: Math.max(2, fontSize * 0.05),
            marginTop: -Math.max(1, fontSize * 0.025),
            background: 'rgba(0,0,0,0.75)',
            boxShadow: '0 1px 0 rgba(255,255,255,0.07)',
          }}
        />

        {/* Top shine */}
        <div
          className="pointer-events-none absolute left-0 right-0 top-0"
          style={{
            height: '48%',
            borderRadius: `${radius}px ${radius}px 0 0`,
            background: 'linear-gradient(180deg, rgba(255,255,255,0.06) 0%, transparent 100%)',
            zIndex: 4,
          }}
        />
      </div>
    </div>
  )
}
