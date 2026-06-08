const TIME_PATTERN = /^(\d{2}):(\d{2}):(\d{2})$/

export function tryParseTime(timeStr: string): number | null {
  const match = TIME_PATTERN.exec(timeStr)
  if (!match) {
    return null
  }

  const hours = Number(match[1])
  const minutes = Number(match[2])
  const seconds = Number(match[3])

  if (minutes >= 60 || seconds >= 60) {
    return null
  }

  return hours * 3600 + minutes * 60 + seconds
}

export function parseTime(timeStr: string): number {
  const result = tryParseTime(timeStr)
  if (result === null) {
    throw new Error(`Invalid time format: ${timeStr}`)
  }
  return result
}

export function formatTime(totalSeconds: number): string {
  const seconds = Math.max(0, Math.floor(totalSeconds))
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

export function isValidTimeString(timeStr: string): boolean {
  return tryParseTime(timeStr) !== null
}

export function parseResolution(resolution: string): { width: number; height: number } {
  const match = /^(\d{3,5})x(\d{3,5})$/.exec(resolution)
  if (!match) {
    return { width: 1920, height: 1080 }
  }
  return { width: Number(match[1]), height: Number(match[2]) }
}
