import { tryParseTime } from './formatTime'

export type CounterMode = 'countdown' | 'countup'

export const MAX_DISPLAY_SECONDS = 99 * 3600 + 59 * 60 + 59

export function displaySecondsAt(
  counterMode: CounterMode,
  startSeconds: number,
  secondIndex: number,
): number {
  if (counterMode === 'countup') {
    return startSeconds + secondIndex
  }
  return Math.max(0, startSeconds - secondIndex)
}

export function prevDisplaySecondsAt(
  counterMode: CounterMode,
  startSeconds: number,
  secondIndex: number,
): number {
  if (secondIndex <= 0) {
    return displaySecondsAt(counterMode, startSeconds, secondIndex)
  }
  return displaySecondsAt(counterMode, startSeconds, secondIndex - 1)
}

export function validateCountupRange(startSeconds: number, durationSeconds: number): string | null {
  if (startSeconds + (durationSeconds - 1) > MAX_DISPLAY_SECONDS) {
    return 'Count up would exceed 99:59:59'
  }
  return null
}

export function validateCountupRangeFromStartTime(
  startTime: string,
  durationSeconds: number,
): string | null {
  const startSeconds = tryParseTime(startTime)
  if (startSeconds === null) {
    return null
  }
  return validateCountupRange(startSeconds, durationSeconds)
}
