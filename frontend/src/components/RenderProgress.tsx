import { apiUrl } from '../config/api'
import type { CreateJobResponse, RenderJob } from '../types/config'

interface RenderProgressProps {
  job: RenderJob | null
  jobId: string | null
  estimates: Pick<CreateJobResponse, 'estimated_size_mb' | 'estimated_render_minutes'> | null
  isSubmitting: boolean
  isPolling: boolean
  error: string | null
  onCancel: () => void
  onClear: () => void
}

const STATUS_LABELS: Record<RenderJob['status'], string> = {
  pending: 'Queued',
  running: 'Rendering',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
}

const STATUS_COLORS: Record<RenderJob['status'], string> = {
  pending: 'text-amber-400',
  running: 'text-indigo-400',
  completed: 'text-emerald-400',
  failed: 'text-red-400',
  cancelled: 'text-gray-400',
}

function formatEstimate(value: number, unit: string): string {
  if (value < 1) {
    return `< 1 ${unit}`
  }
  return `~${value.toFixed(1)} ${unit}`
}

export default function RenderProgress({
  job,
  jobId,
  estimates,
  isSubmitting,
  isPolling,
  error,
  onCancel,
  onClear,
}: RenderProgressProps) {
  const isActive = job?.status === 'pending' || job?.status === 'running'
  const canDownload = job?.status === 'completed' && jobId
  const showPanel = isSubmitting || jobId || error

  if (!showPanel) {
    return null
  }

  const progress = job?.progress ?? 0
  const status = job?.status ?? (isSubmitting ? 'pending' : 'pending')

  return (
    <section className="rounded-xl border border-gray-800 bg-gray-900/70 p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-white">Render Progress</h2>
          {jobId && (
            <p className="mt-1 font-mono text-xs text-gray-500">Job {jobId}</p>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {isActive && (
            <button
              type="button"
              onClick={onCancel}
              className="rounded-lg border border-red-500/50 px-3 py-1.5 text-sm text-red-300 transition-colors hover:bg-red-500/10"
            >
              Cancel
            </button>
          )}
          {canDownload && (
            <a
              href={apiUrl(`/api/jobs/${jobId}/download`)}
              download
              className="rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-emerald-500"
            >
              Download MP4
            </a>
          )}
          {(job?.status === 'completed' ||
            job?.status === 'failed' ||
            job?.status === 'cancelled') && (
            <button
              type="button"
              onClick={onClear}
              className="rounded-lg border border-gray-700 px-3 py-1.5 text-sm text-gray-300 transition-colors hover:bg-gray-800"
            >
              Dismiss
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mt-4 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {job?.error && (
        <div className="mt-4 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {job.error}
        </div>
      )}

      <div className="mt-4 space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span className={`font-medium ${STATUS_COLORS[status]}`}>
            {isSubmitting && !job ? 'Submitting…' : STATUS_LABELS[status]}
          </span>
          <span className="font-mono text-gray-400">{progress.toFixed(0)}%</span>
        </div>

        <div className="h-2 overflow-hidden rounded-full bg-gray-800">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              job?.status === 'failed'
                ? 'bg-red-500'
                : job?.status === 'completed'
                  ? 'bg-emerald-500'
                  : 'bg-indigo-500'
            }`}
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>

        {(isPolling || isSubmitting) && !job?.error && (
          <p className="text-xs text-gray-500">
            {isPolling ? 'Polling for updates…' : 'Starting render job…'}
          </p>
        )}
      </div>

      {estimates && (
        <dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <div className="rounded-lg bg-gray-950/60 px-3 py-2">
            <dt className="text-xs text-gray-500">Est. file size</dt>
            <dd className="mt-0.5 text-gray-200">
              {formatEstimate(estimates.estimated_size_mb, 'MB')}
            </dd>
          </div>
          <div className="rounded-lg bg-gray-950/60 px-3 py-2">
            <dt className="text-xs text-gray-500">Est. render time</dt>
            <dd className="mt-0.5 text-gray-200">
              {formatEstimate(estimates.estimated_render_minutes, 'min')}
            </dd>
          </div>
          {job && (
            <>
              <div className="rounded-lg bg-gray-950/60 px-3 py-2">
                <dt className="text-xs text-gray-500">Duration</dt>
                <dd className="mt-0.5 text-gray-200">
                  {job.config.duration_seconds}s
                </dd>
              </div>
              <div className="rounded-lg bg-gray-950/60 px-3 py-2">
                <dt className="text-xs text-gray-500">Resolution</dt>
                <dd className="mt-0.5 text-gray-200">{job.config.resolution}</dd>
              </div>
            </>
          )}
        </dl>
      )}
    </section>
  )
}
