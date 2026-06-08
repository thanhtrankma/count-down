class ConcurrentJobLimitError(Exception):
    """Raised when a new render is requested while another job is active."""
