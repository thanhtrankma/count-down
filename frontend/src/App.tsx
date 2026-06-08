import { useCallback, useEffect, useState } from 'react'

import ConfigForm from './components/ConfigForm'
import PreviewPlayer from './components/PreviewPlayer'
import RenderProgress from './components/RenderProgress'
import Toast from './components/Toast'
import { usePersistedConfig } from './hooks/usePersistedConfig'
import { useRenderJob } from './hooks/useRenderJob'
import type { RenderConfig } from './types/config'
import { isLongRender } from './utils/validateConfig'

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

  const [toastMessage, setToastMessage] = useState<string | null>(null)

  const isJobActive =
    isSubmitting ||
    isPolling ||
    job?.status === 'pending' ||
    job?.status === 'running'

  const showToast = useCallback((message: string) => {
    setToastMessage(message)
  }, [])

  useEffect(() => {
    if (error) {
      showToast(error)
    }
  }, [error, showToast])

  useEffect(() => {
    if (warnings.length > 0) {
      showToast(warnings.join(' '))
    }
  }, [warnings, showToast])

  useEffect(() => {
    if (job?.status === 'failed' && job.error) {
      showToast(job.error)
    }
  }, [job?.status, job?.error, showToast])

  useEffect(() => {
    if (job?.status === 'completed') {
      showToast('Render completed — download your video below.')
    }
  }, [job?.status, showToast])

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

    void submitRender(nextConfig)
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {toastMessage && (
        <Toast
          message={toastMessage}
          variant={
            job?.status === 'completed' && !error
              ? 'success'
              : error || job?.error
                ? 'error'
                : 'info'
          }
          onDismiss={() => setToastMessage(null)}
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

        <div className="mt-6">
          <RenderProgress
            job={job}
            jobId={jobId}
            estimates={estimates}
            isSubmitting={isSubmitting}
            isPolling={isPolling}
            error={error}
            onCancel={() => void cancelJob()}
            onClear={clearJob}
          />
        </div>
      </main>
    </div>
  )
}

export default App
