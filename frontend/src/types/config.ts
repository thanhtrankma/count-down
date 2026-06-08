export type CountdownAnimation =
  | 'none'
  | 'fade'
  | 'scale'
  | 'slide_up'
  | 'flip'
  | 'circle'

export interface RenderStyle {
  font_name: string
  font_id?: string | null
  font_size: number
  color: string
  title_font_size: number
  animation?: CountdownAnimation
  animation_intensity?: number
}

export interface RenderConfig {
  start_time: string
  duration_seconds: number
  resolution: string
  background_color: string
  style: RenderStyle
  title?: string | null
  audio_tick?: boolean
}

export type JobStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'

export interface RenderJob {
  id: string
  status: JobStatus
  progress: number
  config: RenderConfig
  output_path?: string | null
  error?: string | null
}

export interface CreateJobResponse {
  job_id: string
  estimated_size_mb: number
  estimated_render_minutes: number
  warnings?: string[]
}

export type AspectFormat = '16:9' | '9:16' | '1:1'

export interface FormatPreset {
  label: string
  value: AspectFormat
  resolution: string
}

export interface DurationPreset {
  label: string
  seconds: number
}

export const FORMAT_PRESETS: FormatPreset[] = [
  { label: '16:9', value: '16:9', resolution: '1920x1080' },
  { label: '9:16', value: '9:16', resolution: '1080x1920' },
  { label: '1:1', value: '1:1', resolution: '1080x1080' },
]

export const DURATION_PRESETS: DurationPreset[] = [
  { label: '1 min', seconds: 60 },
  { label: '5 min', seconds: 300 },
  { label: '15 min', seconds: 900 },
  { label: '1 hour', seconds: 3600 },
  { label: '3 hours', seconds: 10800 },
  { label: '8 hours', seconds: 28800 },
]

export const DEFAULT_RENDER_CONFIG: RenderConfig = {
  start_time: '01:00:00',
  duration_seconds: 3600,
  resolution: '1920x1080',
  background_color: '#000000',
  style: {
    font_name: 'Arial',
    font_id: null,
    font_size: 120,
    color: '#FFFFFF',
    title_font_size: 48,
    animation: 'none',
    animation_intensity: 1.0,
  },
  title: '',
  audio_tick: false,
}
