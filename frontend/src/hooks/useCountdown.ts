import { useCallback, useEffect, useRef, useState } from 'react'

import type { CounterMode } from '../types/config'
import { displaySecondsAt } from '../utils/counterLabel'
import { formatTime, tryParseTime } from '../utils/formatTime'

export interface UseCountdownOptions {
  startTime: string
  counterMode?: CounterMode
  active?: boolean
  loopDuration?: number
  tickMs?: number
}

export interface UseCountdownResult {
  display: string
  remainingSeconds: number
  elapsedSeconds: number
  displaySeconds: number
  reset: () => void
}

export function useCountdown({
  startTime,
  counterMode = 'countdown',
  active = true,
  loopDuration,
  tickMs = 1000,
}: UseCountdownOptions): UseCountdownResult {
  const lastValidStartSecondsRef = useRef(0)
  const parsedStartSeconds = tryParseTime(startTime)
  if (parsedStartSeconds !== null) {
    lastValidStartSecondsRef.current = parsedStartSeconds
  }
  const startSeconds =
    parsedStartSeconds ?? lastValidStartSecondsRef.current
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const startTimeRef = useRef(startTime)
  const counterModeRef = useRef(counterMode)

  const reset = useCallback(() => {
    setElapsedSeconds(0)
  }, [])

  useEffect(() => {
    if (startTimeRef.current !== startTime || counterModeRef.current !== counterMode) {
      startTimeRef.current = startTime
      counterModeRef.current = counterMode
      reset()
    }
  }, [startTime, counterMode, reset])

  useEffect(() => {
    if (!active) {
      return
    }

    const intervalId = window.setInterval(() => {
      setElapsedSeconds((current) => {
        const next = current + tickMs / 1000
        if (loopDuration !== undefined && next >= loopDuration) {
          return 0
        }
        return next
      })
    }, tickMs)

    return () => window.clearInterval(intervalId)
  }, [active, loopDuration, tickMs])

  const elapsed = Math.floor(elapsedSeconds)
  const displaySeconds = displaySecondsAt(counterMode, startSeconds, elapsed)
  const remainingSeconds = Math.max(0, startSeconds - elapsed)
  const display = formatTime(displaySeconds)

  return {
    display,
    remainingSeconds,
    elapsedSeconds,
    displaySeconds,
    reset,
  }
}
