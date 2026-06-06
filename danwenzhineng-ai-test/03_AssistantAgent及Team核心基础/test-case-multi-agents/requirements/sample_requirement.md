# Requirement: User Login

Build a login feature for a web application.

## Functional Requirements

- Users can log in with email and password.
- Email must use a valid email format.
- Password is required and must not be empty.
- Users with valid credentials are redirected to the dashboard.
- Users with invalid credentials see a clear error message.
- After five consecutive failed attempts, the account is temporarily locked for 15 minutes.

## Non-Functional Requirements

- Login response time should be under 2 seconds for normal load.
- Error messages must not reveal whether the email or password was incorrect.
- The page should be usable with keyboard navigation.

