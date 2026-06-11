import type { RenderConfig } from '../types/config'
import { validateCountupRangeFromStartTime } from './counterLabel'
import { isValidTimeString } from './formatTime'

const HEX_COLOR_PATTERN = /^#[0-9A-Fa-f]{6}$/
const RESOLUTION_PATTERN = /^(\d{3,5})x(\d{3,5})$/

export const MAX_DURATION_SECONDS = 28800
export const LONG_RENDER_THRESHOLD_SECONDS = 3600

export interface ConfigValidationResult {
  valid: boolean
  errors: string[]
}

export function validateRenderConfig(config: RenderConfig): ConfigValidationResult {
  const errors: string[] = []

  if (!isValidTimeString(config.start_time)) {
    errors.push('Start time must be HH:MM:SS')
  }

  if ((config.counter_mode ?? 'countdown') === 'countup') {
    const countupError = validateCountupRangeFromStartTime(
      config.start_time,
      config.duration_seconds,
    )
    if (countupError) {
      errors.push(countupError)
    }
  }

  if (
    !Number.isInteger(config.duration_seconds) ||
    config.duration_seconds < 1 ||
    config.duration_seconds > MAX_DURATION_SECONDS
  ) {
    errors.push(`Duration must be between 1 and ${MAX_DURATION_SECONDS} seconds`)
  }

  if (!RESOLUTION_PATTERN.test(config.resolution)) {
    errors.push('Resolution must be WIDTHxHEIGHT')
  }

  if (!HEX_COLOR_PATTERN.test(config.background_color)) {
    errors.push('Background color must be #RRGGBB')
  }

  if (!HEX_COLOR_PATTERN.test(config.style.color)) {
    errors.push('Text color must be #RRGGBB')
  }

  if (config.style.font_size < 8 || config.style.font_size > 500) {
    errors.push('Countdown font size must be 8–500')
  }

  if (config.style.title_font_size < 8 || config.style.title_font_size > 300) {
    errors.push('Title font size must be 8–300')
  }

  const intensity = config.style.animation_intensity ?? 1
  if (intensity < 0.5 || intensity > 1.5) {
    errors.push('Animation intensity must be 0.5–1.5')
  }

  return { valid: errors.length === 0, errors }
}

export function isLongRender(durationSeconds: number): boolean {
  return durationSeconds > LONG_RENDER_THRESHOLD_SECONDS
}
