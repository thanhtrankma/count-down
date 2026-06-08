import type { CountdownAnimation } from '../types/config'

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

export function clampIntensity(intensity: number): number {
  return Math.min(1.5, Math.max(0.5, intensity))
}

/** Base transition ~350ms, scaled by intensity (higher = snappier). */
export function transitionMs(intensity: number): number {
  return Math.max(150, Math.round(350 / clampIntensity(intensity)))
}

export function circleProgress(remainingSeconds: number, durationSeconds: number): number {
  if (durationSeconds <= 0) {
    return 0
  }
  const remaining = Math.max(0, remainingSeconds)
  return Math.max(0, Math.min(1, remaining / durationSeconds))
}

export function scalePeak(intensity: number): number {
  return 1 + 0.2 * clampIntensity(intensity)
}

export function slideOffsetPx(intensity: number, fontSize: number): number {
  return Math.round(fontSize * 0.35 * clampIntensity(intensity))
}
