// One cancellable request at a time; hidden workspaces do no background work.
export function startPolling({ load, onData, onError, onLoading, interval, timeout = 15_000, visibility = document }) {
  let stopped = false
  let pending = false
  let timer
  let controller

  async function refresh() {
    if (stopped || pending || visibility.hidden) return
    pending = true
    controller = new AbortController()
    const requestController = controller
    let timedOut = false
    const deadline = setTimeout(() => {
      timedOut = true
      requestController.abort()
    }, timeout)
    onLoading(true)
    try {
      const data = await load(requestController.signal)
      if (!stopped && !requestController.signal.aborted) onData(data)
    } catch (error) {
      if (!stopped && !visibility.hidden && (!requestController.signal.aborted || timedOut)) {
        onError(timedOut ? new Error('Refresh timed out. Please try again.') : error)
      }
    } finally {
      clearTimeout(deadline)
      pending = false
      if (!stopped) {
        onLoading(false)
        if (!visibility.hidden) timer = setTimeout(refresh, interval)
      }
    }
  }

  function onVisibilityChange() {
    clearTimeout(timer)
    if (visibility.hidden) controller?.abort()
    else refresh()
  }

  visibility.addEventListener('visibilitychange', onVisibilityChange)
  refresh()
  return () => {
    stopped = true
    clearTimeout(timer)
    controller?.abort()
    visibility.removeEventListener('visibilitychange', onVisibilityChange)
  }
}
