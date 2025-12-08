# PawRes Testing Documentation

## Table of Contents

1. [Test Strategy](#test-strategy)
2. [Test Coverage Summary](#test-coverage-summary)
3. [Test Execution](#test-execution)
4. [Test Fixtures](#test-fixtures)
5. [Test Patterns](#test-patterns)
6. [Manual Exploratory Test Checklist](#manual-exploratory-test-checklist)
7. [CI/CD Considerations](#cicd-considerations)

---

## Test Strategy

PawRes employs a comprehensive multi-layered testing strategy to ensure reliability, security, and maintainability:

### 1. **Unit Tests** (Primary Focus)
- **Scope**: Individual service methods and business logic
- **Isolation**: Each test uses a temporary SQLite database for complete isolation
- **Coverage Target**: 85%+ of service layer code
- **Execution Time**: Fast (<5 seconds for full suite)

### 2. **Integration Tests**
- **Scope**: End-to-end workflows across multiple services
- **Examples**: Complete rescue-to-adoption flow, user authentication to resource access
- **Purpose**: Validate service interactions and state transitions

### 3. **Manual Exploratory Testing**
- **Scope**: UI/UX workflows, visual validation, edge cases
- **Focus Areas**: Form validation, photo uploads, map interactions, chart rendering
- **Execution**: Developer-driven testing during feature development

### 4. **Security Testing** (Embedded)
- **Focus**: Authentication, authorization, password policies, account lockout
- **Validation**: SQL injection prevention, XSS protection, audit logging

### Testing Philosophy
- **Fail Fast**: Tests run quickly and provide immediate feedback
- **Deterministic**: No flaky tests; temporary databases ensure clean state
- **Readable**: Clear test names describe expected behavior
- **Maintainable**: Fixtures reduce duplication and simplify setup

---

## Test Coverage Summary

### Test Files by Services Overview

PawRes includes **12 comprehensive test files** covering all critical service layers:

| Test File | Purpose | Key Test Areas | Test Count |
|-----------|---------|----------------|------------|
| `test_auth_service.py` | Authentication & authorization | Registration, login, lockout, session timeout, OAuth linking | 20+ |
| `test_animal_service.py` | Animal CRUD operations | Create, read, update, delete, photo handling, adoptable filtering | 18+ |
| `test_rescue_service.py` | Rescue mission management | Submit requests, status transitions, auto-animal creation, archived filtering | 22+ |
| `test_adoption_service.py` | Adoption workflow | Submit applications, approve/deny, auto-denial logic, status tracking | 18+ |
| `test_user_service.py` | User management | Get user, list users, enable/disable, delete with cascades, password reset | 15+ |
| `test_analytics_service.py` | Dashboard analytics | Stats calculation, trend analysis, date filtering, chart data | 12+ |
| `test_status_constants.py` | Status normalization | Status string normalization, archived suffix handling, validation | 10+ |
| `test_password_policy.py` | Password security | Validation rules, history checking, strength requirements | 12+ |
| `test_logging_service.py` | Audit logging | Auth logs, admin logs, security logs, filtering, retention | 10+ |
| `test_google_auth_service.py` | OAuth integration | Google login flow, profile fetching, token validation | 8+ |
| `test_integration.py` | End-to-end workflows | Complete rescue→adoption flow, multi-service interactions | 15+ |
| `test_enhancement_features.py` | Advanced features | AI classification, maps, charts, CSV import, export | 12+ |

**Total Test Cases**: 331 (verified December 8, 2025)  
**Overall Project Coverage**: **51.80%** (verified December 8, 2025)  
**Untested Areas**: UI layer (Flet views), AI models (0%), map service (0%)

### Detailed Test Coverage by File (Updated December 8, 2025)

The following table shows coverage metrics for each test file and the modules they test:

| Test File | Module Tested | Statements | Missing | Coverage |
|-----------|---------------|------------|---------|----------|
| `test_app_config.py` | `app_config.py` | 283 | 22 | **92.23%** |
| `test_password_policy.py` | `password_policy.py` | 74 | 20 | **72.97%** |
| `test_photo_service.py` | `photo_service.py` | 101 | 24 | **76.24%** |
| `test_logging_service.py` | `logging_service.py` | 125 | 36 | **71.20%** |
| `test_user_service.py` + `test_user_service_extended.py` | `user_service.py` | 236 | 77 | **67.37%** |
| `test_adoption_service.py` | `adoption_service.py` | 130 | 46 | **64.62%** |
| `test_classification_result.py` | `classification_result.py` | 50 | 18 | **64.00%** |
| `test_google_auth_service.py` | `google_auth_service.py` | 164 | 60 | **63.41%** |
| `test_rescue_service.py` | `rescue_service.py` | 199 | 78 | **60.80%** |
| `test_animal_service.py` | `animal_service.py` | 150 | 69 | **54.00%** |
| `test_auth_service.py` | `auth_service.py` | 345 | 165 | **52.17%** |
| `test_import_service.py` | `import_service.py` | 276 | 150 | **45.65%** |
| `test_analytics_service.py` | `analytics_service.py` | 706 | 611 | **13.46%** |
| (untested) | `ai_classification_service.py` | - | - | **0%** (requires model files) |
| (untested) | `map_service.py` | - | - | **0%** (external API dependent) |

### Coverage by Module Category

#### Core Infrastructure (High Coverage)
```
app_config.py                       ████████████████████ 92.23%
storage/__init__.py                 ████████████████████ 100.00%
storage/cache.py                    █████████░░░░░░░░░░░ 45.99%
storage/database.py                 █████████████░░░░░░░ 64.81%
storage/db_interface.py             ██████████░░░░░░░░░░ 52.00%
storage/file_store.py               ███████░░░░░░░░░░░░░ 39.01%
```

#### Service Layer (Mixed Coverage)
```
services/
├── photo_service.py                ███████████████░░░░░ 76.24%
├── password_policy.py              ██████████████░░░░░░ 72.97%
├── logging_service.py              ██████████████░░░░░░ 71.20%
├── user_service.py                 █████████████░░░░░░░ 67.37%
├── adoption_service.py             █████████████░░░░░░░ 64.62%
├── google_auth_service.py          ████████████░░░░░░░░ 63.41%
├── rescue_service.py               ████████████░░░░░░░░ 60.80%
├── animal_service.py               ██████████░░░░░░░░░░ 54.00%
├── auth_service.py                 ██████████░░░░░░░░░░ 52.17%
├── import_service.py               █████████░░░░░░░░░░░ 45.65%
├── analytics_service.py            ██░░░░░░░░░░░░░░░░░░ 13.46%
├── ai_classification_service.py    ░░░░░░░░░░░░░░░░░░░░  0% (requires model files)
└── map_service.py                  ░░░░░░░░░░░░░░░░░░░░  0% (external API dependent)
```

#### Models (Good Coverage)
```
models/classification_result.py     ████████████░░░░░░░░ 64.00%
```

**Coverage Insights**:

- **High Coverage (>70%)**: Core configuration, password policy, photo service, and logging service are well-tested with comprehensive test suites.
- **Good Coverage (50-70%)**: Most service layer modules have solid coverage including authentication, CRUD operations, and business logic.
- **Low Coverage (<50%)**: Analytics service contains complex aggregation logic that requires integration testing; import service has many conditional branches for different file formats.
- **Untested (0%)**: AI classification and map services depend on external resources (model files, APIs) and require mocking or integration tests.

**Note**: The overall project coverage (51.80%) includes all modules in the codebase. The service layer ranges from 13% to 76% coverage, with core business logic modules (auth, animal, rescue, adoption, user services) averaging 60% coverage (52-67% range), and supporting services (photo, password policy, logging) achieving 71-76% coverage. Lower coverage in analytics (13%) and import (46%) services reflects complex aggregation logic and conditional branches requiring integration testing.

---

## Test Execution

### Prerequisites

1. **Python Environment**: Ensure virtual environment is activated
  ```powershell
  # Change <path-to-project> to the folder where you cloned the repo (for example: C:\Users\you\projects\PawRes)
  # Using an environment variable in PowerShell is also an option: cd $env:USERPROFILE\projects\PawRes
  cd <path-to-project>
  # Activate the virtual environment (Windows PowerShell)
  .\venv\Scripts\Activate.ps1
  
  # macOS / Linux example (Bash / Zsh)
  # cd <path-to-project>
  # source venv/bin/activate
  ```

2. **Dependencies**: Install pytest and coverage tools
   ```powershell
   pip install pytest pytest-cov
   ```

### Running Tests

#### Run All Tests
```powershell
cd <path-to-project>
python -m pytest app/tests -v
```

**Expected Output**:
```
========================= test session starts =========================
collected 331 items

app\tests\test_adoption_service.py::TestSubmitAdoptionRequest::test_submit_adoption_success PASSED      [  0%]
app\tests\test_adoption_service.py::TestSubmitAdoptionRequest::test_submit_adoption_minimal PASSED      [  0%]
app\tests\test_adoption_service.py::TestSubmitAdoptionRequest::test_submit_multiple_requests_same_animal PASSED [  0%]
...
========================= 331 passed in 37.81s =========================
```

#### Run Specific Test File
```powershell
python -m pytest app/tests/test_auth_service.py -v
```

#### Run Specific Test Class
```powershell
python -m pytest app/tests/test_auth_service.py::TestUserRegistration -v
```

#### Run Specific Test Method
```powershell
python -m pytest app/tests/test_auth_service.py::TestUserRegistration::test_register_user_success -v
```

#### Run Tests by Marker
```powershell
# Run only security tests
python -m pytest app/tests -m security -v

# Run only integration tests
python -m pytest app/tests -m integration -v

# Run only fast unit tests
python -m pytest app/tests -m unit -v
```

#### Run Tests with Coverage
```powershell
# Generate HTML coverage report
python -m pytest app/tests --cov=app --cov-report=html --cov-report=term

# View coverage report in browser
Start-Process .\htmlcov\index.html
```

**Coverage Report Interpretation**:
- **Green lines**: Executed during tests
- **Red lines**: Not covered by tests
- **Yellow lines**: Partial coverage (e.g., only one branch of an if statement)

#### Run Tests in Quiet Mode (Summary Only)
```powershell
python -m pytest app/tests -q
```

#### Run Tests with Detailed Output
```powershell
python -m pytest app/tests -vv
```

#### Stop on First Failure
```powershell
python -m pytest app/tests -x
```

---

## Test Fixtures

Test fixtures are defined in `app/tests/conftest.py` and provide reusable test infrastructure.

### Database Fixtures

#### `temp_db`
Creates a temporary SQLite database with all tables initialized. Automatically deleted after test completion.

```python
def test_example(temp_db):
    # temp_db is a Database instance with empty tables
    temp_db.execute("INSERT INTO users (...) VALUES (...)")
```

**Use Case**: When you need direct database access for assertions.

#### `temp_db_path`
Provides the path to a temporary database file. Services automatically initialize tables.

```python
def test_example(temp_db_path):
    # temp_db_path is a string path
    service = AnimalService(temp_db_path)
```

**Use Case**: When testing services that accept `db_path` parameter (most common).

### Service Fixtures

Pre-configured service instances with temporary databases:

```python
@pytest.fixture
def auth_service(temp_db_path):
    """Auth service with temporary database."""
    return AuthService(temp_db_path)
```

**Available Service Fixtures**:
- `auth_service` - Authentication and user registration
- `animal_service` - Animal CRUD operations
- `rescue_service` - Rescue mission management
- `adoption_service` - Adoption request handling
- `analytics_service` - Dashboard statistics
- `user_service` - User management operations
- `import_service` - CSV/Excel import functionality

**Usage Example**:
```python
def test_login(auth_service):
    user_id = auth_service.register_user("Test", "test@example.com", "Pass@123", skip_policy=True)
    result = auth_service.login("test@example.com", "Pass@123")
    assert result.success
```

### Data Fixtures

#### `sample_user`
Creates a test user with known credentials.

```python
@pytest.fixture
def sample_user(auth_service):
    user_id = auth_service.register_user(
        name="Test User",
        email="testuser@example.com",
        password="TestPass@123",
        role="user",
        skip_policy=True
    )
    return {
        "id": user_id,
        "email": "testuser@example.com",
        "password": "TestPass@123",
        "name": "Test User",
        "role": "user"
    }
```

#### `sample_admin`
Creates a test admin user.

```python
def test_admin_action(sample_admin, rescue_service):
    # sample_admin has full admin privileges
    missions = rescue_service.get_all_missions()
    assert isinstance(missions, list)
```

#### `sample_animal`
Creates a test animal record.

```python
def test_adoption(sample_animal, adoption_service, sample_user):
    adoption_id = adoption_service.submit_request(
        user_id=sample_user["id"],
        animal_id=sample_animal["id"],
        contact=sample_user["email"],
        reason="I love dogs"
    )
    assert adoption_id > 0
```

#### `sample_rescue_mission`
Creates a pending rescue mission.

```python
def test_rescue_approval(sample_rescue_mission, rescue_service):
    success = rescue_service.update_rescue_status(
        sample_rescue_mission["id"],
        RescueStatus.ONGOING
    )
    assert success
```

### Fixture Combinations

Fixtures can be combined to test complex scenarios:

```python
def test_integration_flow(auth_service, rescue_service, animal_service, adoption_service, sample_user):
    # User submits rescue
    mission_id = rescue_service.submit_rescue_request(
        user_id=sample_user["id"],
        animal_type="dog",
        breed="Labrador",
        name="Lucky",
        location="Naga City"
    )
    
    # Admin marks as rescued (auto-creates animal)
    rescue_service.update_rescue_status(mission_id, RescueStatus.RESCUED)
    mission = rescue_service.get_mission_by_id(mission_id)
    
    # User submits adoption for the rescued animal
    adoption_id = adoption_service.submit_request(
        user_id=sample_user["id"],
        animal_id=mission["animal_id"],
        contact=sample_user["email"],
        reason="Great dog!"
    )
    
    assert adoption_id > 0
```

---

## Test Patterns

### 1. Arrange-Act-Assert (AAA)

All tests follow the AAA pattern for clarity:

```python
def test_update_animal(animal_service, sample_animal):
    # Arrange - Set up test data
    animal_id = sample_animal["id"]
    new_health_status = "healthy"
    
    # Act - Execute the action being tested
    success = animal_service.update_animal(
        animal_id,
        health_status=new_health_status
    )
    
    # Assert - Verify expected outcome
    assert success is True
    updated_animal = animal_service.get_animal_by_id(animal_id)
    assert updated_animal["health_status"] == "healthy"
```

### 2. Test Class Organization

Related tests are grouped into classes by feature:

```python
class TestUserRegistration:
    """Test user registration functionality."""
    
    def test_register_user_success(self, auth_service):
        # Happy path test
        pass
    
    def test_register_duplicate_email(self, auth_service):
        # Error handling test
        pass
    
    def test_register_with_phone(self, auth_service):
        # Optional parameter test
        pass
```

**Benefits**:
- Logical grouping improves readability
- Setup/teardown can be shared via class-level fixtures
- Test discovery is more intuitive

### 3. Result Validation Pattern

Services return result objects with consistent structure:

```python
def test_login_success(auth_service, sample_user):
    result = auth_service.login(
        sample_user["email"],
        sample_user["password"]
    )
    
    # Validate result structure
    assert result.success is True
    assert result.user_id == sample_user["id"]
    assert result.message == "Login successful"
    assert result.user_role == "user"
```

### 4. Exception Testing

Use `pytest.raises` for expected exceptions:

```python
def test_register_duplicate_email(auth_service):
    auth_service.register_user("User1", "test@example.com", "Pass@123", skip_policy=True)
    
    with pytest.raises(ValueError, match="email is already registered"):
        auth_service.register_user("User2", "test@example.com", "Pass@456", skip_policy=True)
```

### 5. State Transition Testing

Verify complex state changes:

```python
def test_rescue_status_transitions(rescue_service, sample_rescue_mission):
    mission_id = sample_rescue_mission["id"]
    
    # pending → on-going
    rescue_service.update_rescue_status(mission_id, RescueStatus.ONGOING)
    mission = rescue_service.get_mission_by_id(mission_id)
    assert RescueStatus.normalize(mission["status"]) == RescueStatus.ONGOING
    
    # on-going → rescued
    rescue_service.update_rescue_status(mission_id, RescueStatus.RESCUED)
    mission = rescue_service.get_mission_by_id(mission_id)
    assert RescueStatus.normalize(mission["status"]) == RescueStatus.RESCUED
    assert mission["animal_id"] is not None  # Auto-creates animal
```

### 6. Data-Driven Testing

Use parametrization for multiple test cases:

```python
@pytest.mark.parametrize("password,expected_valid", [
    ("Short1!", False),           # Too short
    ("nouppercase1!", False),     # No uppercase
    ("NOLOWERCASE1!", False),     # No lowercase
    ("NoSpecialChar1", False),    # No special char
    ("ValidPass@123", True),      # Valid password
])
def test_password_validation(password, expected_valid):
    from services.password_policy import PasswordPolicy
    policy = PasswordPolicy()
    is_valid, _ = policy.validate_password(password)
    assert is_valid == expected_valid
```

### 7. Time-Based Testing

Handle time-sensitive tests with datetime manipulation:

```python
def test_session_timeout(auth_service, sample_user):
    result = auth_service.login(sample_user["email"], sample_user["password"])
    session_id = result.session_id
    
    # Simulate time passage (via database manipulation or mocking)
    db = Database(auth_service.db.db_path)
    db.execute(
        "UPDATE sessions SET last_activity = datetime('now', '-31 minutes') WHERE id = ?",
        (session_id,)
    )
    
    # Verify session is expired
    is_valid = auth_service.validate_session(session_id)
    assert is_valid is False
```

---

## Manual Exploratory Test Checklist

While automated tests cover business logic, certain UI/UX aspects require manual testing.

### Authentication Flow

- [ ] **Login Page**
  - [ ] Valid credentials → Dashboard redirect
  - [ ] Invalid credentials → Error message displayed
  - [ ] Account lockout after 5 failed attempts → Error message with lockout duration
  - [ ] Disabled account → "Account disabled" message
  - [ ] Remember me checkbox → Persistent session
  - [ ] Google OAuth button → Opens Google login flow

- [ ] **Registration Page**
  - [ ] Valid form submission → Success message → Auto-login
  - [ ] Duplicate email → Error message
  - [ ] Weak password → Real-time validation errors
  - [ ] Phone number format validation
  - [ ] Terms & conditions checkbox required

- [ ] **Logout**
  - [ ] Logout button → Redirect to login → Session cleared
  - [ ] Back button after logout → Redirect to login (not cached page)

### Dashboard Navigation

- [ ] **User Dashboard**
  - [ ] Statistics cards display correct counts
  - [ ] Recent rescue missions table populates
  - [ ] Recent adoption requests table populates
  - [ ] Charts render correctly (bar, pie, line)
  - [ ] "View Details" buttons navigate to correct pages

- [ ] **Admin Dashboard**
  - [ ] All system statistics load
  - [ ] Pending approvals section highlights items needing attention
  - [ ] Quick action buttons work (approve, deny, view)
  - [ ] Date range filters update charts

### Rescue Mission Workflow

- [ ] **Submit Rescue (User)**
  - [ ] All form fields validate (required, format)
  - [ ] Photo upload works (drag-drop and file picker)
  - [ ] Photo preview displays
  - [ ] AI breed detection button triggers analysis
  - [ ] AI suggestions populate breed field
  - [ ] Map widget displays and allows location selection
  - [ ] "Get Current Location" button (if geolocation enabled)
  - [ ] Submit button → Success snackbar → Redirect to status page

- [ ] **Review Rescue (Admin)**
  - [ ] Rescue list displays all missions with filters
  - [ ] Status badges show correct colors
  - [ ] Click mission → Detail view opens
  - [ ] Photo displays in detail view
  - [ ] Map shows reported location
  - [ ] Status dropdown allows transitions (pending→on-going→rescued→cancelled)
  - [ ] Admin message field works
  - [ ] Update button → Confirmation dialog → Success message
  - [ ] "Rescued" status auto-creates animal record

### Animal Management

- [ ] **Add Animal (Admin)**
  - [ ] Form fields validate
  - [ ] Photo upload with preview
  - [ ] AI breed detection (if photo uploaded)
  - [ ] Species dropdown filters breed suggestions
  - [ ] Submit → Success → Redirect to animal list

- [ ] **Edit Animal (Admin)**
  - [ ] Form pre-populates with existing data
  - [ ] Photo change works (shows old photo as fallback)
  - [ ] Update button saves changes
  - [ ] Archive button hides animal from public list

- [ ] **Animals List (User)**
  - [ ] Only adoptable animals display
  - [ ] Filters work (species, breed, age)
  - [ ] Search by name works
  - [ ] Card layout displays photos correctly
  - [ ] "View Details" opens detail page
  - [ ] "Apply for Adoption" button navigates to adoption form

### Adoption Workflow

- [ ] **Submit Adoption (User)**
  - [ ] Animal information displays correctly
  - [ ] Contact field pre-fills from profile
  - [ ] Reason field validates (minimum length)
  - [ ] Submit → Success message → Redirect to status page

- [ ] **Review Adoption (Admin)**
  - [ ] Adoption list displays all requests
  - [ ] User profile information visible
  - [ ] Animal details visible
  - [ ] Reason text readable
  - [ ] Approve button → Confirmation dialog → Status updates to "approved"
  - [ ] Deny button → Prompt for reason → Status updates to "denied"
  - [ ] Auto-denial if animal adopted by another user

### User Management (Admin Only)

- [ ] **User List**
  - [ ] All users display with roles
  - [ ] Search by name/email works
  - [ ] Filter by role works
  - [ ] Enable/disable toggle updates status
  - [ ] Delete button → Confirmation → User removed

- [ ] **Reset Password**
  - [ ] Admin can reset user password
  - [ ] Temporary password generates
  - [ ] User can login with temp password
  - [ ] Force password change on next login

### Profile Management

- [ ] **Update Profile**
  - [ ] Name change saves
  - [ ] Phone change saves
  - [ ] Email change validates uniqueness
  - [ ] Password change requires old password
  - [ ] Profile photo upload works
  - [ ] Google account linking/unlinking works

### Audit Logs (Admin Only)

- [ ] **View Logs**
  - [ ] All event types display
  - [ ] Filter by event type works
  - [ ] Filter by user works
  - [ ] Date range picker works
  - [ ] Pagination works (if many logs)
  - [ ] Log details expand on click

### Import/Export (Admin Only)

- [ ] **Import Animals**
  - [ ] CSV file picker opens
  - [ ] Valid CSV processes successfully
  - [ ] Invalid CSV shows validation errors
  - [ ] Preview table displays before import
  - [ ] Confirm import → Progress indicator → Success message

- [ ] **Export Data**
  - [ ] Export animals to CSV downloads file
  - [ ] Export adoptions to CSV downloads file
  - [ ] CSV opens correctly in Excel/Google Sheets

### Error Handling

- [ ] **Network Errors**
  - [ ] Lost connection → User-friendly error message
  - [ ] Retry mechanism works

- [ ] **Session Timeout**
  - [ ] After 30 minutes inactivity → Redirect to login
  - [ ] Warning message displays before timeout

- [ ] **Photo Upload Errors**
  - [ ] File too large → Error message with size limit
  - [ ] Invalid file type → Error message
  - [ ] Upload failure → Retry option

- [ ] **AI Model Errors**
  - [ ] Model not downloaded → Download prompt
  - [ ] Classification failure → Fallback message

### Cross-Browser Testing (If Web Deployed)

- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (macOS)

### Responsive Design (If Web Deployed)

- [ ] Desktop (1920x1080)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)

---

## CI/CD Considerations

### Automated Test Pipeline (Future Implementation)

While PawRes currently relies on manual test execution, the test suite is CI/CD-ready. Here's a recommended pipeline configuration:

#### GitHub Actions Example

```yaml
name: PawRes Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests with coverage
      run: |
        python -m pytest app/tests --cov=app --cov-report=xml --cov-report=term
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        fail_ci_if_error: true
```

#### Pre-Commit Hooks

Use `pre-commit` to run tests before each commit:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: python -m pytest app/tests -q
        language: system
        pass_filenames: false
        always_run: true
```

Install:
```powershell
pip install pre-commit
pre-commit install
```

#### Test Parallelization

Speed up tests with pytest-xdist:

```powershell
pip install pytest-xdist
python -m pytest app/tests -n auto  # Auto-detect CPU cores
```

#### Coverage Thresholds

Enforce minimum coverage in CI:

```powershell
python -m pytest app/tests --cov=app --cov-fail-under=85
```

Exit code 1 if coverage < 85%, blocking merge.

---

## Troubleshooting Test Failures

### Common Issues

#### 1. **Database Lock Errors**
**Symptom**: `sqlite3.OperationalError: database is locked`

**Solution**: Ensure services open fresh connections per operation (already implemented in `Database` class).

#### 2. **Fixture Not Found**
**Symptom**: `fixture 'sample_user' not found`

**Solution**: Check `conftest.py` is in `app/tests/` and pytest discovers it.

#### 3. **Import Errors**
**Symptom**: `ModuleNotFoundError: No module named 'services'`

**Solution**: Run pytest from repo root: `python -m pytest app/tests`

#### 4. **Temporary File Cleanup Failures**
**Symptom**: `PermissionError: [WinError 32] The process cannot access the file`

**Solution**: Windows file locks may delay deletion. Tests already use exception handling in cleanup.

#### 5. **Time-Sensitive Tests Fail**
**Symptom**: Session timeout tests fail unpredictably

**Solution**: Use database time manipulation instead of `time.sleep()` (already implemented).

---

## Test Maintenance

### Adding New Tests

1. **Create test file** in `app/tests/test_<feature>.py`
2. **Import fixtures** from conftest
3. **Follow AAA pattern**
4. **Use descriptive test names**: `test_<action>_<expected_result>`
5. **Run tests** to verify: `python -m pytest app/tests/test_<feature>.py -v`

### Updating Tests After Code Changes

1. **Service signature changes**: Update fixture and all usages
2. **New status values**: Add tests for new transitions
3. **Database schema changes**: Update `Database.create_tables()` and verify fixtures work

### Test Review Checklist

Before merging new tests:

- [ ] All tests pass locally
- [ ] Test names clearly describe behavior
- [ ] No hardcoded paths or external dependencies
- [ ] Fixtures used correctly (no database path hardcoding)
- [ ] Assertions validate expected behavior, not implementation details
- [ ] Edge cases covered (empty inputs, nulls, duplicates)
- [ ] Error conditions tested (exceptions, validation failures)

---

## Conclusion

PawRes maintains a robust test suite with 251 automated tests covering 30% overall service layer code (52-73% for core CRUD operations). The combination of unit tests, integration tests, and manual exploratory testing ensures reliability while maintaining fast feedback loops for developers.

**Key Takeaways**:
- ✅ Run tests before every commit: `python -m pytest app/tests -q`
- ✅ Use fixtures to simplify test setup
- ✅ Follow AAA pattern for readability
- ✅ Combine automated and manual testing for full coverage
- ✅ Monitor coverage: `python -m pytest app/tests --cov=app --cov-report=html`

For questions or contributions, refer to the main [README](README.md) or contact the development team.
