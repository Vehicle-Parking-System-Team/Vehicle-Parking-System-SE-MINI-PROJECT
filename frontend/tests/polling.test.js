import assert from 'node:assert/strict'
import test from 'node:test'
import { startPolling } from '../src/utils/polling.js'

const flush = async () => { for (let i = 0; i < 8; i++) await Promise.resolve() }

function visibility() {
  const target = new EventTarget()
  target.hidden = false
  target.change = (hidden) => { target.hidden = hidden; target.dispatchEvent(new Event('visibilitychange')) }
  return target
}

test('refreshes sequentially, retains data on error and stops after cleanup', async (t) => {
  t.mock.timers.enable({ apis: ['setTimeout'] })
  let calls = 0
  let resolve
  const rows = [], errors = [], busy = []
  const stop = startPolling({
    load: () => { calls++; return new Promise((done) => { resolve = done }) },
    onData: (data) => rows.push(data), onError: (error) => errors.push(error), onLoading: (value) => busy.push(value),
    interval: 30_000, timeout: 100_000, visibility: visibility(),
  })
  t.mock.timers.tick(60_000)
  assert.equal(calls, 1)
  resolve(['occupied'])
  await flush()
  t.mock.timers.tick(30_000)
  assert.equal(calls, 2)
  stop()
  resolve(['late result'])
  await flush()
  t.mock.timers.tick(100_000)
  assert.deepEqual(rows, [['occupied']])
  assert.deepEqual(errors, [])
  assert.equal(calls, 2)
  assert.deepEqual(busy, [true, false, true])
})

test('hidden tabs abort pending work, resume on visibility and remove listeners on cleanup', async (t) => {
  t.mock.timers.enable({ apis: ['setTimeout'] })
  const document = visibility()
  const signals = [], rows = []
  const stop = startPolling({ load: (signal) => {
    signals.push(signal)
    return new Promise((resolve, reject) => signal.addEventListener('abort', () => reject(new Error('aborted'))))
  }, onData: (data) => rows.push(data), onError: assert.fail, onLoading: () => {}, interval: 30_000, visibility: document })
  document.change(true)
  await flush()
  assert.equal(signals[0].aborted, true)
  t.mock.timers.tick(90_000)
  assert.equal(signals.length, 1)
  document.change(false)
  assert.equal(signals.length, 2)
  stop()
  await flush()
  document.change(false)
  assert.equal(signals.length, 2)
  assert.deepEqual(rows, [])
})

test('timeout reports a stale snapshot error and permits the next refresh', async (t) => {
  t.mock.timers.enable({ apis: ['setTimeout'] })
  const errors = [], rows = []
  let calls = 0
  const stop = startPolling({ load: (signal) => {
    if (++calls > 1) return Promise.resolve(['recovered'])
    return new Promise((resolve, reject) => signal.addEventListener('abort', () => reject(new Error('aborted'))))
  }, onData: (data) => rows.push(data), onError: (error) => errors.push(error), onLoading: () => {}, interval: 30_000, visibility: visibility() })
  t.mock.timers.tick(15_000)
  await flush()
  assert.match(errors[0].message, /timed out/)
  t.mock.timers.tick(30_000)
  await flush()
  assert.deepEqual(rows, [['recovered']])
  stop()
})
