# PawRes API Reference

Comprehensive API documentation for all PawRes service classes. Services provide business logic and data access for the application.

---

## Table of Contents

1. [AuthService](#authservice) - Authentication and user registration
2. [AnimalService](#animalservice) - Animal CRUD operations
3. [RescueService](#rescueservice) - Rescue mission management
4. [AdoptionService](#adoptionservice) - Adoption request handling
5. [UserService](#userservice) - User management (admin operations)
6. [AnalyticsService](#analyticsservice) - Dashboard statistics and metrics
7. [AIClassificationService](#aiclassificationservice) - AI-powered animal breed detection
8. [MapService](#mapservice) - Geocoding and location services
9. [PhotoService](#photoservice) - Photo loading and validation
10. [ImportService](#importservice) - Bulk animal data import
11. [LoggingService](#loggingservice) - Structured logging
12. [PasswordPolicy](#passwordpolicy) - Password validation and enforcement

---

## AuthService

Authentication service with PBKDF2-HMAC-SHA256 password hashing, login lockout, and OAuth support.

**Location**: `app/services/auth_service.py`

### Constructor

```python
def __init__(
    self,
    db: Optional[Database | str] = None,
    *,
    ensure_tables: bool = True,
) -> None
```

**Parameters**:
- `db`: Database instance or path to SQLite file (defaults to `app_config.DB_PATH`)
- `ensure_tables`: If True, creates required database tables on initialization

**Example**:
```python
from services.auth_service import AuthService
from storage.database import Database

# Using default database path
auth_service = AuthService()

# Using custom database path
auth_service = AuthService(db="path/to/custom.db")

# Using existing Database instance
db = Database("path/to/db.sqlite")
auth_service = AuthService(db=db)
```

---

### register_user()

Create a new user account with password hashing and validation.

```python
def register_user(
    self,
    name: str,
    email: Optional[str] = None,
    password: str = "",
    phone: Optional[str] = None,
    role: str = "user",
    skip_policy: bool = False,
    profile_picture: Optional[str] = None
) -> int
```

**Parameters**:
- `name`: User's display name (max 100 characters)
- `email`: Unique email address (max 255 characters) - optional if phone provided
- `password`: Plain-text password meeting policy requirements
- `phone`: Phone number (will be normalized to E.164 format)
- `role`: User role - `"user"` or `"admin"` (default: `"user"`)
- `skip_policy`: Skip password policy validation (for testing only)
- `profile_picture`: Optional filename of uploaded profile picture

**Returns**: `int` - The new user's ID

**Raises**:
- `ValueError`: If email/phone already exists, validation fails, or invalid input
- `AuthServiceError`: If database operation fails

**Example**:
```python
# Register a new user
try:
    user_id = auth_service.register_user(
        name="John Doe",
        email="john@example.com",
        password="SecureP@ss123",
        phone="+639171234567"
    )
    print(f"User registered with ID: {user_id}")
except ValueError as e:
    print(f"Registration failed: {e}")
```

---

### login()

Verify user credentials and return authentication result.

```python
def login(
    self,
    email_or_phone: str,
    password: str
) -> Tuple[Optional[Dict[str, Any]], AuthResult]
```

**Parameters**:
- `email_or_phone`: User's email address or phone number
- `password`: Plain-text password to verify

**Returns**: `Tuple[Optional[Dict], AuthResult]`
- First element: User dictionary with keys `id`, `name`, `email`, `role`, etc., or `None` if failed
- Second element: `AuthResult` enum indicating success or failure reason

**AuthResult Values**:
- `SUCCESS`: Login successful
- `INVALID_CREDENTIALS`: Wrong password
- `USER_NOT_FOUND`: No user with provided email/phone
- `ACCOUNT_LOCKED`: Too many failed attempts
- `ACCOUNT_DISABLED`: Account disabled by admin
- `INVALID_INPUT`: Missing email/password

**Example**:
```python
user, result = auth_service.login("john@example.com", "SecureP@ss123")

if result == AuthResult.SUCCESS:
    print(f"Welcome {user['name']}!")
    print(f"User ID: {user['id']}, Role: {user['role']}")
elif result == AuthResult.INVALID_CREDENTIALS:
    print("Invalid email or password")
elif result == AuthResult.ACCOUNT_LOCKED:
    print("Account locked due to too many failed attempts")
```

---

### create_oauth_user()

Create or retrieve user account for OAuth authentication (e.g., Google Sign-In).

```python
def create_oauth_user(
    self,
    email: str,
    name: str,
    provider: str,
    profile_picture: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters**:
- `email`: User's email from OAuth provider
- `name`: User's display name from OAuth provider
- `provider`: OAuth provider name (e.g., `"google"`)
- `profile_picture`: URL or filename of profile picture

**Returns**: `Dict` with keys:
- `user_id`: User's ID (int)
- `is_new`: Whether user was newly created (bool)
- `result`: `AuthResult` enum

**Example**:
```python
result = auth_service.create_oauth_user(
    email="john@gmail.com",
    name="John Doe",
    provider="google",
    profile_picture="https://example.com/photo.jpg"
)

if result['is_new']:
    print(f"New user created with ID: {result['user_id']}")
else:
    print(f"Existing user logged in: {result['user_id']}")
```

---

### verify_password()

Check if a password is correct for a user (without logging in).

```python
def verify_password(self, user_id: int, password: str) -> bool
```

**Parameters**:
- `user_id`: User's ID
- `password`: Plain-text password to verify

**Returns**: `bool` - True if password is correct

**Example**:
```python
if auth_service.verify_password(user_id=5, password="CurrentPass123"):
    print("Password verified")
else:
    print("Incorrect password")
```

---

> **Note**: End-user password changes are implemented in `UserService` and
> exposed through the profile page ("Change Password" and "Set Password" for
> OAuth users) using `change_user_password()` and `set_password_for_oauth_user()`.

---

### get_lockout_status()

Check whether an account is locked and how long until it unlocks.

```python
def get_lockout_status(self, email_or_phone: str) -> Tuple[bool, Optional[int]]
```

**Parameters**:
- `email_or_phone`: User's email address or phone number

**Returns**: `Tuple[bool, Optional[int]]`
- First element: `True` if the account is currently locked
- Second element: Remaining lockout time in whole minutes, or `None` if not locked

**Example**:
```python
is_locked, remaining = auth_service.get_lockout_status("john@example.com")
if is_locked:
    print(f"Account locked. Try again in {remaining} minute(s).")
```

---

### get_failed_login_attempts()

Get the current failed-login attempt counter for a user identifier.

```python
def get_failed_login_attempts(self, email_or_phone: str) -> Optional[int]
```

**Parameters**:
- `email_or_phone`: User's email address or phone number

**Returns**: `Optional[int]` - Number of failed attempts, or `None` if no matching user

**Example**:
```python
attempts = auth_service.get_failed_login_attempts("john@example.com")
print(f"Failed attempts: {attempts if attempts is not None else 0}")
```

---

## AnimalService

Service for CRUD operations on animal records.

**Location**: `app/services/animal_service.py`

### Constructor

```python
def __init__(
    self,
    db: Optional[Database | str] = None,
    *,
    ensure_tables: bool = True
) -> None
```

**Parameters**:
- `db`: Database instance or path (defaults to `app_config.DB_PATH`)
- `ensure_tables`: If True, creates required tables on init

---

### get_all_animals()

Retrieve all animal records.

```python
def get_all_animals(self) -> List[Dict[str, Any]]
```

**Returns**: `List[Dict]` - List of animal dictionaries with DB column names

**Animal Dict Keys**: `id`, `name`, `species`, `breed`, `age`, `status`, `photo`, `created_at`, `updated_at`

**Example**:
```python
animals = animal_service.get_all_animals()
for animal in animals:
    print(f"{animal['name']} ({animal['species']}) - {animal['status']}")
```

---

### get_adoptable_animals()

Retrieve animals available for adoption.

```python
def get_adoptable_animals(self) -> List[Dict[str, Any]]
```

**Returns**: `List[Dict]` - Animals with status in `ADOPTABLE_STATUSES` (healthy, recovering)

**Example**:
```python
adoptable = animal_service.get_adoptable_animals()
print(f"Found {len(adoptable)} adoptable animals")
```

---

### get_animal_by_id()

Retrieve a single animal by ID.

```python
def get_animal_by_id(self, animal_id: int) -> Optional[Dict[str, Any]]
```

**Parameters**:
- `animal_id`: Animal's ID

**Returns**: `Optional[Dict]` - Animal dictionary or None if not found

**Example**:
```python
animal = animal_service.get_animal_by_id(123)
if animal:
    print(f"Found: {animal['name']}")
else:
    print("Animal not found")
```

---

### create_animal()

Add a new animal to the database.

```python
def create_animal(
    self,
    name: str,
    species: str,
    breed: Optional[str] = None,
    age: Optional[int] = None,
    status: str = "healthy",
    photo: Optional[str] = None,
    rescue_mission_id: Optional[int] = None
) -> int
```

**Parameters**:
- `name`: Animal's name
- `species`: Species type (e.g., "dog", "cat", "other")
- `breed`: Breed name
- `age`: Age in years
- `status`: Health status (default: "healthy")
- `photo`: Photo filename from FileStore
- `rescue_mission_id`: ID of associated rescue mission

**Returns**: `int` - The new animal's ID

**Example**:
```python
animal_id = animal_service.create_animal(
    name="Buddy",
    species="dog",
    breed="Golden Retriever",
    age=3,
    status="healthy",
    photo="buddy_20231208.jpg"
)
print(f"Animal created with ID: {animal_id}")
```

---

### update_animal()

Update an existing animal's information.

```python
def update_animal(self, animal_id: int, **kwargs: Any) -> bool
```

**Parameters**:
- `animal_id`: Animal's ID
- `**kwargs`: Fields to update (name, type/species, age, health_status/status, photo, breed)

**Returns**: `bool` - True if updated successfully

**Example**:
```python
success = animal_service.update_animal(
    animal_id=123,
    name="Buddy Jr.",
    age=4,
    status="recovering"
)
if success:
    print("Animal updated")
```

---

### delete_animal()

Permanently delete an animal record (hard delete).

```python
def delete_animal(self, animal_id: int) -> bool
```

**Parameters**:
- `animal_id`: Animal's ID

**Returns**: `bool` - True if deleted

**Warning**: This is a permanent deletion. Consider using `archive_animal()` or `remove_animal()` instead.

**Example**:
```python
if animal_service.delete_animal(animal_id=123):
    print("Animal permanently deleted")
```

---

### update_photo()

Update an animal's photo, deleting the old photo file.

```python
def update_photo(self, animal_id: int, photo: str) -> bool
```

**Parameters**:
- `animal_id`: Animal's ID
- `photo`: New photo filename from FileStore

**Returns**: `bool` - True if updated

**Example**:
```python
animal_service.update_photo(animal_id=123, photo="new_photo.jpg")
```

---

### archive_animal()

Archive an animal (soft-hide, still counts in analytics).

```python
def archive_animal(
    self,
    animal_id: int,
    archived_by: int,
    note: Optional[str] = None
) -> bool
```

**Parameters**:
- `animal_id`: Animal's ID
- `archived_by`: Admin user ID performing the action
- `note`: Optional note explaining why archived

**Returns**: `bool` - True if archived

**Note**: Status becomes "original_status|archived" to preserve original for analytics.

**Example**:
```python
animal_service.archive_animal(
    animal_id=123,
    archived_by=1,
    note="Animal was adopted outside the system"
)
```

---

### remove_animal()

Remove an animal (soft-delete, excluded from analytics).

```python
def remove_animal(
    self,
    animal_id: int,
    removed_by: int,
    reason: str
) -> bool
```

**Parameters**:
- `animal_id`: Animal's ID
- `removed_by`: Admin user ID performing the action
- `reason`: Reason for removal (required)

**Returns**: `bool` - True if removed

**Use Cases**: Spam, duplicates, test data, invalid entries

**Example**:
```python
animal_service.remove_animal(
    animal_id=999,
    removed_by=1,
    reason="Duplicate entry"
)
```

---

## RescueService

Service for managing rescue mission requests and status updates.

**Location**: `app/services/rescue_service.py`

### Constructor

```python
def __init__(
    self,
    db: Optional[Database | str] = None,
    *,
    ensure_tables: bool = True
) -> None
```

---

### create_rescue_mission()

Submit a new rescue mission request.

```python
def create_rescue_mission(
    self,
    user_id: Optional[int],
    location: str,
    animal_id: Optional[int] = None,
    animal_type: Optional[str] = None,
    breed: Optional[str] = None,
    name: Optional[str] = None,
    details: Optional[str] = None,
    status: str = RescueStatus.PENDING,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    reporter_name: Optional[str] = None,
    reporter_phone: Optional[str] = None,
    urgency: str = Urgency.MEDIUM,
    animal_photo: Optional[str] = None
) -> int
```

**Parameters**:
- `user_id`: ID of user submitting the request (optional for guest submissions)
- `location`: Location description of rescue site
- `animal_id`: ID of existing animal (if applicable)
- `animal_type`: Type of animal (dog, cat, other)
- `breed`: Animal's breed if known
- `name`: Animal's name if known
- `details`: Additional notes about the rescue situation
- `status`: Initial status (default: "pending")
- `latitude`: GPS latitude coordinate
- `longitude`: GPS longitude coordinate
- `reporter_name`: Name of person reporting (for guest submissions)
- `reporter_phone`: Contact phone number
- `urgency`: Urgency level ("low", "medium", "high", "critical")
- `animal_photo`: Photo filename if uploaded

**Returns**: `int` - The new rescue mission ID

**Example**:
```python
mission_id = rescue_service.create_rescue_mission(
    user_id=5,
    location="123 Main St, Manila",
    animal_type="dog",
    breed="Aspin",
    details="Injured dog found near road",
    latitude=14.5995,
    longitude=120.9842,
    urgency="high",
    reporter_phone="+639171234567"
)
print(f"Rescue mission created: {mission_id}")
```

---

### get_all_rescue_missions()

Retrieve all rescue missions.

```python
def get_all_rescue_missions(self) -> List[Dict[str, Any]]
```

**Returns**: `List[Dict]` - List of rescue mission dictionaries

**Example**:
```python
missions = rescue_service.get_all_rescue_missions()
for mission in missions:
    print(f"Mission {mission['id']}: {mission['status']}")
```

---

### get_rescue_missions_by_user()

Retrieve rescue missions submitted by a specific user.

```python
def get_rescue_missions_by_user(self, user_id: int) -> List[Dict[str, Any]]
```

**Parameters**:
- `user_id`: User's ID

**Returns**: `List[Dict]` - User's rescue missions

**Example**:
```python
user_missions = rescue_service.get_rescue_missions_by_user(user_id=5)
print(f"User has {len(user_missions)} rescue missions")
```

---

### update_rescue_status()

Update the status of a rescue mission (admin action).

```python
def update_rescue_status(
    self,
    mission_id: int,
    new_status: str,
    admin_message: Optional[str] = None,
    admin_id: Optional[int] = None
) -> bool
```

**Parameters**:
- `mission_id`: Rescue mission ID
- `new_status`: New status value
- `admin_message`: Optional message to reporter
- `admin_id`: ID of admin performing the update

**Returns**: `bool` - True if updated

**Status Values**: `"pending"`, `"on-going"`, `"rescued"`, `"failed"`, `"cancelled"`

**Auto-Actions**:
- When status changes TO "rescued": Automatically creates an animal entry from mission details
- When status changes FROM "rescued": Deletes the auto-created animal (if no adoptions exist)

**Example**:
```python
rescue_service.update_rescue_status(
    mission_id=42,
    new_status="rescued",
    admin_message="Animal successfully rescued and brought to shelter",
    admin_id=1
)
```

---

### archive_rescue()

Archive a rescue mission (soft-hide).

```python
def archive_rescue(
    self,
    mission_id: int,
    archived_by: int,
    note: Optional[str] = None
) -> bool
```

**Parameters**:
- `mission_id`: Rescue mission ID
- `archived_by`: Admin user ID
- `note`: Optional note

**Returns**: `bool` - True if archived

**Example**:
```python
rescue_service.archive_rescue(
    mission_id=42,
    archived_by=1,
    note="Resolved through external channel"
)
```

---

### remove_rescue()

Remove a rescue mission (soft-delete).

```python
def remove_rescue(
    self,
    mission_id: int,
    removed_by: int,
    reason: str
) -> bool
```

**Parameters**:
- `mission_id`: Rescue mission ID
- `removed_by`: Admin user ID
- `reason`: Reason for removal

**Returns**: `bool` - True if removed

**Example**:
```python
rescue_service.remove_rescue(
    mission_id=999,
    removed_by=1,
    reason="Spam report"
)
```

---

## AdoptionService

Service for managing adoption requests and approvals.

**Location**: `app/services/adoption_service.py`

### Constructor

```python
def __init__(
    self,
    db: Optional[Database | str] = None,
    *,
    ensure_tables: bool = True
) -> None
```

---

### create_adoption_request()

Submit a new adoption request.

```python
def create_adoption_request(
    self,
    user_id: int,
    animal_id: int,
    contact: str,
    reason: str
) -> int
```

**Parameters**:
- `user_id`: ID of user requesting adoption
- `animal_id`: ID of animal to adopt
- `contact`: Contact information (email/phone)
- `reason`: Explanation for why user wants to adopt

**Returns**: `int` - The new adoption request ID

**Example**:
```python
request_id = adoption_service.create_adoption_request(
    user_id=5,
    animal_id=123,
    contact="+639171234567",
    reason="I have experience with this breed and a large backyard"
)
print(f"Adoption request submitted: {request_id}")
```

---

### get_all_adoption_requests()

Retrieve all adoption requests with user and animal details.

```python
def get_all_adoption_requests(self) -> List[Dict[str, Any]]
```

**Returns**: `List[Dict]` - Adoption requests with joined user and animal data

**Dict Keys**: `id`, `user_id`, `animal_id`, `contact`, `reason`, `status`, `request_date`, `user_name`, `user_email`, `animal_name`, `animal_species`, etc.

**Example**:
```python
requests = adoption_service.get_all_adoption_requests()
for req in requests:
    print(f"{req['user_name']} wants to adopt {req['animal_name']}")
```

---

### get_requests_by_user()

Retrieve adoption requests submitted by a specific user.

```python
def get_requests_by_user(self, user_id: int) -> List[Dict[str, Any]]
```

**Parameters**:
- `user_id`: User's ID

**Returns**: `List[Dict]` - User's adoption requests

**Example**:
```python
my_requests = adoption_service.get_requests_by_user(user_id=5)
```

---

### get_requests_by_animal()

Retrieve adoption requests for a specific animal.

```python
def get_requests_by_animal(self, animal_id: int) -> List[Dict[str, Any]]
```

**Parameters**:
- `animal_id`: Animal's ID

**Returns**: `List[Dict]` - Adoption requests for this animal

**Example**:
```python
animal_requests = adoption_service.get_requests_by_animal(animal_id=123)
print(f"This animal has {len(animal_requests)} adoption requests")
```

---

### approve_request()

Approve an adoption request (admin action).

```python
def approve_request(
    self,
    request_id: int,
    admin_message: Optional[str] = None,
    admin_id: Optional[int] = None
) -> Dict[str, Any]
```

**Parameters**:
- `request_id`: Adoption request ID
- `admin_message`: Optional message to adopter
- `admin_id`: ID of admin approving the request

**Returns**: `Dict` with keys:
- `success`: Whether approval succeeded (bool)
- `message`: Result message (str)

**Auto-Actions**:
- Sets animal status to "adopted"
- Auto-denies all other pending requests for the same animal
- Records approval timestamp

**Example**:
```python
result = adoption_service.approve_request(
    request_id=42,
    admin_message="Congratulations! Please visit the shelter to complete adoption.",
    admin_id=1
)
if result['success']:
    print("Adoption approved!")
```

---

### deny_request()

Deny an adoption request (admin action).

```python
def deny_request(
    self,
    request_id: int,
    denial_reason: str,
    admin_message: Optional[str] = None,
    admin_id: Optional[int] = None
) -> bool
```

**Parameters**:
- `request_id`: Adoption request ID
- `denial_reason`: Reason for denial (required)
- `admin_message`: Optional message to applicant
- `admin_id`: ID of admin denying the request

**Returns**: `bool` - True if denied

**Example**:
```python
adoption_service.deny_request(
    request_id=42,
    denial_reason="Incomplete application",
    admin_message="Please provide more details about your housing situation",
    admin_id=1
)
```

---

### cancel_request()

Cancel an adoption request (user action).

```python
def cancel_request(self, request_id: int, user_id: int) -> bool
```

**Parameters**:
- `request_id`: Adoption request ID
- `user_id`: User ID canceling the request (must be request owner)

**Returns**: `bool` - True if cancelled

**Note**: Only pending requests can be cancelled.

**Example**:
```python
if adoption_service.cancel_request(request_id=42, user_id=5):
    print("Request cancelled")
```

---

### update_request()

Update an adoption request's contact and reason.

```python
def update_request(
    self,
    request_id: int,
    **kwargs: Any
) -> bool
```

**Parameters**:
- `request_id`: Adoption request ID
- `**kwargs`: Fields to update (contact, reason)

**Returns**: `bool` - True if updated

**Example**:
```python
adoption_service.update_request(
    request_id=42,
    contact="newemail@example.com",
    reason="Updated: I now have a fenced yard"
)
```

---

## UserService

Service for user management operations (admin functions).

**Location**: `app/services/user_service.py`

### Constructor

```python
def __init__(self, db_path: Optional[str] = None)
```

---

### get_user_by_id()

Retrieve a user by ID.

```python
def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]
```

**Parameters**:
- `user_id`: User's ID

**Returns**: `Optional[Dict]` - User dictionary (without password fields) or None

**Example**:
```python
user = user_service.get_user_by_id(5)
if user:
    print(f"User: {user['name']} ({user['email']})")
```

---

### get_user_by_email()

Retrieve a user by email address.

```python
def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]
```

**Parameters**:
- `email`: User's email address

**Returns**: `Optional[Dict]` - User dictionary or None

**Example**:
```python
user = user_service.get_user_by_email("john@example.com")
```

---

### get_all_users()

Retrieve all user accounts.

```python
def get_all_users(self) -> List[Dict[str, Any]]
```

**Returns**: `List[Dict]` - List of all users (without password fields)

**Example**:
```python
users = user_service.get_all_users()
print(f"Total users: {len(users)}")
```

---

### search_users()

Search users by name or email.

```python
def search_users(self, query: str) -> List[Dict[str, Any]]
```

**Parameters**:
- `query`: Search term (searches name and email fields)

**Returns**: `List[Dict]` - Matching users

**Example**:
```python
results = user_service.search_users("john")
for user in results:
    print(f"{user['name']} - {user['email']}")
```

---

### disable_user()

Disable a user account (admin action).

```python
def disable_user(self, user_id: int, admin_id: int) -> bool
```

**Parameters**:
- `user_id`: User ID to disable
- `admin_id`: ID of admin performing the action

**Returns**: `bool` - True if disabled

**Note**: Disabled users cannot log in but data is preserved.

**Example**:
```python
if user_service.disable_user(user_id=5, admin_id=1):
    print("User disabled")
```

---

### enable_user()

Re-enable a disabled user account (admin action).

```python
def enable_user(self, user_id: int, admin_id: int) -> bool
```

**Parameters**:
- `user_id`: User ID to enable
- `admin_id`: ID of admin performing the action

**Returns**: `bool` - True if enabled

**Example**:
```python
user_service.enable_user(user_id=5, admin_id=1)
```

---

### delete_user()

Permanently delete a user account (admin action).

```python
def delete_user(self, user_id: int, admin_id: int) -> bool
```

**Parameters**:
- `user_id`: User ID to delete
- `admin_id`: ID of admin performing the action

**Returns**: `bool` - True if deleted

**Warning**: This is permanent and deletes all user data.

**Example**:
```python
if user_service.delete_user(user_id=999, admin_id=1):
    print("User permanently deleted")
```

---

### reset_password()

Reset a user's password (admin action).

```python
def reset_password(
    self,
    user_id: int,
    new_password: str,
    admin_id: int
) -> bool
```

**Parameters**:
- `user_id`: User ID to reset password for
- `new_password`: New password (must meet policy requirements)
- `admin_id`: ID of admin performing the action

**Returns**: `bool` - True if password reset

**Example**:
```python
if user_service.reset_password(user_id=5, new_password="TempP@ss123", admin_id=1):
    print("Password reset successfully")
```

---

### update_profile()

Update a user's profile information.

```python
def update_profile(self, user_id: int, **kwargs: Any) -> bool
```

**Parameters**:
- `user_id`: User ID to update
- `**kwargs`: Fields to update (name, email, phone, profile_picture)

**Returns**: `bool` - True if updated

**Example**:
```python
user_service.update_profile(
    user_id=5,
    name="John Smith",
    phone="+639179999999"
)
```

---

### change_user_password()

Change the current user's password from the profile page (self-service).

```python
def change_user_password(
    self,
    user_id: int,
    current_password: str,
    new_password: str
) -> Dict[str, Any]
```

**Parameters**:
- `user_id`: ID of the user changing their own password
- `current_password`: Current password (used for verification)
- `new_password`: New password (must pass password policy and history checks)

**Returns**: `Dict` with keys:
- `success`: `True` if the password was changed
- `error`: Optional error message when `success` is `False`

**Behavior**:
- Verifies the current password using PBKDF2-HMAC-SHA256 and `PBKDF2_ITERATIONS` from `app_config`.
- Rejects changes for OAuth-only accounts (these must use `set_password_for_oauth_user`).
- Validates the new password against the configured password policy.
- Prevents reuse of recent passwords via `PasswordHistoryManager`.

**Example**:
```python
result = user_service.change_user_password(
    user_id=5,
    current_password="OldP@ss123",
    new_password="NewP@ss456!"
)

if result["success"]:
    print("Password changed successfully")
else:
    print(f"Error: {result['error']}")
```

---

### set_password_for_oauth_user()

Set an initial password for an OAuth-only account (self-service).

```python
def set_password_for_oauth_user(
    self,
    user_id: int,
    new_password: str
) -> Dict[str, Any]
```

**Parameters**:
- `user_id`: ID of the OAuth user setting a password
- `new_password`: New password to set (must pass password policy)

**Returns**: `Dict` with keys:
- `success`: `True` if the password was set
- `error`: Optional error message when `success` is `False`

**Behavior**:
- Only allowed for users with an `oauth_provider` set and no existing password hash.
- Validates the new password against the configured password policy.
- Hashes and stores the password using PBKDF2-HMAC-SHA256 and records it in password history.

**Example**:
```python
result = user_service.set_password_for_oauth_user(
    user_id=5,
    new_password="MyFirstP@ss123"
)

if result["success"]:
    print("Password set successfully")
else:
    print(f"Error: {result['error']}")
```

---

## AnalyticsService

Service for generating dashboard statistics and trend data.

**Location**: `app/services/analytics_service.py`

### Constructor

```python
def __init__(self, db: Optional[Database | str] = None) -> None
```

---

### get_dashboard_stats()

Get summary statistics for the admin dashboard.

```python
def get_dashboard_stats(self) -> Dict[str, int]
```

**Returns**: `Dict` with keys:
- `total_animals`: Total number of animals
- `total_rescues`: Total rescue missions
- `total_adoptions`: Total adoption requests
- `pending_requests`: Pending adoption requests count

**Example**:
```python
stats = analytics_service.get_dashboard_stats()
print(f"Animals: {stats['total_animals']}")
print(f"Pending Adoptions: {stats['pending_requests']}")
```

---

### get_rescue_trend()

Get rescue mission trend data for charts.

```python
def get_rescue_trend(self, days: int = 14) -> List[Tuple[str, int]]
```

**Parameters**:
- `days`: Number of days to analyze (default: 14)

**Returns**: `List[Tuple[str, int]]` - List of (date_string, count) tuples

**Example**:
```python
trend = analytics_service.get_rescue_trend(days=30)
for date, count in trend:
    print(f"{date}: {count} rescues")
```

---

### get_adoption_trend()

Get adoption approval trend data for charts.

```python
def get_adoption_trend(self, days: int = 14) -> List[Tuple[str, int]]
```

**Parameters**:
- `days`: Number of days to analyze (default: 14)

**Returns**: `List[Tuple[str, int]]` - List of (date_string, count) tuples

**Example**:
```python
trend = analytics_service.get_adoption_trend(days=14)
```

---

### get_animal_distribution()

Get count of animals by species type.

```python
def get_animal_distribution(self) -> Dict[str, int]
```

**Returns**: `Dict[str, int]` - Species type mapped to count (e.g., `{"dog": 15, "cat": 8}`)

**Example**:
```python
distribution = analytics_service.get_animal_distribution()
for species, count in distribution.items():
    print(f"{species}: {count}")
```

---

### get_monthly_comparison()

Get current vs previous month comparison metrics.

```python
def get_monthly_comparison(self) -> Dict[str, Any]
```

**Returns**: `Dict` with keys:
- `current_month_rescues`: Rescue count this month
- `previous_month_rescues`: Rescue count last month
- `current_month_adoptions`: Adoption count this month
- `previous_month_adoptions`: Adoption count last month

**Example**:
```python
comparison = analytics_service.get_monthly_comparison()
print(f"This month: {comparison['current_month_rescues']} rescues")
print(f"Last month: {comparison['previous_month_rescues']} rescues")
```

---

## AIClassificationService

AI-powered animal breed detection using HuggingFace transformers.

**Location**: `app/services/ai_classification_service.py`

### Constructor

```python
def __init__(self)
```

**Note**: Uses singleton pattern - only one instance is created.

---

### classify_image()

Classify an animal image to detect species and breed.

```python
def classify_image(
    self,
    image_path_or_bytes: Union[str, bytes]
) -> ClassificationResult
```

**Parameters**:
- `image_path_or_bytes`: File path to image or raw image bytes

**Returns**: `ClassificationResult` object with:
- `species`: Detected species ("Dog", "Cat", "Other", or "Not Specified Species")
- `breed`: Detected breed or "Mixed Breed" (Aspin/Puspin)
- `confidence`: Confidence score (0.0 to 1.0)
- `top_predictions`: List of top N predictions with confidence scores
- `error`: Error message if classification failed

**Example**:
```python
result = ai_service.classify_image("path/to/dog.jpg")

if result.error:
    print(f"Error: {result.error}")
else:
    print(f"Species: {result.species}")
    print(f"Breed: {result.breed}")
    print(f"Confidence: {result.confidence:.2%}")
    
    for pred in result.top_predictions:
        print(f"  {pred.label}: {pred.confidence:.2%}")
```

---

### download_models()

Download AI models from HuggingFace (required on first use).

```python
def download_models(
    self,
    on_progress: Optional[Callable[[str, float], None]] = None,
    on_error: Optional[Callable[[str], None]] = None
) -> bool
```

**Parameters**:
- `on_progress`: Callback function `(message: str, progress: float)` for progress updates
- `on_error`: Callback function `(error_message: str)` for error handling

**Returns**: `bool` - True if download successful

**Example**:
```python
def progress_callback(message, progress):
    print(f"{message} - {progress:.0%}")

def error_callback(error):
    print(f"Download failed: {error}")

success = ai_service.download_models(
    on_progress=progress_callback,
    on_error=error_callback
)
```

---

### are_models_downloaded()

Check if AI models are already downloaded.

```python
def are_models_downloaded(self) -> bool
```

**Returns**: `bool` - True if models are available locally

**Example**:
```python
if ai_service.are_models_downloaded():
    print("Models ready")
else:
    print("Need to download models first")
```

---

### cancel_download()

Cancel an in-progress model download.

```python
def cancel_download(self) -> None
```

**Example**:
```python
ai_service.cancel_download()
```

---

## MapService

Service for geocoding locations and creating maps.

**Location**: `app/services/map_service.py`

### Constructor

```python
def __init__(self)
```

---

### geocode_location()

Convert an address string to GPS coordinates.

```python
def geocode_location(
    self,
    address: str
) -> Optional[Tuple[float, float]]
```

**Parameters**:
- `address`: Address or location description

**Returns**: `Optional[Tuple[float, float]]` - (latitude, longitude) or None if not found

**Example**:
```python
coords = map_service.geocode_location("123 Main St, Manila, Philippines")
if coords:
    lat, lon = coords
    print(f"Location: {lat}, {lon}")
else:
    print("Address not found")
```

---

### reverse_geocode()

Convert GPS coordinates to an address string.

```python
def reverse_geocode(
    self,
    latitude: float,
    longitude: float
) -> Optional[str]
```

**Parameters**:
- `latitude`: GPS latitude
- `longitude`: GPS longitude

**Returns**: `Optional[str]` - Address string or None if not found

**Example**:
```python
address = map_service.reverse_geocode(14.5995, 120.9842)
if address:
    print(f"Address: {address}")
```

---

## PhotoService

Service for loading, validating, and managing photos.

**Location**: `app/services/photo_service.py`

### Constructor

```python
def __init__(self)
```

---

### load_photo()

Load a photo and return as base64 string.

```python
def load_photo(self, photo: Optional[str]) -> Optional[str]
```

**Parameters**:
- `photo`: Filename (from FileStore) or base64 string

**Returns**: `Optional[str]` - Base64 encoded image data or None if not found

**Note**: Handles both legacy base64 format and new filename format.

**Example**:
```python
photo_base64 = photo_service.load_photo("dog_photo.jpg")
if photo_base64:
    # Use in Flet Image widget
    ft.Image(src_base64=photo_base64, width=200, height=200)
```

---

### save_photo()

Save photo file data to storage.

```python
def save_photo(
    self,
    file_data: Union[bytes, str],
    original_name: str
) -> str
```

**Parameters**:
- `file_data`: Raw file bytes or base64 string
- `original_name`: Original filename (for extension detection)

**Returns**: `str` - Saved filename

**Raises**:
- `PhotoServiceError`: If validation fails or save fails

**Example**:
```python
with open("photo.jpg", "rb") as f:
    file_bytes = f.read()

filename = photo_service.save_photo(file_bytes, "photo.jpg")
print(f"Saved as: {filename}")
```

---

## ImportService

Service for bulk importing animal data from CSV/Excel files.

**Location**: `app/services/import_service.py`

### Constructor

```python
def __init__(self, db_path: Optional[str] = None) -> None
```

---

### import_animals_from_file()

Import animals from a CSV or Excel file.

```python
def import_from_file(self, file_path: str) -> ImportResult
```

**Parameters**:
- `file_path`: Path to CSV or Excel file (.csv, .xlsx, .xls)

**Returns**: `ImportResult` object with:
- `success_count`: Number of animals successfully imported
- `errors`: List of `ImportError` objects (row number and message)
- `total_rows`: Total rows processed
- `has_errors`: Whether any errors occurred
- `all_failed`: Whether all rows failed

**CSV Format**:
- Required columns: `name`, `type`, `age`, `health_status`
- Optional columns: `photo`, `breed`
- Comment lines starting with `#` are ignored

**Example**:
```python
result = import_service.import_from_file("animals.csv")

print(f"Successfully imported: {result.success_count}")
print(f"Total rows: {result.total_rows}")

if result.has_errors:
    print("Errors:")
    for error in result.errors:
        print(f"  Row {error.row}: {error.message}")
```

---

## LoggingService

Structured logging service for authentication, admin actions, and security events.

**Location**: `app/services/logging_service.py`

### Functions

#### log_auth_event()

Log an authentication-related event.

```python
def log_auth_event(
    event_type: str,
    **kwargs: Any
) -> None
```

**Parameters**:
- `event_type`: Event type (e.g., "login_success", "login_failure", "registration")
- `**kwargs`: Additional context (email, user_id, reason, etc.)

**Example**:
```python
from services.logging_service import log_auth_event

log_auth_event(
    "login_success",
    email="john@example.com",
    user_id=5,
    oauth_provider=None
)
```

---

#### log_admin_action()

Log an administrative action.

```python
def log_admin_action(
    action_type: str,
    **kwargs: Any
) -> None
```

**Parameters**:
- `action_type`: Action type (e.g., "user_disabled", "animal_deleted")
- `**kwargs`: Additional context (admin_id, target_id, reason, etc.)

**Example**:
```python
from services.logging_service import log_admin_action

log_admin_action(
    "user_disabled",
    admin_id=1,
    target_user_id=5,
    reason="Policy violation"
)
```

---

#### log_security_event()

Log a security-related event.

```python
def log_security_event(
    event_type: str,
    **kwargs: Any
) -> None
```

**Parameters**:
- `event_type`: Event type (e.g., "account_locked", "password_reset")
- `**kwargs`: Additional context (user_id, reason, ip_address, etc.)

**Example**:
```python
from services.logging_service import log_security_event

log_security_event(
    "account_locked",
    user_id=5,
    reason="Too many failed login attempts",
    attempt_count=5
)
```

---

## PasswordPolicy

Password validation and enforcement service.

**Location**: `app/services/password_policy.py`

### Constructor

```python
def __init__(
    self,
    min_length: int = None,
    require_uppercase: bool = None,
    require_lowercase: bool = None,
    require_digit: bool = None,
    require_special: bool = None,
    history_count: int = None
)
```

**Parameters** (all optional, defaults from `app_config`):
- `min_length`: Minimum password length (default: 8)
- `require_uppercase`: Require uppercase letter (default: True)
- `require_lowercase`: Require lowercase letter (default: True)
- `require_digit`: Require digit (default: True)
- `require_special`: Require special character (default: True)
- `history_count`: Number of previous passwords to check for reuse (default: 5)

---

### validate()

Validate a password against policy rules.

```python
def validate(self, password: str) -> Tuple[bool, List[str]]
```

**Parameters**:
- `password`: Password to validate

**Returns**: `Tuple[bool, List[str]]`
- First element: Whether password is valid
- Second element: List of error messages (empty if valid)

**Example**:
```python
from services.password_policy import get_password_policy

policy = get_password_policy()
is_valid, errors = policy.validate("MyP@ss123")

if is_valid:
    print("Password meets requirements")
else:
    print("Password errors:")
    for error in errors:
        print(f"  - {error}")
```

---

### get_requirements_text()

Get human-readable password requirements.

```python
def get_requirements_text(self) -> str
```

**Returns**: `str` - Formatted requirements text

**Example**:
```python
requirements = policy.get_requirements_text()
print(requirements)
# Output:
# Password must be at least 8 characters
# Password must contain at least one uppercase letter
# Password must contain at least one lowercase letter
# ...
```

---

### check_password_reuse()

Check if a password was used recently by a user.

```python
def check_password_reuse(
    self,
    user_id: int,
    password: str
) -> bool
```

**Parameters**:
- `user_id`: User's ID
- `password`: Password to check

**Returns**: `bool` - True if password was used recently (should reject)

**Example**:
```python
if policy.check_password_reuse(user_id=5, password="OldP@ss123"):
    print("Password was used recently, choose a different one")
```

---

### add_password_to_history()

Add a password to a user's password history.

```python
def add_password_to_history(
    self,
    user_id: int,
    password_hash: str,
    password_salt: str
) -> None
```

**Parameters**:
- `user_id`: User's ID
- `password_hash`: Hashed password
- `password_salt`: Password salt

**Note**: This is called automatically by AuthService when passwords are changed.

---

## Common Patterns

### Service Initialization

All services accept either a `Database` instance or a database path string:

```python
# Using default database path
service = AnimalService()

# Using custom path
service = AnimalService(db="/path/to/custom.db")

# Using existing Database instance
from storage.database import Database
db = Database("path/to/db.sqlite")
service = AnimalService(db=db)
```

### Error Handling

Services raise specific exceptions or return result objects:

```python
# AuthService raises ValueError for validation errors
try:
    user_id = auth_service.register_user(name="John", email="invalid", password="weak")
except ValueError as e:
    print(f"Validation error: {e}")
except AuthServiceError as e:
    print(f"Database error: {e}")

# ImportService returns result objects
result = import_service.import_from_file("data.csv")
if result.has_errors:
    for error in result.errors:
        print(f"Row {error.row}: {error.message}")
```

### Status Constants

Use status constants from `app_config` for consistency:

```python
from app_config import AnimalStatus, RescueStatus, AdoptionStatus

# Check status
if animal['status'] == AnimalStatus.ADOPTED:
    print("Animal is adopted")

# Normalize status (handles case and variants)
normalized = RescueStatus.normalize("ON-GOING")  # Returns "on-going"

# Check if archived
if AnimalStatus.is_archived(animal['status']):
    print("Animal is archived")

# Check if active
if RescueStatus.is_active(mission['status']):
    print("Mission is active (pending or on-going)")
```

### Using PhotoService

```python
from services.photo_service import get_photo_service

photo_service = get_photo_service()

# Load photo for display
photo_b64 = photo_service.load_photo(animal['photo'])
if photo_b64:
    ft.Image(src_base64=photo_b64, width=200, height=200)

# Save uploaded photo
filename = photo_service.save_photo(file_bytes, "original.jpg")
animal_service.update_animal(animal_id, photo=filename)
```

---

## Testing

All services support testing with temporary databases:

```python
import pytest
from services.auth_service import AuthService

def test_registration():
    # Use in-memory database for testing
    service = AuthService(db=":memory:")
    
    user_id = service.register_user(
        name="Test User",
        email="test@test.com",
        password="TestP@ss123",
        skip_policy=False
    )
    
    assert user_id > 0
```

Fixtures are provided in `app/tests/conftest.py` for common test scenarios.

---

## Related Documentation

- **Database Schema**: See [DATABASE.md](DATABASE.md)
- **Security Features**: See [SECURITY.md](SECURITY.md)
- **Testing Guide**: See [TESTING.md](TESTING.md)
- **Architecture Overview**: See [ARCHITECTURE.md](ARCHITECTURE.md)

---

*Generated: December 8, 2025*  
*PawRes Version: 1.0*
