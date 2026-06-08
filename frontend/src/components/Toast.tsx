import { useEffect } from 'react'

interface ToastProps {
  message: string
  variant?: 'error' | 'success' | 'info'
  onDismiss: () => void
  autoDismissMs?: number
}

const VARIANT_STYLES = {
  error: 'border-red-500/50 bg-red-500/15 text-red-200',
  success: 'border-emerald-500/50 bg-emerald-500/15 text-emerald-200',
  info: 'border-indigo-500/50 bg-indigo-500/15 text-indigo-200',
} as const

export default function Toast({
  message,
  variant = 'error',
  onDismiss,
  autoDismissMs = 8000,
}: ToastProps) {
  useEffect(() => {
    const timer = window.setTimeout(onDismiss, autoDismissMs)
    return () => window.clearTimeout(timer)
  }, [autoDismissMs, message, onDismiss])

  return (
    <div
      className="pointer-events-none fixed inset-x-0 top-4 z-50 flex justify-center px-4"
      role="alert"
      aria-live="assertive"
    >
      <div
        className={`pointer-events-auto flex max-w-lg items-start gap-3 rounded-xl border px-4 py-3 text-sm shadow-lg backdrop-blur ${VARIANT_STYLES[variant]}`}
      >
        <p className="flex-1">{message}</p>
        <button
          type="button"
          onClick={onDismiss}
          className="shrink-0 rounded px-1.5 py-0.5 text-xs opacity-70 transition-opacity hover:opacity-100"
          aria-label="Dismiss"
        >
          ✕
        </button>
      </div>
    </div>
  )
}
