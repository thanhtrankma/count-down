import { useCallback, useEffect, useRef, useState } from 'react'

import { apiUrl } from '../config/api'
import type { CreateJobResponse, RenderConfig, RenderJob } from '../types/config'

const POLL_INTERVAL_MS = 1500

interface RawCreateJobResponse {
  job_id?: string
  jobId?: string
  estimated_size_mb?: number
  estimatedSizeMb?: number
  estimated_render_minutes?: number
  estimatedRenderMinutes?: number
  warnings?: string[]
}

function normalizeCreateJobResponse(raw: RawCreateJobResponse): CreateJobResponse {
  return {
    job_id: raw.job_id ?? raw.jobId ?? '',
    estimated_size_mb: raw.estimated_size_mb ?? raw.estimatedSizeMb ?? 0,
    estimated_render_minutes:
      raw.estimated_render_minutes ?? raw.estimatedRenderMinutes ?? 0,
    warnings: raw.warnings ?? [],
  }
}

export interface UseRenderJobResult {
  job: RenderJob | null
  jobId: string | null
  estimates: Pick<CreateJobResponse, 'estimated_size_mb' | 'estimated_render_minutes'> | null
  warnings: string[]
  isSubmitting: boolean
  isPolling: boolean
  error: string | null
  submitRender: (config: RenderConfig) => Promise<void>
  cancelJob: () => Promise<void>
  clearJob: () => void
}

export function useRenderJob(): UseRenderJobResult {
  const [job, setJob] = useState<RenderJob | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const [estimates, setEstimates] = useState<
    Pick<CreateJobResponse, 'estimated_size_mb' | 'estimated_render_minutes'> | null
  >(null)
  const [warnings, setWarnings] = useState<string[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isPolling, setIsPolling] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pollTimerRef = useRef<number | null>(null)

  const clearPollTimer = useCallback(() => {
    if (pollTimerRef.current !== null) {
      window.clearInterval(pollTimerRef.current)
      pollTimerRef.current = null
    }
    setIsPolling(false)
  }, [])

  const pollJob = useCallback(
    async (id: string) => {
      const response = await fetch(apiUrl(`/api/jobs/${id}`))
      if (!response.ok) {
        throw new Error(`Failed to fetch job status (${response.status})`)
      }

      const nextJob = (await response.json()) as RenderJob
      setJob(nextJob)

      if (
        nextJob.status === 'completed' ||
        nextJob.status === 'failed' ||
        nextJob.status === 'cancelled'
      ) {
        clearPollTimer()
      }

      return nextJob
    },
    [clearPollTimer],
  )

  const submitRender = useCallback(
    async (config: RenderConfig) => {
      setIsSubmitting(true)
      setError(null)
      clearPollTimer()
      setJob(null)
      setJobId(null)
      setEstimates(null)
      setWarnings([])

      try {
        const response = await fetch(apiUrl('/api/render'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...config,
            title: config.title?.trim() ? config.title.trim() : null,
          }),
        })

        if (!response.ok) {
          const detail = await response.text()
          let message = detail || `Render request failed (${response.status})`
          try {
            const parsed = JSON.parse(detail) as { detail?: string }
            if (parsed.detail) {
              message = parsed.detail
            }
          } catch {
            // keep raw detail text
          }
          throw new Error(message)
        }

        const created = normalizeCreateJobResponse(
          (await response.json()) as RawCreateJobResponse,
        )

        if (!created.job_id) {
          throw new Error('Server did not return a job id')
        }

        setJobId(created.job_id)
        setEstimates({
          estimated_size_mb: created.estimated_size_mb,
          estimated_render_minutes: created.estimated_render_minutes,
        })
        setWarnings(created.warnings ?? [])

        setIsPolling(true)
        await pollJob(created.job_id)

        pollTimerRef.current = window.setInterval(() => {
          void pollJob(created.job_id).catch((pollError: unknown) => {
            setError(
              pollError instanceof Error ? pollError.message : 'Polling failed',
            )
            clearPollTimer()
          })
        }, POLL_INTERVAL_MS)
      } catch (submitError) {
        setError(
          submitError instanceof Error
            ? submitError.message
            : 'Failed to submit render job',
        )
      } finally {
        setIsSubmitting(false)
      }
    },
    [clearPollTimer, pollJob],
  )

  const cancelJob = useCallback(async () => {
    if (!jobId) {
      return
    }

    setError(null)

    try {
      const response = await fetch(apiUrl(`/api/jobs/${jobId}`), {
        method: 'DELETE',
      })

      if (!response.ok) {
        const detail = await response.text()
        throw new Error(detail || `Cancel failed (${response.status})`)
      }

      await pollJob(jobId)
      clearPollTimer()
    } catch (cancelError) {
      setError(
        cancelError instanceof Error ? cancelError.message : 'Failed to cancel job',
      )
    }
  }, [clearPollTimer, jobId, pollJob])

  const clearJob = useCallback(() => {
    clearPollTimer()
    setJob(null)
    setJobId(null)
    setEstimates(null)
    setWarnings([])
    setError(null)
  }, [clearPollTimer])

  useEffect(() => {
    return () => clearPollTimer()
  }, [clearPollTimer])

  return {
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
  }
}
