const FALLBACK_MESSAGE = 'Unable to complete the request. Please try again.'

/** Convert a parsed US-31 error body into form and field messages. */
export function parseApiError(payload) {
  const fallback = {
    message: FALLBACK_MESSAGE,
    code: 'REQUEST_FAILED',
    fieldErrors: {},
    formErrors: [],
  }

  if (
    !payload || typeof payload !== 'object' || Array.isArray(payload) ||
    typeof payload.error !== 'string' || !payload.error.trim() ||
    typeof payload.code !== 'string' || !/^[A-Z][A-Z0-9_]*$/.test(payload.code) ||
    !payload.details || typeof payload.details !== 'object'
  ) {
    return fallback
  }

  const fields = new Map()
  const formErrors = []
  function collect(value, path = '') {
    if (typeof value === 'string' && value.trim()) {
      if (!path) formErrors.push(value)
      else fields.set(path, [...(fields.get(path) ?? []), value])
    } else if (Array.isArray(value)) {
      value.forEach((item, index) => {
        const itemPath = path ? `${path}.${index}` : String(index)
        collect(item, typeof item === 'string' ? path : itemPath)
      })
    } else if (value && typeof value === 'object') {
      Object.entries(value).forEach(([key, item]) => {
        collect(item, key === 'non_field_errors' ? '' : [path, key].filter(Boolean).join('.'))
      })
    }
  }
  collect(payload.details)

  return {
    message: payload.error,
    code: payload.code,
    fieldErrors: Object.fromEntries(fields),
    formErrors,
  }
}
