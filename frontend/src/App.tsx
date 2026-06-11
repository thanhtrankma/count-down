import { useState } from 'react'

import ActiveJobsList from './components/ActiveJobsList'
import ConfigForm from './components/ConfigForm'
import PreviewPlayer from './components/PreviewPlayer'
import RenderProgress from './components/RenderProgress'
import Toast from './components/Toast'
import { useActiveJobs } from './hooks/useActiveJobs'
import { usePersistedConfig } from './hooks/usePersistedConfig'
import { useRenderJob } from './hooks/useRenderJob'
import type { RenderConfig, RenderJob } from './types/config'
import { isLongRender } from './utils/validateConfig'

type ToastVariant = 'error' | 'success' | 'info'

interface ToastNotification {
  key: string
  message: string
  variant: ToastVariant
}

function getToastNotification(
  error: string | null,
  warnings: string[],
  job: RenderJob | null,
): ToastNotification | null {
  if (error) {
    return { key: `error:${error}`, message: error, variant: 'error' }
  }
  if (job?.status === 'failed' && job.error) {
    return { key: `job-failed:${job.error}`, message: job.error, variant: 'error' }
  }
  if (job?.status === 'completed') {
    return {
      key: `job-completed:${job.id}`,
      message: 'Render completed — download video and thumbnail below.',
      variant: 'success',
    }
  }
  if (warnings.length > 0) {
    const message = warnings.join(' ')
    return { key: `warnings:${message}`, message, variant: 'info' }
  }
  return null
}

function formatDurationLabel(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0 && minutes > 0) {
    return `${hours}h ${minutes}m`
  }
  if (hours > 0) {
    return `${hours} hour${hours === 1 ? '' : 's'}`
  }
  return `${minutes} minute${minutes === 1 ? '' : 's'}`
}

function App() {
  const { config, setConfig, resetConfig } = usePersistedConfig()
  const {
    job,
    jobId,
    estimates,
    warnings,
    isSubmitting,
    isPolling,
    error,
    submitRender,
    cancelJob,
    clearJob,
  } = useRenderJob()
  const { activeJobs, isLoading: isLoadingActiveJobs, fetchError: activeJobsError, cancelJob: cancelActiveJob, refresh: refreshActiveJobs } =
    useActiveJobs(true)

  const [dismissedToastKey, setDismissedToastKey] = useState<string | null>(null)
  const toastNotification = getToastNotification(error, warnings, job)
  const activeToast =
    toastNotification && toastNotification.key !== dismissedToastKey
      ? toastNotification
      : null

  const ownsActiveJob =
    jobId != null &&
    activeJobs.some(
      (activeJob) =>
        activeJob.id === jobId &&
        (activeJob.status === 'pending' || activeJob.status === 'running'),
    )

  const isJobActive =
    isSubmitting ||
    isPolling ||
    job?.status === 'pending' ||
    job?.status === 'running' ||
    (activeJobs.length > 0 && !ownsActiveJob)

  const handleSubmit = (nextConfig: RenderConfig) => {
    if (isLongRender(nextConfig.duration_seconds)) {
      const label = formatDurationLabel(nextConfig.duration_seconds)
      const confirmed = window.confirm(
        `This render is ${label} (${nextConfig.duration_seconds}s) and may take a while.\n\nContinue?`,
      )
      if (!confirmed) {
        return
      }
    }

    void submitRender(nextConfig).finally(() => refreshActiveJobs())
  }

  const handleCancelJob = async () => {
    await cancelJob()
    await refreshActiveJobs()
  }

  const handleCancelActiveJob = async (id: string) => {
    await cancelActiveJob(id)
    if (id === jobId) {
      clearJob()
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {activeToast && (
        <Toast
          message={activeToast.message}
          variant={activeToast.variant}
          onDismiss={() => setDismissedToastKey(activeToast.key)}
        />
      )}

      <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white sm:text-2xl">
              COUNTDOWN
            </h1>
            <p className="text-sm text-gray-400">Video Generator</p>
          </div>
          <span className="rounded-full border border-gray-800 bg-gray-900 px-3 py-1 text-xs text-gray-400">
            Phase 4
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="grid gap-6 lg:grid-cols-2 lg:gap-8">
          <section className="rounded-xl border border-gray-800 bg-gray-900/40 p-5 sm:p-6">
            <ConfigForm
              config={config}
              onChange={setConfig}
              onSubmit={handleSubmit}
              onReset={resetConfig}
              isSubmitting={isSubmitting}
              isJobActive={isJobActive}
            />
          </section>

          <section className="rounded-xl border border-gray-800 bg-gray-900/40 p-5 sm:p-6 lg:min-h-[520px]">
            <PreviewPlayer config={config} />
          </section>
        </div>

        {((activeJobs.length > 0 && !ownsActiveJob) || activeJobsError) && (
          <div className="mt-6">
            <ActiveJobsList
              jobs={activeJobs}
              currentJobId={jobId}
              isLoading={isLoadingActiveJobs}
              fetchError={activeJobsError}
              onCancel={handleCancelActiveJob}
            />
          </div>
        )}

        <div className="mt-6">
          <RenderProgress
            job={job}
            jobId={jobId}
            estimates={estimates}
            isSubmitting={isSubmitting}
            isPolling={isPolling}
            error={error}
            onCancel={() => void handleCancelJob()}
            onClear={clearJob}
          />
        </div>
      </main>
    </div>
  )
}

export default App
