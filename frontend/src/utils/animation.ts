import type { CountdownAnimation, CounterMode } from '../types/config'
import timing from '../../../shared/animation_timing.json'

export const ANIMATION_PRESETS: {
  value: CountdownAnimation
  label: string
  icon: string
}[] = [
  { value: 'none', label: 'None', icon: '—' },
  { value: 'fade', label: 'Fade', icon: '◐' },
  { value: 'scale', label: 'Scale', icon: '◎' },
  { value: 'slide_up', label: 'Slide', icon: '↑' },
  { value: 'flip', label: 'Flip', icon: '↻' },
  { value: 'circle', label: 'Circle', icon: '○' },
]

const flipTiming = timing.flip

export function clampIntensity(intensity: number): number {
  return Math.min(flipTiming.intensity_max, Math.max(flipTiming.intensity_min, intensity))
}

/** Base transition from shared/animation_timing.json (higher intensity = snappier). */
export function transitionMs(intensity: number): number {
  return Math.max(
    flipTiming.min_duration_ms,
    Math.round(flipTiming.base_duration_ms / clampIntensity(intensity)),
  )
}

export function circleProgress(
  valueSeconds: number,
  durationSeconds: number,
  counterMode: CounterMode = 'countdown',
): number {
  if (durationSeconds <= 0) {
    return 0
  }
  if (counterMode === 'countup') {
    if (durationSeconds <= 1) {
      return 0
    }
    const elapsed = Math.max(0, Math.floor(valueSeconds))
    return Math.max(0, Math.min(1, elapsed / (durationSeconds - 1)))
  }
  const remaining = Math.max(0, valueSeconds)
  return Math.max(0, Math.min(1, remaining / durationSeconds))
}

export function scalePeak(intensity: number): number {
  return 1 + 0.2 * clampIntensity(intensity)
}

export function slideOffsetPx(intensity: number, fontSize: number): number {
  return Math.round(fontSize * 0.35 * clampIntensity(intensity))
}
