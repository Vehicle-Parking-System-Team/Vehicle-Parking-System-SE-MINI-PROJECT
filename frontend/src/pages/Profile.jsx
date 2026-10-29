import { useState, useEffect } from 'react'
import { useAuth } from '../context/useAuth'
import BayIcon from '../components/BayIcon'
import {
  validateProfileUpdateInput,
  validatePasswordChangeInput,
} from '../utils/profileValidation'

export default function ProfilePage() {
  const { user, updateUser, fetchWithAuth, logout, isLoading: authLoading } = useAuth()

  // Profile fields state
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [email, setEmail] = useState('')

  // Form states
  const [profileSaving, setProfileSaving] = useState(false)
  const [profileSuccess, setProfileSuccess] = useState('')
  const [profileErrors, setProfileErrors] = useState({})
  const [profileGeneralError, setProfileGeneralError] = useState('')

  // Password fields state
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('')
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  // Password change states
  const [passwordSaving, setPasswordSaving] = useState(false)
  const [passwordSuccess, setPasswordSuccess] = useState('')
  const [passwordErrors, setPasswordErrors] = useState({})
  const [passwordGeneralError, setPasswordGeneralError] = useState('')

  // Populate from current user on load or change
  useEffect(() => {
    if (user) {
      setFirstName(user.first_name || '')
      setLastName(user.last_name || '')
      setPhoneNumber(user.phone_number || user.contact_number || '')
      setEmail(user.email || '')
    }
  }, [user])

  // Fetch fresh profile details from API
  useEffect(() => {
    let isMounted = true
    const fetchLatestProfile = async () => {
      try {
        const res = await fetchWithAuth('/api/auth/profile/')
        if (res.ok) {
          const data = await res.json()
          if (isMounted) {
            setFirstName(data.first_name || '')
            setLastName(data.last_name || '')
            setPhoneNumber(data.phone_number || data.contact_number || '')
            setEmail(data.email || '')
            updateUser(data)
          }
        }
      } catch {
        // Silently retain cached user details
      }
    }
    fetchLatestProfile()
    return () => {
      isMounted = false
    }
  }, [fetchWithAuth, updateUser])

  // Handle profile update (AC-1)
  const handleProfileSubmit = async (e) => {
    e.preventDefault()
    setProfileSuccess('')
    setProfileGeneralError('')
    setProfileErrors({})

    const validation = validateProfileUpdateInput({
      first_name: firstName,
      last_name: lastName,
      phone_number: phoneNumber,
      email,
    })

    if (!validation.isValid) {
      setProfileErrors(validation.errors)
      return
    }

    setProfileSaving(true)
    try {
      const res = await fetchWithAuth('/api/auth/profile/', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          first_name: firstName.trim(),
          last_name: lastName.trim(),
          phone_number: phoneNumber.trim(),
          contact_number: phoneNumber.trim(),
          email: email.trim(),
        }),
      })

      const data = await res.json().catch(() => ({}))

      if (!res.ok) {
        if (data.details && typeof data.details === 'object') {
          const fieldErrs = {}
          Object.entries(data.details).forEach(([key, val]) => {
            fieldErrs[key] = Array.isArray(val) ? val.join(' ') : String(val)
          })
          setProfileErrors(fieldErrs)
        } else if (data.email) {
          setProfileErrors({ email: Array.isArray(data.email) ? data.email.join(' ') : data.email })
        } else if (data.phone_number || data.contact_number) {
          setProfileErrors({
            phone_number: Array.isArray(data.phone_number || data.contact_number)
              ? (data.phone_number || data.contact_number).join(' ')
              : (data.phone_number || data.contact_number),
          })
        }
        setProfileGeneralError(data.error || 'Failed to update profile. Please check the inputs.')
        return
      }

      updateUser(data)
      setProfileSuccess('Profile details updated successfully.')
    } catch {
      setProfileGeneralError('Network error: Unable to contact profile update service.')
    } finally {
      setProfileSaving(false)
    }
  }

  // Handle password change (AC-2 & AC-3)
  const handlePasswordSubmit = async (e) => {
    e.preventDefault()
    setPasswordSuccess('')
    setPasswordGeneralError('')
    setPasswordErrors({})

    const validation = validatePasswordChangeInput({
      current_password: currentPassword,
      new_password: newPassword,
      new_password_confirm: newPasswordConfirm,
    })

    if (!validation.isValid) {
      setPasswordErrors(validation.errors)
      return
    }

    setPasswordSaving(true)
    try {
      const res = await fetchWithAuth('/api/auth/password/change/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          new_password_confirm: newPasswordConfirm,
        }),
      })

      const data = await res.json().catch(() => ({}))

      if (!res.ok) {
        if (data.details && typeof data.details === 'object') {
          const fieldErrs = {}
          Object.entries(data.details).forEach(([key, val]) => {
            fieldErrs[key] = Array.isArray(val) ? val.join(' ') : String(val)
          })
          setPasswordErrors(fieldErrs)
        } else {
          const fieldErrs = {}
          if (data.current_password) {
            fieldErrs.current_password = Array.isArray(data.current_password)
              ? data.current_password.join(' ')
              : data.current_password
          }
          if (data.new_password) {
            fieldErrs.new_password = Array.isArray(data.new_password)
              ? data.new_password.join(' ')
              : data.new_password
          }
          if (data.new_password_confirm) {
            fieldErrs.new_password_confirm = Array.isArray(data.new_password_confirm)
              ? data.new_password_confirm.join(' ')
              : data.new_password_confirm
          }
          setPasswordErrors(fieldErrs)
        }
        setPasswordGeneralError(data.error || 'Failed to change password. Please verify current password and requirements.')
        return
      }

      setPasswordSuccess('Password changed successfully. Your active sessions have been updated.')
      setCurrentPassword('')
      setNewPassword('')
      setNewPasswordConfirm('')
    } catch {
      setPasswordGeneralError('Network error: Unable to contact password change service.')
    } finally {
      setPasswordSaving(false)
    }
  }

  return (
    <div className="bay-account" style={{ maxWidth: '800px', margin: '0 auto', padding: '24px 16px' }}>
      <span className="bay-eyebrow">USER PROFILE & SECURITY</span>
      <h1>
        Account Settings<span>.</span>
      </h1>
      <p style={{ color: 'var(--bay-muted)', marginBottom: '24px' }}>
        Manage your personal profile information, contact details, and password security.
      </p>

      {/* Account Overview Card */}
      <div className="bay-account-card" style={{ maxWidth: '100%', marginBottom: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flexWrap: 'wrap' }}>
          <span className="bay-avatar bay-avatar-large">
            {user?.username?.slice(0, 2).toUpperCase() || 'US'}
          </span>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <h2 style={{ margin: '0 0 4px 0' }}>{user?.username}</h2>
            <p style={{ margin: 0, color: 'var(--bay-muted)' }}>{user?.email || 'No email provided'}</p>
          </div>
          <button
            type="button"
            className="bay-button bay-button-secondary"
            onClick={logout}
            disabled={authLoading}
            id="btn-profile-logout"
          >
            {authLoading ? 'Signing out...' : 'Sign out'}
            <BayIcon name="exit" size={16} />
          </button>
        </div>

        <dl className="bay-slot-details" style={{ marginTop: '20px' }}>
          <div>
            <dt>Role</dt>
            <dd id="profile-display-role">{user?.role || 'Customer'}</dd>
          </div>
          <div>
            <dt>Account status</dt>
            <dd id="profile-display-status">{user?.status || 'active'}</dd>
          </div>
          <div>
            <dt>Username</dt>
            <dd id="profile-display-username">{user?.username}</dd>
          </div>
          <div>
            <dt>Contact Phone</dt>
            <dd id="profile-display-contact">{user?.phone_number || user?.contact_number || 'Not set'}</dd>
          </div>
        </dl>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '24px' }}>
        {/* Profile Update Section (AC-1) */}
        <section
          className="bay-account-card"
          style={{ maxWidth: '100%', margin: 0 }}
          aria-labelledby="heading-profile-details"
        >
          <h2 id="heading-profile-details" style={{ fontSize: '20px', marginBottom: '8px' }}>
            Personal Details
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--bay-muted)', marginBottom: '18px' }}>
            Update your name and primary contact number.
          </p>

          {profileSuccess && (
            <div
              className="bay-alert"
              role="status"
              id="profile-success-alert"
              style={{
                marginBottom: '16px',
                background: '#e8f5e9',
                borderColor: '#a5d6a7',
                color: '#2e7d32',
                borderRadius: '8px',
                padding: '10px 14px',
                fontSize: '13px',
              }}
            >
              {profileSuccess}
            </div>
          )}

          {profileGeneralError && (
            <div
              className="bay-alert"
              role="alert"
              id="profile-error-alert"
              style={{
                marginBottom: '16px',
                background: '#ffebee',
                borderColor: '#ffcdd2',
                color: '#c62828',
                borderRadius: '8px',
                padding: '10px 14px',
                fontSize: '13px',
              }}
            >
              {profileGeneralError}
            </div>
          )}

          <form onSubmit={handleProfileSubmit} id="profile-form">
            <div className="bay-field">
              <label htmlFor="profile-first-name">First Name</label>
              <input
                id="profile-first-name"
                name="first_name"
                type="text"
                value={firstName}
                onChange={(e) => {
                  setFirstName(e.target.value)
                  if (profileErrors.first_name) setProfileErrors((p) => ({ ...p, first_name: null }))
                }}
                placeholder="Jane"
                disabled={profileSaving}
                maxLength={150}
              />
              {profileErrors.first_name && (
                <span className="field-error-text" style={{ color: '#c62828', fontSize: '12px' }}>
                  {profileErrors.first_name}
                </span>
              )}
            </div>

            <div className="bay-field">
              <label htmlFor="profile-last-name">Last Name</label>
              <input
                id="profile-last-name"
                name="last_name"
                type="text"
                value={lastName}
                onChange={(e) => {
                  setLastName(e.target.value)
                  if (profileErrors.last_name) setProfileErrors((p) => ({ ...p, last_name: null }))
                }}
                placeholder="Doe"
                disabled={profileSaving}
                maxLength={150}
              />
              {profileErrors.last_name && (
                <span className="field-error-text" style={{ color: '#c62828', fontSize: '12px' }}>
                  {profileErrors.last_name}
                </span>
              )}
            </div>

            <div className="bay-field">
              <label htmlFor="profile-phone-number">Contact Phone Number</label>
              <input
                id="profile-phone-number"
                name="phone_number"
                type="tel"
                value={phoneNumber}
                onChange={(e) => {
                  setPhoneNumber(e.target.value)
                  if (profileErrors.phone_number) setProfileErrors((p) => ({ ...p, phone_number: null }))
                }}
                placeholder="+1 (555) 000-0000"
                disabled={profileSaving}
                maxLength={20}
              />
              {profileErrors.phone_number && (
                <span className="field-error-text" style={{ color: '#c62828', fontSize: '12px' }}>
                  {profileErrors.phone_number}
                </span>
              )}
            </div>

            <div className="bay-field">
              <label htmlFor="profile-email">Email Address</label>
              <input
                id="profile-email"
                name="email"
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                  if (profileErrors.email) setProfileErrors((p) => ({ ...p, email: null }))
                }}
                placeholder="jane.doe@example.com"
                disabled={profileSaving}
              />
              {profileErrors.email && (
                <span className="field-error-text" style={{ color: '#c62828', fontSize: '12px' }}>
                  {profileErrors.email}
                </span>
              )}
            </div>

            <button
              type="submit"
              className="bay-button bay-button-primary"
              id="btn-save-profile"
              disabled={profileSaving}
              style={{ marginTop: '8px', width: '100%' }}
            >
              {profileSaving ? 'Saving...' : 'Save Profile Changes'}
            </button>
          </form>
        </section>

        {/* Password Management Section (AC-2 & AC-3) */}
        <section
          className="bay-account-card"
          style={{ maxWidth: '100%', margin: 0 }}
          aria-labelledby="heading-password-security"
        >
          <h2 id="heading-password-security" style={{ fontSize: '20px', marginBottom: '8px' }}>
            Change Password
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--bay-muted)', marginBottom: '18px' }}>
            Keep your account secure with a strong, compliant password.
          </p>

          {passwordSuccess && (
            <div
              className="bay-alert"
              role="status"
              id="password-success-alert"
              style={{
                marginBottom: '16px',
                background: '#e8f5e9',
                borderColor: '#a5d6a7',
                color: '#2e7d32',
                borderRadius: '8px',
                padding: '10px 14px',
                fontSize: '13px',
              }}
            >
              {passwordSuccess}
            </div>
          )}

          {passwordGeneralError && (
            <div
              className="bay-alert"
              role="alert"
              id="password-error-alert"
              style={{
                marginBottom: '16px',
                background: '#ffebee',
                borderColor: '#ffcdd2',
                color: '#c62828',
                borderRadius: '8px',
                padding: '10px 14px',
                fontSize: '13px',
              }}
            >
              {passwordGeneralError}
            </div>
          )}

          <form onSubmit={handlePasswordSubmit} id="password-form">
            <div className="bay-field">
              <label htmlFor="pwd-current">Current Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  id="pwd-current"
                  name="current_password"
                  type={showCurrentPassword ? 'text' : 'password'}
                  value={currentPassword}
                  onChange={(e) => {
                    setCurrentPassword(e.target.value)
                    if (passwordErrors.current_password) {
                      setPasswordErrors((p) => ({ ...p, current_password: null }))
                    }
                  }}
                  placeholder="Enter current password"
                  disabled={passwordSaving}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  style={{
                    position: 'absolute',
                    right: '10px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '12px',
                    color: 'var(--bay-muted)',
                  }}
                  tabIndex={-1}
                  aria-label={showCurrentPassword ? 'Hide current password' : 'Show current password'}
                >
                  {showCurrentPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              {passwordErrors.current_password && (
                <span className="field-error-text" style={{ color: '#c62828', fontSize: '12px' }}>
                  {passwordErrors.current_password}
                </span>
              )}
            </div>

            <div className="bay-field">
              <label htmlFor="pwd-new">New Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  id="pwd-new"
                  name="new_password"
                  type={showNewPassword ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => {
                    setNewPassword(e.target.value)
                    if (passwordErrors.new_password) {
                      setPasswordErrors((p) => ({ ...p, new_password: null }))
                    }
                  }}
                  placeholder="At least 8 chars with mixed case, number, symbol"
                  disabled={passwordSaving}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  style={{
                    position: 'absolute',
                    right: '10px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '12px',
                    color: 'var(--bay-muted)',
                  }}
                  tabIndex={-1}
                  aria-label={showNewPassword ? 'Hide new password' : 'Show new password'}
                >
                  {showNewPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              {passwordErrors.new_password && (
                <span className="field-error-text" style={{ color: '#c62828', fontSize: '12px' }}>
                  {passwordErrors.new_password}
                </span>
              )}
            </div>

            <div className="bay-field">
              <label htmlFor="pwd-new-confirm">Confirm New Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  id="pwd-new-confirm"
                  name="new_password_confirm"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={newPasswordConfirm}
                  onChange={(e) => {
                    setNewPasswordConfirm(e.target.value)
                    if (passwordErrors.new_password_confirm) {
                      setPasswordErrors((p) => ({ ...p, new_password_confirm: null }))
                    }
                  }}
                  placeholder="Re-type new password"
                  disabled={passwordSaving}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  style={{
                    position: 'absolute',
                    right: '10px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '12px',
                    color: 'var(--bay-muted)',
                  }}
                  tabIndex={-1}
                  aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                >
                  {showConfirmPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              {passwordErrors.new_password_confirm && (
                <span className="field-error-text" style={{ color: '#c62828', fontSize: '12px' }}>
                  {passwordErrors.new_password_confirm}
                </span>
              )}
            </div>

            <p style={{ fontSize: '11.5px', color: 'var(--bay-muted)', margin: '8px 0 16px' }}>
              Password must be at least 8 characters long, containing uppercase and lowercase letters, at least one digit, and at least one special character.
            </p>

            <button
              type="submit"
              className="bay-button bay-button-primary"
              id="btn-change-password"
              disabled={passwordSaving}
              style={{ width: '100%' }}
            >
              {passwordSaving ? 'Updating Password...' : 'Update Password'}
            </button>
          </form>
        </section>
      </div>
    </div>
  )
}

