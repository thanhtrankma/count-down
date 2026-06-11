import { useState } from 'react'

import type { RenderJob } from '../types/config'

interface ActiveJobsListProps {
  jobs: RenderJob[]
  currentJobId?: string | null
  isLoading?: boolean
  fetchError?: string | null
  onCancel: (jobId: string) => Promise<void>
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

function shortJobId(jobId: string): string {
  return jobId.length > 8 ? `${jobId.slice(0, 8)}…` : jobId
}

export default function ActiveJobsList({
  jobs,
  currentJobId,
  isLoading = false,
  fetchError,
  onCancel,
}: ActiveJobsListProps) {
  const [cancellingId, setCancellingId] = useState<string | null>(null)
  const [cancelError, setCancelError] = useState<string | null>(null)

  if (jobs.length === 0 && !fetchError) {
    return null
  }

  const handleCancel = async (jobId: string) => {
    setCancellingId(jobId)
    setCancelError(null)
    try {
      await onCancel(jobId)
    } catch (err) {
      setCancelError(err instanceof Error ? err.message : 'Failed to cancel job')
    } finally {
      setCancellingId(null)
    }
  }

  return (
    <section className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-white">Active Render Jobs</h2>
          <p className="mt-1 text-sm text-gray-400">
            Only one render can run at a time. Wait for these jobs to finish or cancel them.
          </p>
        </div>
        {isLoading && (
          <span className="text-xs text-gray-500">Updating…</span>
        )}
      </div>

      {fetchError && (
        <p className="mt-3 text-sm text-red-300">{fetchError}</p>
      )}

      {cancelError && (
        <p className="mt-3 text-sm text-red-300">{cancelError}</p>
      )}

      {jobs.length > 0 && (
        <ul className="mt-4 space-y-3">
          {jobs.map((activeJob) => {
            const isCurrent = activeJob.id === currentJobId
            const mode =
              (activeJob.config.counter_mode ?? 'countdown') === 'countup'
                ? 'Count up'
                : 'Count down'

            return (
              <li
                key={activeJob.id}
                className="rounded-lg border border-gray-800 bg-gray-950/60 p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0 space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`text-sm font-medium ${STATUS_COLORS[activeJob.status]}`}
                      >
                        {STATUS_LABELS[activeJob.status]}
                      </span>
                      <span className="font-mono text-xs text-gray-500">
                        {shortJobId(activeJob.id)}
                      </span>
                      {isCurrent && (
                        <span className="rounded-full bg-indigo-500/20 px-2 py-0.5 text-xs text-indigo-300">
                          This session
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-300">
                      {activeJob.config.duration_seconds}s · {activeJob.config.resolution} ·{' '}
                      {mode} · start {activeJob.config.start_time}
                    </p>
                    {activeJob.config.title?.trim() && (
                      <p className="truncate text-xs text-gray-500">
                        Title: {activeJob.config.title.trim()}
                      </p>
                    )}
                  </div>

                  <div className="flex shrink-0 flex-col items-end gap-2">
                    <span className="font-mono text-sm text-gray-400">
                      {activeJob.progress.toFixed(0)}%
                    </span>
                    <button
                      type="button"
                      onClick={() => void handleCancel(activeJob.id)}
                      disabled={cancellingId === activeJob.id}
                      className="rounded-lg border border-red-500/50 px-3 py-1.5 text-sm text-red-300 transition-colors hover:bg-red-500/10 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {cancellingId === activeJob.id ? 'Cancelling…' : 'Cancel'}
                    </button>
                  </div>
                </div>

                <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-gray-800">
                  <div
                    className="h-full rounded-full bg-indigo-500 transition-all duration-500"
                    style={{
                      width: `${Math.min(100, Math.max(0, activeJob.progress))}%`,
                    }}
                  />
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
