import type { ChangeEvent, FormEvent } from 'react'

import {
  FONT_CATALOG,
  SYSTEM_FONT,
  SYSTEM_FONT_ID,
  applyFontSelection,
  getFontSelectValue,
} from '../fonts'
import {
  DURATION_PRESETS,
  FORMAT_PRESETS,
  type AspectFormat,
  type RenderConfig,
} from '../types/config'
import { ANIMATION_PRESETS } from '../utils/animation'
import { validateRenderConfig } from '../utils/validateConfig'

interface ConfigFormProps {
  config: RenderConfig
  onChange: (config: RenderConfig) => void
  onSubmit: (config: RenderConfig) => void
  onReset: () => void
  isSubmitting?: boolean
  isJobActive?: boolean
}

function getFormatFromResolution(resolution: string): AspectFormat {
  const preset = FORMAT_PRESETS.find((item) => item.resolution === resolution)
  return preset?.value ?? '16:9'
}

function clampNumber(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

export default function ConfigForm({
  config,
  onChange,
  onSubmit,
  onReset,
  isSubmitting = false,
  isJobActive = false,
}: ConfigFormProps) {
  const selectedFormat = getFormatFromResolution(config.resolution)
  const validation = validateRenderConfig(config)
  const canSubmit = validation.valid && !isSubmitting && !isJobActive

  const updateConfig = (patch: Partial<RenderConfig>) => {
    onChange({ ...config, ...patch })
  }

  const updateStyle = (patch: Partial<RenderConfig['style']>) => {
    onChange({
      ...config,
      style: { ...config.style, ...patch },
    })
  }

  const handleFormatChange = (format: AspectFormat) => {
    const preset = FORMAT_PRESETS.find((item) => item.value === format)
    if (preset) {
      updateConfig({ resolution: preset.resolution })
    }
  }

  const handleDurationPreset = (seconds: number) => {
    updateConfig({ duration_seconds: seconds })
  }

  const handleDurationChange = (event: ChangeEvent<HTMLInputElement>) => {
    const value = Number(event.target.value)
    if (!Number.isNaN(value)) {
      updateConfig({ duration_seconds: clampNumber(value, 1, 28800) })
    }
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (canSubmit) {
      onSubmit(config)
    }
  }

  const startTimeError = validation.errors.find((e) => e.includes('Start time'))
  const durationError = validation.errors.find((e) => e.includes('Duration'))
  const bgColorError = validation.errors.find((e) => e.includes('Background'))
  const textColorError = validation.errors.find((e) => e.includes('Text color'))

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white">Configuration</h2>
        <p className="mt-1 text-sm text-gray-400">
          Set countdown duration, appearance, and output format.
        </p>
      </div>

      {!validation.valid && (
        <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm text-amber-200">
          <ul className="list-inside list-disc space-y-0.5">
            {validation.errors.map((error) => (
              <li key={error}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {isJobActive && (
        <div className="rounded-lg border border-indigo-500/40 bg-indigo-500/10 px-3 py-2 text-sm text-indigo-200">
          A render is in progress. Wait for it to finish or cancel before starting another.
        </div>
      )}

      <section className="space-y-3">
        <label className="block text-sm font-medium text-gray-300">
          Duration presets
        </label>
        <div className="flex flex-wrap gap-2">
          {DURATION_PRESETS.map((preset) => (
            <button
              key={preset.seconds}
              type="button"
              onClick={() => handleDurationPreset(preset.seconds)}
              className={`rounded-lg px-3 py-1.5 text-sm transition-colors ${
                config.duration_seconds === preset.seconds
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>
        <div>
          <label htmlFor="duration" className="block text-sm text-gray-400">
            Custom duration (seconds)
          </label>
          <input
            id="duration"
            type="number"
            min={1}
            max={28800}
            value={config.duration_seconds}
            onChange={handleDurationChange}
            className={`mt-1 w-full rounded-lg border bg-gray-900 px-3 py-2 text-white focus:outline-none focus:ring-1 ${
              durationError
                ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                : 'border-gray-700 focus:border-indigo-500 focus:ring-indigo-500'
            }`}
          />
          {durationError && <p className="mt-1 text-sm text-red-400">{durationError}</p>}
        </div>
      </section>

      <section className="space-y-3">
        <label htmlFor="start-time" className="block text-sm font-medium text-gray-300">
          Start time (HH:MM:SS)
        </label>
        <input
          id="start-time"
          type="text"
          value={config.start_time}
          onChange={(event) => updateConfig({ start_time: event.target.value })}
          placeholder="01:00:00"
          className={`w-full rounded-lg border bg-gray-900 px-3 py-2 font-mono text-white focus:outline-none focus:ring-1 ${
            startTimeError
              ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
              : 'border-gray-700 focus:border-indigo-500 focus:ring-indigo-500'
          }`}
        />
        {startTimeError && <p className="text-sm text-red-400">{startTimeError}</p>}
      </section>

      <section className="space-y-3">
        <span className="block text-sm font-medium text-gray-300">Format</span>
        <div className="grid grid-cols-3 gap-2">
          {FORMAT_PRESETS.map((preset) => (
            <button
              key={preset.value}
              type="button"
              onClick={() => handleFormatChange(preset.value)}
              className={`rounded-lg px-3 py-2 text-sm transition-colors ${
                selectedFormat === preset.value
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-500">Resolution: {config.resolution}</p>
      </section>

      <section className="space-y-3">
        <label htmlFor="title" className="block text-sm font-medium text-gray-300">
          Title (optional)
        </label>
        <input
          id="title"
          type="text"
          value={config.title ?? ''}
          onChange={(event) => updateConfig({ title: event.target.value })}
          placeholder="New Year Countdown"
          className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </section>

      <section className="space-y-3">
        <label className="flex cursor-pointer items-center gap-3">
          <input
            type="checkbox"
            checked={config.audio_tick ?? false}
            onChange={(event) => updateConfig({ audio_tick: event.target.checked })}
            className="h-4 w-4 rounded border-gray-600 bg-gray-900 text-indigo-600 focus:ring-indigo-500"
          />
          <span className="text-sm text-gray-300">
            Audio tick each second
          </span>
        </label>
        <p className="text-xs text-gray-500">
          Adds a short beep at every second boundary in the output video.
        </p>
      </section>

      <section className="space-y-3">
        <span className="block text-sm font-medium text-gray-300">Animation style</span>
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
          {ANIMATION_PRESETS.map((preset) => (
            <button
              key={preset.value}
              type="button"
              onClick={() => updateStyle({ animation: preset.value })}
              className={`flex flex-col items-center gap-1 rounded-lg px-2 py-2.5 text-xs transition-colors ${
                (config.style.animation ?? 'none') === preset.value
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              }`}
            >
              <span className="text-base leading-none">{preset.icon}</span>
              <span>{preset.label}</span>
            </button>
          ))}
        </div>
        {(config.style.animation ?? 'none') !== 'none' && (
          <div>
            <label htmlFor="animation-intensity" className="block text-xs text-gray-400">
              Intensity ({(config.style.animation_intensity ?? 1).toFixed(1)})
            </label>
            <input
              id="animation-intensity"
              type="range"
              min={0.5}
              max={1.5}
              step={0.1}
              value={config.style.animation_intensity ?? 1}
              onChange={(event) =>
                updateStyle({ animation_intensity: Number(event.target.value) })
              }
              className="mt-2 w-full accent-indigo-500"
            />
          </div>
        )}
        <p className="text-xs text-gray-500">
          Flip/Circle in rendered video may differ slightly from preview (ASS limitations).
        </p>
      </section>

      <section className="space-y-4 rounded-xl border border-gray-800 bg-gray-900/50 p-4">
        <h3 className="text-sm font-medium text-gray-300">Style</h3>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="bg-color" className="block text-xs text-gray-400">
              Background
            </label>
            <div className="mt-1 flex items-center gap-2">
              <input
                id="bg-color"
                type="color"
                value={
                  /^#[0-9A-Fa-f]{6}$/.test(config.background_color)
                    ? config.background_color
                    : '#000000'
                }
                onChange={(event) =>
                  updateConfig({ background_color: event.target.value.toUpperCase() })
                }
                className="h-9 w-12 cursor-pointer rounded border border-gray-700 bg-transparent"
              />
              <input
                type="text"
                value={config.background_color}
                onChange={(event) => updateConfig({ background_color: event.target.value })}
                className={`flex-1 rounded-lg border bg-gray-900 px-2 py-1.5 font-mono text-xs text-white ${
                  bgColorError ? 'border-red-500' : 'border-gray-700'
                }`}
              />
            </div>
            {bgColorError && <p className="mt-1 text-xs text-red-400">{bgColorError}</p>}
          </div>

          <div>
            <label htmlFor="text-color" className="block text-xs text-gray-400">
              Text color
            </label>
            <div className="mt-1 flex items-center gap-2">
              <input
                id="text-color"
                type="color"
                value={
                  /^#[0-9A-Fa-f]{6}$/.test(config.style.color)
                    ? config.style.color
                    : '#FFFFFF'
                }
                onChange={(event) =>
                  updateStyle({ color: event.target.value.toUpperCase() })
                }
                className="h-9 w-12 cursor-pointer rounded border border-gray-700 bg-transparent"
              />
              <input
                type="text"
                value={config.style.color}
                onChange={(event) => updateStyle({ color: event.target.value })}
                className={`flex-1 rounded-lg border bg-gray-900 px-2 py-1.5 font-mono text-xs text-white ${
                  textColorError ? 'border-red-500' : 'border-gray-700'
                }`}
              />
            </div>
            {textColorError && <p className="mt-1 text-xs text-red-400">{textColorError}</p>}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="font-name" className="block text-xs text-gray-400">
              Font family
            </label>
            <select
              id="font-name"
              value={getFontSelectValue(config.style)}
              onChange={(event) =>
                updateStyle(applyFontSelection(event.target.value))
              }
              className="mt-1 w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
            >
              <option value={SYSTEM_FONT_ID}>{SYSTEM_FONT.label}</option>
              {FONT_CATALOG.map((font) => (
                <option key={font.id} value={font.id}>
                  {font.label}
                </option>
              ))}
            </select>
            {FONT_CATALOG.length === 0 && (
              <p className="mt-1 text-xs text-gray-500">
                Add fonts to <code className="text-gray-400">frontend/font/</code> and{' '}
                <code className="text-gray-400">fonts.json</code> to enable custom fonts.
              </p>
            )}
          </div>

          <div>
            <label htmlFor="font-size" className="block text-xs text-gray-400">
              Countdown font size
            </label>
            <input
              id="font-size"
              type="number"
              min={8}
              max={500}
              value={config.style.font_size}
              onChange={(event) =>
                updateStyle({ font_size: clampNumber(Number(event.target.value), 8, 500) })
              }
              className="mt-1 w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label htmlFor="title-font-size" className="block text-xs text-gray-400">
            Title font size
          </label>
          <input
            id="title-font-size"
            type="number"
            min={8}
            max={300}
            value={config.style.title_font_size}
            onChange={(event) =>
              updateStyle({
                title_font_size: clampNumber(Number(event.target.value), 8, 300),
              })
            }
            className="mt-1 w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
          />
        </div>
      </section>

      <div className="flex flex-wrap gap-3 pt-2">
        <button
          type="submit"
          disabled={!canSubmit}
          className="flex-1 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSubmitting ? 'Submitting…' : 'Generate Video'}
        </button>
        <button
          type="button"
          onClick={onReset}
          className="rounded-lg border border-gray-700 px-4 py-2.5 text-sm text-gray-300 transition-colors hover:bg-gray-800"
        >
          Reset
        </button>
      </div>
    </form>
  )
}
