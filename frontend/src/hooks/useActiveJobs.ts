import { useCallback, useEffect, useState } from 'react'

import { apiUrl } from '../config/api'
import type { RenderJob } from '../types/config'

export interface UseActiveJobsResult {
  activeJobs: RenderJob[]
  isLoading: boolean
  fetchError: string | null
  refresh: () => Promise<void>
  cancelJob: (jobId: string) => Promise<void>
}

export function useActiveJobs(enabled = true): UseActiveJobsResult {
  const [activeJobs, setActiveJobs] = useState<RenderJob[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)

  const loadActiveJobs = useCallback(async (showLoading: boolean) => {
    if (showLoading) {
      setIsLoading(true)
    }
    try {
      const response = await fetch(apiUrl('/api/jobs/active'))
      if (!response.ok) {
        throw new Error(`Failed to fetch active jobs (${response.status})`)
      }
      const data = (await response.json()) as { jobs: RenderJob[] }
      setActiveJobs(data.jobs ?? [])
      setFetchError(null)
    } catch (err) {
      setFetchError(err instanceof Error ? err.message : 'Failed to fetch active jobs')
    } finally {
      if (showLoading) {
        setIsLoading(false)
      }
    }
  }, [])

  const refresh = useCallback(() => loadActiveJobs(true), [loadActiveJobs])

  const cancelJob = useCallback(
    async (jobId: string) => {
      const response = await fetch(apiUrl(`/api/jobs/${jobId}`), { method: 'DELETE' })
      if (!response.ok) {
        const detail = await response.text()
        throw new Error(detail || `Cancel failed (${response.status})`)
      }
      await refresh()
    },
    [refresh],
  )

  useEffect(() => {
    if (!enabled) {
      return
    }

    const timer = window.setTimeout(() => {
      void loadActiveJobs(false)
    }, 0)

    return () => {
      window.clearTimeout(timer)
    }
  }, [enabled, loadActiveJobs])

  return { activeJobs, isLoading, fetchError, refresh, cancelJob }
}
