import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../context/useAuth'
import BayIcon from '../components/BayIcon'

const API_BASE = '/api/auth/users'

export default function UsersPage() {
  const { user: currentUser, accessToken } = useAuth()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)

  // Filters
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  // Create Modal State
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [createForm, setCreateForm] = useState({
    username: '',
    email: '',
    password: '',
    role: 'Operator',
  })
  const [formError, setFormError] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const fetchUsers = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (search) params.append('search', search)
      if (roleFilter) params.append('role', roleFilter)
      if (statusFilter) params.append('status', statusFilter)

      const token = accessToken || localStorage.getItem('vps_access_token')
      const response = await fetch(`${API_BASE}/?${params.toString()}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      const data = await response.json().catch(() => [])
      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch user accounts.')
      }
      setUsers(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [search, roleFilter, statusFilter, accessToken])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  const handleCreateSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setIsSubmitting(true)

    try {
      const token = accessToken || localStorage.getItem('vps_access_token')
      const response = await fetch(`${API_BASE}/`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(createForm),
      })

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        if (response.status === 409) {
          const conflictMsg =
            data.details?.username || data.details?.email || data.error || 'Account conflict: user already exists.'
          throw new Error(conflictMsg)
        }
        if (data.details) {
          const detailMsgs = Object.values(data.details).flat().join(' ')
          throw new Error(detailMsgs || data.error || 'Validation error.')
        }
        throw new Error(data.error || 'Failed to create user account.')
      }

      setSuccessMessage(`Account created successfully for ${data.username}.`)
      setIsModalOpen(false)
      setCreateForm({ username: '', email: '', password: '', role: 'Operator' })
      fetchUsers()
    } catch (err) {
      setFormError(err.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleStatusToggle = async (targetUser) => {
    if (targetUser.id === currentUser?.id) {
      setError('Administrators cannot suspend or deactivate their own account.')
      return
    }

    const nextStatus = targetUser.status === 'active' ? 'suspended' : 'active'
    setError(null)
    setSuccessMessage(null)

    try {
      const token = accessToken || localStorage.getItem('vps_access_token')
      const response = await fetch(`${API_BASE}/${targetUser.id}/`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: nextStatus }),
      })

      const data = await response.json().catch(() => ({}))
      if (!response.ok) {
        throw new Error(data.error || 'Failed to update account status.')
      }

      setSuccessMessage(`Account ${targetUser.username} is now ${nextStatus}.`)
      fetchUsers()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="bay-users-page" style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <span className="bay-eyebrow">ADMINISTRATION</span>
          <h1 style={{ margin: '4px 0 0', fontSize: '28px' }}>User Account Management</h1>
        </div>
        <button
          type="button"
          className="bay-button bay-button-primary"
          onClick={() => {
            setIsModalOpen(true)
            setFormError(null)
          }}
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <BayIcon name="plus" size={16} />
          Create user account
        </button>
      </header>

      {successMessage && (
        <div style={{ padding: '12px 16px', background: '#e6f4ea', color: '#137333', borderRadius: '8px', marginBottom: '16px' }}>
          {successMessage}
        </div>
      )}

      {error && (
        <div style={{ padding: '12px 16px', background: '#fce8e6', color: '#c5221f', borderRadius: '8px', marginBottom: '16px' }}>
          {error}
        </div>
      )}

      {/* Filters Bar */}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '20px' }}>
        <input
          type="text"
          placeholder="Search by username or email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: '1', minWidth: '220px', padding: '8px 12px', borderRadius: '6px', border: '1px solid #d8dee8' }}
        />
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #d8dee8' }}
        >
          <option value="">All Roles</option>
          <option value="Admin">Admin</option>
          <option value="Operator">Operator</option>
          <option value="Customer">Customer</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #d8dee8' }}
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
          <option value="deactivated">Deactivated</option>
        </select>
      </div>

      {/* Users Table */}
      {loading ? (
        <p>Loading user accounts...</p>
      ) : users.length === 0 ? (
        <div style={{ padding: '32px', textAlign: 'center', background: '#fff', borderRadius: '8px', border: '1px solid #e1e4e8' }}>
          <p style={{ margin: 0, color: '#596579' }}>No user accounts found matching the criteria.</p>
        </div>
      ) : (
        <div style={{ overflowX: 'auto', background: '#fff', borderRadius: '8px', border: '1px solid #e1e4e8' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #e1e4e8', background: '#f8fafc' }}>
                <th style={{ padding: '12px 16px' }}>Username</th>
                <th style={{ padding: '12px 16px' }}>Email</th>
                <th style={{ padding: '12px 16px' }}>Role</th>
                <th style={{ padding: '12px 16px' }}>Status</th>
                <th style={{ padding: '12px 16px' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const isSelf = u.id === currentUser?.id
                return (
                  <tr key={u.id} style={{ borderBottom: '1px solid #edf2f7' }}>
                    <td style={{ padding: '12px 16px', fontWeight: '500' }}>
                      {u.username} {isSelf && <span style={{ fontSize: '11px', color: '#596579' }}>(You)</span>}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#596579' }}>{u.email}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          background: u.role === 'Admin' ? '#e8f0fe' : u.role === 'Operator' ? '#fef7e0' : '#f1f3f4',
                          color: u.role === 'Admin' ? '#1a73e8' : u.role === 'Operator' ? '#b06000' : '#3c4043',
                        }}
                      >
                        {u.role}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          background: u.status === 'active' ? '#e6f4ea' : '#fce8e6',
                          color: u.status === 'active' ? '#137333' : '#c5221f',
                        }}
                      >
                        {u.status}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      {!isSelf && (
                        <button
                          type="button"
                          onClick={() => handleStatusToggle(u)}
                          style={{
                            padding: '4px 10px',
                            fontSize: '12px',
                            cursor: 'pointer',
                            borderRadius: '4px',
                            border: '1px solid #d8dee8',
                            background: u.status === 'active' ? '#fff5f5' : '#f0fff4',
                            color: u.status === 'active' ? '#c5221f' : '#137333',
                          }}
                        >
                          {u.status === 'active' ? 'Suspend' : 'Activate'}
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal for Creating User */}
      {isModalOpen && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div style={{ background: '#fff', borderRadius: '8px', padding: '24px', width: '100%', maxWidth: '440px' }}>
            <h2 style={{ marginTop: 0, fontSize: '20px' }}>Create User Account</h2>

            {formError && (
              <div style={{ padding: '10px 14px', background: '#fce8e6', color: '#c5221f', borderRadius: '6px', marginBottom: '14px', fontSize: '13px' }}>
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateSubmit}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 'bold', marginBottom: '4px' }}>Username</label>
                <input
                  type="text"
                  required
                  value={createForm.username}
                  onChange={(e) => setCreateForm({ ...createForm, username: e.target.value })}
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 'bold', marginBottom: '4px' }}>Email</label>
                <input
                  type="email"
                  required
                  value={createForm.email}
                  onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 'bold', marginBottom: '4px' }}>Password</label>
                <input
                  type="password"
                  required
                  value={createForm.password}
                  onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
                  placeholder="Min 8 chars, 1 uppercase, 1 digit, 1 symbol"
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 'bold', marginBottom: '4px' }}>Role</label>
                <select
                  value={createForm.role}
                  onChange={(e) => setCreateForm({ ...createForm, role: e.target.value })}
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc', boxSizing: 'border-box' }}
                >
                  <option value="Operator">Operator</option>
                  <option value="Customer">Customer</option>
                  <option value="Admin">Administrator</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  style={{ padding: '8px 16px', borderRadius: '4px', border: '1px solid #ccc', background: '#fff', cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="bay-button bay-button-primary"
                  style={{ padding: '8px 16px', cursor: 'pointer' }}
                >
                  {isSubmitting ? 'Creating...' : 'Create Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
