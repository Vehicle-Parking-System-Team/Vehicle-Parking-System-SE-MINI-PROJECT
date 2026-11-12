import assert from 'node:assert/strict'
import test from 'node:test'
import { readWorkspaceLocation, workspaceUrl } from '../src/utils/workspaceNavigation.js'

const pages = ['vehicles', 'profiles', 'account', 'availability']

test('bookmarked workspace and vehicle survive reloading the URL', () => {
  const href = 'https://parking.test/?page=profiles&vehicle=42'
  assert.deepEqual(readWorkspaceLocation(href, pages, 'vehicles'), { page: 'profiles', vehicleId: 42 })
  assert.equal(workspaceUrl(href, readWorkspaceLocation(href, pages, 'vehicles')), '/?page=profiles&vehicle=42')
})

test('forbidden and unknown routes fall back before rendering and discard record IDs', () => {
  for (const page of ['users', 'dashboard', 'facility', 'audit', 'unknown', '']) {
    assert.deepEqual(readWorkspaceLocation(`https://parking.test/?page=${page}&vehicle=42`, pages, 'vehicles'), { page: 'vehicles', vehicleId: null })
  }
})

test('navigation preserves unrelated URL state but clears IDs outside profiles', () => {
  assert.equal(workspaceUrl('https://parking.test/app?source=bookmark&vehicle=42#bay-main', { page: 'account', vehicleId: 42 }), '/app?source=bookmark&page=account#bay-main')
})

test('invalid or unsafe vehicle identifiers never reach the profile API', () => {
  for (const id of ['-1', '0', '1.1', 'NaN', '1e3', '9007199254740992', 'x<script>', '']) {
    assert.equal(readWorkspaceLocation(`https://parking.test/?page=profiles&vehicle=${encodeURIComponent(id)}`, pages, 'vehicles').vehicleId, null)
  }
})
