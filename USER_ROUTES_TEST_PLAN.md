# User Routes Testing Guide

## Prerequisites
- Backend server running on `http://localhost:8000`
- Valid JWT token for authenticated requests
- Test user account created

## API Endpoints Testing

### 1. Get User Profile
```bash
# Test: Retrieve current user profile
curl -X GET "http://localhost:8000/api/user/profile" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Expected Response (200 OK):
{
  "id": "user-uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### 2. Update User Profile
```bash
# Test: Update full name
curl -X PUT "http://localhost:8000/api/user/profile" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Jane Doe"
  }'

# Test: Update email
curl -X PUT "http://localhost:8000/api/user/profile" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com"
  }'

# Test: Update both fields
curl -X PUT "http://localhost:8000/api/user/profile" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Jane Smith",
    "email": "jane.smith@example.com"
  }'

# Expected Response (200 OK):
{
  "id": "user-uuid",
  "email": "jane.smith@example.com",
  "full_name": "Jane Smith",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}

# Test: Duplicate email (should fail)
curl -X PUT "http://localhost:8000/api/user/profile" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "existing@example.com"
  }'

# Expected Response (400 Bad Request):
{
  "detail": "Email already in use by another account"
}
```

### 3. Delete User Account
```bash
# Test: Delete account (DESTRUCTIVE - use with caution)
curl -X DELETE "http://localhost:8000/api/user/account" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Expected Response (200 OK):
{
  "message": "Account deleted successfully",
  "detail": "Your account and all associated data have been permanently deleted"
}
```

### 4. Forgot Password
```bash
# Test: Request password reset
curl -X POST "http://localhost:8000/api/user/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'

# Expected Response (200 OK) - Development:
{
  "message": "Password reset token generated",
  "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "note": "In production, this would be sent via email"
}

# Expected Response (200 OK) - Production:
{
  "message": "If the email exists, a password reset link has been sent"
}

# Test: Non-existent email (same response for security)
curl -X POST "http://localhost:8000/api/user/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nonexistent@example.com"
  }'

# Expected Response (200 OK):
{
  "message": "If the email exists, a password reset link has been sent"
}
```

### 5. Reset Password
```bash
# Test: Reset password with token
curl -X POST "http://localhost:8000/api/user/reset-password" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "RESET_TOKEN_FROM_FORGOT_PASSWORD",
    "new_password": "NewSecurePassword123!"
  }'

# Expected Response (200 OK):
{
  "message": "Password successfully reset"
}

# Test: Invalid token
curl -X POST "http://localhost:8000/api/user/reset-password" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "invalid_token",
    "new_password": "NewPassword123!"
  }'

# Expected Response (400 Bad Request):
{
  "detail": "Invalid reset token"
}

# Test: Expired token (after 1 hour)
# Expected Response (400 Bad Request):
{
  "detail": "Invalid or expired reset token"
}
```

## Frontend Testing (Profile Page)

### Test Cases

1. **Profile Display**
   - Navigate to `/profile`
   - Verify user information displays correctly
   - Check avatar initials are generated properly

2. **Update Profile**
   - Update full name
   - Update email
   - Verify success toast appears
   - Verify profile updates in UI

3. **Email Validation**
   - Try to update with duplicate email
   - Verify error message displays
   - Verify profile doesn't update

4. **Account Deletion**
   - Click delete account button
   - Verify confirmation dialog appears
   - Confirm deletion
   - Verify redirect to signup page
   - Verify logout occurs

5. **Password Reset Flow**
   - Navigate to forgot password page
   - Enter email
   - Verify success message
   - Use reset token (in development)
   - Enter new password
   - Verify success message
   - Login with new password

## Integration Testing

### Test Scenarios

1. **Profile Update + Preferences**
   - Update profile
   - Update preferences
   - Verify both persist correctly

2. **Account Deletion Cascade**
   - Create user with sources, drafts, etc.
   - Delete account
   - Verify all related data is deleted

3. **Password Reset Flow**
   - Request reset
   - Verify token stored in database
   - Reset password
   - Verify token cleared from database
   - Login with new password

4. **Concurrent Updates**
   - Update profile from two sessions
   - Verify last write wins
   - Verify no data corruption

## Error Scenarios to Test

1. **Authentication Errors**
   - Missing token → 401
   - Invalid token → 401
   - Expired token → 401

2. **Validation Errors**
   - Invalid email format → 422
   - Empty update → 400
   - Duplicate email → 400

3. **Not Found Errors**
   - Reset password with deleted user → 404

4. **Server Errors**
   - Database connection failure → 500

## Performance Testing

1. **Load Test Profile Retrieval**
   - 100 concurrent requests
   - Verify response time < 200ms

2. **Stress Test Profile Updates**
   - Rapid successive updates
   - Verify data consistency

## Security Testing

1. **Authorization**
   - Try to access another user's profile
   - Verify 401/403 response

2. **Email Enumeration**
   - Request password reset for multiple emails
   - Verify responses are identical

3. **Token Security**
   - Try to use reset token twice
   - Verify second attempt fails

4. **SQL Injection**
   - Try malicious input in email/name fields
   - Verify proper sanitization

## Automated Testing (Python)

```python
import requests

BASE_URL = "http://localhost:8000"
TOKEN = "your_jwt_token"

def test_get_profile():
    response = requests.get(
        f"{BASE_URL}/api/user/profile",
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    assert response.status_code == 200
    assert "email" in response.json()

def test_update_profile():
    response = requests.put(
        f"{BASE_URL}/api/user/profile",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"full_name": "Test User"}
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Test User"

def test_forgot_password():
    response = requests.post(
        f"{BASE_URL}/api/user/forgot-password",
        json={"email": "test@example.com"}
    )
    assert response.status_code == 200
    assert "message" in response.json()

# Run tests
if __name__ == "__main__":
    test_get_profile()
    test_update_profile()
    test_forgot_password()
    print("All tests passed!")
```

## Checklist

- [ ] All endpoints return correct status codes
- [ ] Authentication works properly
- [ ] Email validation prevents duplicates
- [ ] Password reset flow works end-to-end
- [ ] Account deletion removes all data
- [ ] Error messages are user-friendly
- [ ] Logging captures important events
- [ ] Frontend integration works seamlessly
- [ ] Security measures are in place
- [ ] Performance is acceptable

## Notes

- Password reset tokens expire after 1 hour
- Account deletion is permanent and cannot be undone
- Email changes require unique emails across all users
- All operations are logged for audit purposes
