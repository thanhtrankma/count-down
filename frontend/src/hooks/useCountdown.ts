import { useCallback, useEffect, useRef, useState } from 'react'

import { formatTime, tryParseTime } from '../utils/formatTime'

export interface UseCountdownOptions {
  startTime: string
  active?: boolean
  loopDuration?: number
  tickMs?: number
}

export interface UseCountdownResult {
  display: string
  remainingSeconds: number
  elapsedSeconds: number
  reset: () => void
}

export function useCountdown({
  startTime,
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

  const reset = useCallback(() => {
    setElapsedSeconds(0)
  }, [])

  useEffect(() => {
    if (startTimeRef.current !== startTime) {
      startTimeRef.current = startTime
      reset()
    }
  }, [startTime, reset])

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

  const remainingSeconds = Math.max(0, startSeconds - Math.floor(elapsedSeconds))
  const display = formatTime(remainingSeconds)

  return {
    display,
    remainingSeconds,
    elapsedSeconds,
    reset,
  }
}
