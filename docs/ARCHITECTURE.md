# System Architecture Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architectural Layers](#architectural-layers)
3. [Component Diagrams](#component-diagrams)
4. [Design Patterns](#design-patterns)
5. [Data Flow](#data-flow)
6. [Module Dependencies](#module-dependencies)
7. [Configuration Management](#configuration-management)

---

## Diagram Rendering Note

If the Mermaid diagrams in this document do not render in your editor or preview, here are quick options to view or generate them:

- Quick view (no install): Open the Mermaid Live Editor at https://mermaid.live/, paste the Mermaid code block, preview, and export PNG/SVG.
- VS Code preview: Install a Markdown preview extension that supports Mermaid such as **"Markdown Preview Mermaid Support"** (`vstirbu.vscode-mermaid-preview`) or **"Markdown Preview Enhanced"** (`yzhang.markdown-preview-enhanced`), then open the Markdown preview (`Ctrl+Shift+V`).

## Overview

PawRes follows a **layered architecture pattern** with clear separation of concerns across six main layers. The architecture emphasizes modularity, testability, and maintainability through well-defined interfaces and dependency injection.

### Architecture Principles

- **Separation of Concerns**: Each layer has a distinct responsibility
- **Dependency Inversion**: Services depend on abstractions (Database interface), not concrete implementations
- **Single Responsibility**: Components handle one aspect of functionality
- **Observable State**: Reactive state management for UI updates
- **Component-Based UI**: Reusable, styled components for consistency

---

## Architectural Layers

```mermaid
graph TB
    subgraph "Layer 1: Presentation"
        Views[Views<br/>Page Classes]
        Components[Components<br/>Reusable UI Elements]
    end
    
    subgraph "Layer 2: Routing"
        Routes[Route Registry<br/>URL → Handler Mapping]
        Middleware[Middleware<br/>Auth & Session Validation]
    end
    
    subgraph "Layer 3: Business Logic"
        AuthSvc[Auth Service]
        AnimalSvc[Animal Service]
        RescueSvc[Rescue Service]
        AdoptionSvc[Adoption Service]
        UserSvc[User Service]
        AnalyticsSvc[Analytics Service]
    end
    
    subgraph "Layer 4: State Management"
        AppState[App State Singleton]
        AuthState[Auth State]
        AnimalState[Animal State]
        RescueState[Rescue State]
        AdoptionState[Adoption State]
    end
    
    subgraph "Layer 5: Data Access"
        Database[(SQLite Database)]
        FileStore[File Storage]
        Cache[In-Memory Cache]
    end
    
    subgraph "Layer 6: External Integrations"
        AI[AI Classification<br/>HuggingFace Models]
        Maps[Map Service<br/>Geocoding]
        Charts[Chart Service<br/>Visualization]
        OAuth[OAuth Service<br/>Google Sign-In]
    end
    
    Views --> Routes
    Routes --> Middleware
    Middleware --> AuthSvc
    Middleware --> UserSvc
    Views --> Components
    Views --> AppState
    
    AuthSvc --> Database
    AnimalSvc --> Database
    RescueSvc --> Database
    AdoptionSvc --> Database
    UserSvc --> Database
    AnalyticsSvc --> Database
    
    AuthSvc --> AuthState
    AnimalSvc --> AnimalState
    RescueSvc --> RescueState
    AdoptionSvc --> AdoptionState
    
    AnimalSvc --> FileStore
    RescueSvc --> FileStore
    
    AnalyticsSvc --> Cache
    
    AnimalSvc --> AI
    RescueSvc --> Maps
    AnalyticsSvc --> Charts
    AuthSvc --> OAuth
    
    style Views fill:#e1f5ff
    style Routes fill:#fff3e0
    style AuthSvc fill:#f3e5f5
    style AppState fill:#e8f5e9
    style Database fill:#ffebee
    style AI fill:#fff9c4
```

---

## Component Diagrams

### 1. Presentation Layer Architecture

```mermaid
graph LR
    subgraph "Views (Pages)"
        Login[Login Page]
        Dashboard[Admin/User Dashboard]
        AnimalList[Animals List Page]
        RescueForm[Rescue Form Page]
        AdoptionForm[Adoption Form Page]
    end
    
    subgraph "Components Library"
        FormFields[Form Fields<br/>text_field, dropdown, label]
        Containers[Containers<br/>card, table, section]
        Dialogs[Dialogs<br/>confirmation, error, success]
        Charts[Charts<br/>line, pie, bar]
        Buttons[Buttons<br/>primary, secondary, icon]
        Utils[Utilities<br/>date_parser, validator]
    end
    
    Login --> FormFields
    Login --> Buttons
    Login --> Dialogs
    
    Dashboard --> Containers
    Dashboard --> Charts
    Dashboard --> Utils
    
    AnimalList --> Containers
    AnimalList --> FormFields
    
    RescueForm --> FormFields
    RescueForm --> Dialogs
    
    AdoptionForm --> FormFields
    AdoptionForm --> Dialogs
    
    style FormFields fill:#bbdefb
    style Containers fill:#c8e6c9
    style Dialogs fill:#ffccbc
    style Charts fill:#f0f4c3
```

### 2. Service Layer Architecture

```mermaid
graph TB
    subgraph "Core Services"
        AuthService[Auth Service<br/>Login, Registration, OAuth]
        UserService[User Service<br/>Profile, Search, Enable/Disable]
        AnimalService[Animal Service<br/>CRUD, Photos, Status]
        RescueService[Rescue Service<br/>Missions, Status, Auto-Animal]
        AdoptionService[Adoption Service<br/>Requests, Approval, Auto-Status]
        AnalyticsService[Analytics Service<br/>Stats, Trends, Charts]
    end
    
    subgraph "Supporting Services"
        PhotoService[Photo Service<br/>Load, Validate]
        MapService[Map Service<br/>Geocode, Reverse]
        AIService[AI Classification<br/>Species, Breed]
        ImportService[Import Service<br/>CSV, Excel]
        LoggingService[Logging Service<br/>Auth, Admin, Security]
        PasswordPolicy[Password Policy<br/>Validation, History]
    end
    
    AuthService --> PasswordPolicy
    AuthService --> LoggingService
    
    UserService --> LoggingService
    
    AnimalService --> PhotoService
    AnimalService --> AIService
    
    RescueService --> MapService
    RescueService --> PhotoService
    RescueService --> AnimalService
    
    AdoptionService --> AnimalService
    AdoptionService --> LoggingService
    
    AnalyticsService --> Cache
    
    style AuthService fill:#e1bee7
    style UserService fill:#b39ddb
    style AnimalService fill:#90caf9
    style RescueService fill:#80deea
    style AdoptionService fill:#80cbc4
    style AnalyticsService fill:#a5d6a7
```

### 3. Data Storage Architecture

```mermaid
graph TB
    subgraph "Storage Layer"
        DB[Database Class<br/>Thread-safe SQLite Wrapper]
        FileStore[File Store<br/>Upload/Download Manager]
        Cache[Cache Manager<br/>TTL-based In-Memory]
    end
    
    subgraph "Database Tables"
        Users[users]
        Animals[animals]
        Rescues[rescue_missions]
        Adoptions[adoption_requests]
    end
    
    subgraph "File System"
        Uploads[storage/uploads/<br/>Animal Photos]
        Exports[storage/data/exports/<br/>CSV/Excel Files]
        Logs[storage/data/logs/<br/>Auth, Admin, Security]
        AIModels[storage/ai_models/<br/>Downloaded Models]
    end
    
    DB --> Users
    DB --> Animals
    DB --> Rescues
    DB --> Adoptions
    
    FileStore --> Uploads
    FileStore --> Exports
    
    LoggingService --> Logs
    AIService --> AIModels
    
    Animals -->|FK: rescue_mission_id| Rescues
    Adoptions -->|FK: user_id| Users
    Adoptions -->|FK: animal_id| Animals
    Rescues -->|FK: user_id| Users
    Rescues -->|FK: animal_id| Animals
    
    style DB fill:#ffccbc
    style FileStore fill:#fff9c4
    style Cache fill:#c5e1a5
```

### 4. Authentication & Authorization Flow

```mermaid
sequenceDiagram
    participant User
    participant Page
    participant Middleware
    participant AuthService
    participant Database
    participant AppState
    
    User->>Page: Navigate to protected route
    Page->>Middleware: Check authorization
    
    alt Not authenticated
        Middleware->>Page: Redirect to login
        Page->>User: Show login page
    else Session expired
        Middleware->>AppState: Clear session
        Middleware->>Page: Redirect to login
        Page->>User: Show "Session expired" message
    else Insufficient role
        Middleware->>Page: Redirect to user dashboard
        Page->>User: Show "Access denied" message
    else Authorized
        Middleware->>Page: Allow access
        Page->>User: Render protected content
    end
    
    Note over User,Database: Login Flow
    
    User->>Page: Submit credentials
    Page->>AuthService: login(email, password)
    AuthService->>Database: Check lockout status
    
    alt Account locked
        AuthService->>Page: Return lockout error
        Page->>User: Show lockout message
    else Credentials invalid
        AuthService->>Database: Increment failed attempts
        AuthService->>Page: Return error
        Page->>User: Show error message
    else Credentials valid
        AuthService->>Database: Reset failed attempts
        AuthService->>Database: Update last_login
        AuthService->>AppState: Set session (user_id, role)
        AuthService->>Page: Return success
        Page->>User: Redirect to dashboard
    end
```

### 5. Rescue → Animal → Adoption Workflow

```mermaid
stateDiagram-v2
    [*] --> RescueSubmitted: User reports rescue
    
    RescueSubmitted --> RescuePending: Status pending
    RescuePending --> RescueOngoing: Admin marks on-going
    RescueOngoing --> RescueRescued: Admin marks rescued
    RescueOngoing --> RescueFailed: Rescue unsuccessful
    RescuePending --> RescueCancelled: User or Admin cancels
    
    RescueRescued --> AnimalCreated: Auto-create animal record
    AnimalCreated --> AnimalHealthy: Status healthy or recovering
    
    AnimalHealthy --> AdoptionAvailable: Animal shown to users
    AdoptionAvailable --> AdoptionRequested: User submits request
    AdoptionRequested --> AdoptionPending: Status pending
    
    AdoptionPending --> AdoptionApproved: Admin approves
    AdoptionPending --> AdoptionDenied: Admin denies
    AdoptionPending --> AdoptionCancelled: User cancels
    
    AdoptionApproved --> AnimalAdopted: Auto-update animal status
    AdoptionApproved --> OtherDenied: Auto-deny other pending requests
    
    AnimalAdopted --> [*]: Process complete
    AdoptionDenied --> [*]
    AdoptionCancelled --> [*]
    RescueFailed --> [*]
    RescueCancelled --> [*]
    
    note right of RescueRescued
        RescueService creates animal
        record and links via
        rescue_mission_id
    end note
    
    note right of AdoptionApproved
        AdoptionService:
        1. Updates animal status
        2. Denies other pending requests
        3. Timestamps approval
    end note

```

---

## Design Patterns

### 1. Service Layer Pattern

All business logic is encapsulated in service classes that accept a `Database` instance or path:

```python
class AnimalService:
    def __init__(self, db: Optional[Database | str] = None, *, ensure_tables: bool = True):
        """
        Accept either Database instance or path string for flexibility.
        Tests can pass in-memory/temp databases; production uses configured path.
        """
        if isinstance(db, Database):
            self.db = db
        else:
            self.db = Database(db if isinstance(db, str) else app_config.DB_PATH)
        
        if ensure_tables:
            self.db.create_tables()
```

**Benefits**:
- Dependency injection for testability
- Reusable services across views
- Clear separation of concerns

---

### 2. Observable State Pattern

State management uses a reactive observer pattern with a singleton coordinator:

```python
class AppState:
    """Singleton coordinating all state managers."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_state()
        return cls._instance
    
    def _init_state(self):
        self.auth = AuthState()      # Authentication state
        self.animals = AnimalState()  # Animal cache
        self.rescues = RescueState()  # Rescue cache
        # ... other state managers
```

**State Managers** inherit from `ObservableBase`:

```python
class ObservableBase:
    def __init__(self):
        self._observers = []
    
    def subscribe(self, callback: Callable):
        """Register observer for state changes."""
        self._observers.append(callback)
    
    def _notify(self):
        """Notify all observers of state change."""
        for callback in self._observers:
            callback()
```

**Benefits**:
- Reactive UI updates
- Decoupled components
- Centralized state management

---

### 3. Component-Based UI Pattern

All UI elements use standardized components from `components/` module:

```python
# Correct usage
from components import create_form_text_field, create_form_dropdown, show_snackbar

name_field = create_form_text_field(
    hint_text="Animal Name",
    value=animal.get("name", ""),
    required=True
)

status_dropdown = create_form_dropdown(
    options=["Healthy", "Recovering", "Injured"],
    value=animal.get("status"),
    label="Health Status"
)

show_snackbar(page, "Animal saved successfully!", color="success")
```

**Component Categories**:
- **Form Components**: Text fields, dropdowns, labels, date pickers
- **Layout Components**: Cards, sections, tables, stat cards
- **Interactive Components**: Buttons, dialogs, photo uploads
- **Visual Components**: Charts, badges, status indicators

**Benefits**:
- Consistent styling across app
- Reduced code duplication
- Easy theme changes

---

### 4. Status Constants Pattern

Centralized status management with normalization and helper methods:

```python
class RescueStatus:
    PENDING = "pending"
    ON_GOING = "on-going"
    RESCUED = "rescued"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REMOVED = "removed"
    
    @staticmethod
    def normalize(status: str) -> str:
        """Normalize status variants (case-insensitive, handles archived)."""
        if not status:
            return RescueStatus.PENDING
        
        base_status = status.split("|")[0].strip().lower().replace(" ", "-")
        
        # Map variants to canonical form
        if base_status in ["pending", "submitted"]:
            return RescueStatus.PENDING
        elif base_status in ["on-going", "ongoing", "in-progress"]:
            return RescueStatus.ON_GOING
        # ... etc
    
    @staticmethod
    def is_archived(status: str) -> bool:
        """Check if status has archived suffix."""
        return "|archived" in status.lower()
    
    @staticmethod
    is_active(status: str) -> bool:
        """Check if rescue is active (pending or on-going)."""
        base = RescueStatus.normalize(status)
        return base in [RescueStatus.PENDING, RescueStatus.ON_GOING]
```

**Benefits**:
- Single source of truth for statuses
- Handles legacy data variants
- Type-safe constants

---

### 5. Lazy Import Pattern (Views)

Views import Flet lazily inside `build()` method to avoid import conflicts during testing:

```python
class MyPage:
    def __init__(self, db_path: Optional[str] = None):
        self.service = MyService(db_path or app_config.DB_PATH)
    
    def build(self, page) -> None:
        import flet as ft  # Lazy import here, not at module level
        
        # Build UI components
        container = ft.Container(...)
        page.add(container)
        page.update()
```

**Benefits**:
- Test isolation (pytest doesn't need Flet UI)
- Faster test startup
- Cleaner test output

---

## Data Flow

### 1. Read Operation (Display Animals)

```mermaid
sequenceDiagram
    participant User
    participant View
    participant Service
    participant Cache
    participant Database
    
    User->>View: Navigate to Animals List
    View->>Service: get_adoptable_animals()
    Service->>Cache: Check cache
    
    alt Cache hit
        Cache->>Service: Return cached data
    else Cache miss
        Service->>Database: SELECT * FROM animals WHERE...
        Database->>Service: Return rows
        Service->>Cache: Store in cache (60s TTL)
    end
    
    Service->>View: Return animal list
    View->>View: Render UI components
    View->>User: Display animals
```

### 2. Write Operation (Create Rescue Mission)

```mermaid
sequenceDiagram
    participant User
    participant View
    participant Service
    participant Database
    participant State
    participant FileStore
    
    User->>View: Fill rescue form + upload photo
    View->>View: Validate inputs
    View->>FileStore: save_photo(file_data)
    FileStore->>FileStore: Generate unique filename
    FileStore->>View: Return filename
    
    View->>Service: create_rescue_mission(data)
    Service->>Database: BEGIN TRANSACTION
    Service->>Database: INSERT INTO rescue_missions
    Database->>Service: Return mission_id
    Service->>Database: COMMIT
    
    Service->>State: Clear rescue cache
    State->>State: Notify observers
    
    Service->>View: Return success result
    View->>User: Show success message
    View->>View: Redirect to missions list
```

### 3. Complex Operation (Approve Adoption)

```mermaid
sequenceDiagram
    participant Admin
    participant View
    participant AdoptionSvc
    participant AnimalSvc
    participant Database
    participant LoggingSvc
    
    Admin->>View: Click "Approve" on adoption request
    View->>AdoptionSvc: approve_request(request_id, message)
    
    AdoptionSvc->>Database: BEGIN TRANSACTION
    
    AdoptionSvc->>Database: UPDATE adoption_requests<br/>SET status='approved', approved_at=NOW()
    AdoptionSvc->>Database: SELECT animal_id FROM adoption_requests
    
    AdoptionSvc->>AnimalSvc: update_animal_status(animal_id, "adopted")
    AnimalSvc->>Database: UPDATE animals SET status='adopted'
    
    AdoptionSvc->>Database: UPDATE adoption_requests<br/>SET status='denied' WHERE animal_id=X<br/>AND status='pending'
    
    AdoptionSvc->>Database: COMMIT
    
    AdoptionSvc->>LoggingSvc: log_admin_action("ADOPTION_APPROVED")
    
    AdoptionSvc->>View: Return success
    View->>Admin: Show success message
```

---

## Module Dependencies

### Dependency Graph

```mermaid
graph TD
    main[main.py] --> routes
    main --> AppState
    main --> app_config
    
    routes --> middleware
    routes --> views
    middleware --> AuthService
    middleware --> AppState
    
    views --> components
    views --> services
    views --> AppState
    
    services --> storage
    services --> models
    services --> app_config
    
    AuthService --> PasswordPolicy
    AuthService --> LoggingService
    AuthService --> GoogleAuthService
    
    AnimalService --> PhotoService
    AnimalService --> AIService
    
    RescueService --> MapService
    RescueService --> AnimalService
    
    AdoptionService --> AnimalService
    AdoptionService --> LoggingService
    
    AnalyticsService --> Cache
    
    storage --> Database
    storage --> FileStore
    storage --> Cache
    
    components --> utils
    
    style main fill:#ffcdd2
    style routes fill:#f8bbd0
    style views fill:#e1bee7
    style services fill:#d1c4e9
    style storage fill:#c5cae9
    style components fill:#bbdefb
```

### Module Import Rules

1. **No circular imports**: Services don't import views; views import services
2. **Lazy imports**: Flet imported inside `build()` methods in views
3. **Configuration first**: `app_config.py` has no dependencies (except stdlib + dotenv)
4. **Services as boundaries**: Views never directly access Database or FileStore

---

## Configuration Management

### Centralized Configuration (app_config.py)

All environment-dependent settings are centralized:

```python
# Database
DB_PATH = os.getenv("PAWRES_DB_PATH", "storage/data/app.db")

# Security
MAX_FAILED_LOGIN_ATTEMPTS = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))

# Password Policy
PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
PASSWORD_REQUIRE_UPPERCASE = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"
PASSWORD_REQUIRE_DIGIT = os.getenv("PASSWORD_REQUIRE_DIGIT", "true").lower() == "true"
# ... etc

# AI Classification
AI_MODEL_CACHE_DIR = "storage/ai_models"
MIN_SPECIES_CONFIDENCE = 0.60
MIN_BREED_CONFIDENCE = 0.58

# Maps
DEFAULT_MAP_CENTER = (13.5250, 123.3486)  # Camarines Sur, Philippines
GEOCODE_RATE_LIMIT = 1.5  # seconds between requests
```

**Benefits**:
- Single source of truth for configuration
- Easy environment-specific overrides
- Type conversion handled once
- Default values for development

---

## Architecture Decision Records

### ADR-001: Why Flet Framework?

**Context**: Need cross-platform UI framework for Python backend.

**Decision**: Use Flet (Python to Flutter) instead of traditional web frameworks.

**Rationale**:
- Single codebase for desktop and web
- Python expertise on team (no JavaScript required)
- Fast development with hot-reload
- Native-like performance and UI

**Trade-offs**:
- Smaller community than React/Vue
- Limited third-party component library
- Web version requires Flet server

---

### ADR-002: Why SQLite Instead of PostgreSQL?

**Context**: Need database for animal shelter operations.

**Decision**: Use SQLite embedded database.

**Rationale**:
- Zero configuration (no database server)
- Perfect for single-shelter deployments
- ACID compliance with foreign keys
- Easy backup (single file)
- Sufficient for expected load (<10,000 records)

**Trade-offs**:
- No built-in replication
- Limited concurrent writes
- Not suitable for multi-tenant SaaS

---

### ADR-003: Why Observable State Pattern?

**Context**: Need reactive UI updates across multiple pages.

**Decision**: Implement custom observable state managers.

**Rationale**:
- Lightweight (no external state library)
- Fine-grained control over reactivity
- Clear separation between state and business logic
- Easy to test

**Trade-offs**:
- Manual observer management
- No time-travel debugging
- Less sophisticated than Redux/MobX

---

### ADR-004: Why Service Layer Pattern?

**Context**: Business logic scattered across views and database code.

**Decision**: Introduce service layer between views and data access.

**Rationale**:
- Reusable business logic
- Testable without UI
- Clear API boundaries
- Easier to swap data sources

**Trade-offs**:
- Additional abstraction layer
- More files to maintain

---

## Performance Considerations

### Caching Strategy

```python
# Cache frequently accessed data with TTL
cache = Cache()

# Cache adoptable animals (60-second TTL)
adoptable_animals = cache.get("adoptable_animals")
if adoptable_animals is None:
    adoptable_animals = db.execute("SELECT * FROM animals WHERE ...").fetchall()
    cache.set("adoptable_animals", adoptable_animals, ttl=60)
```

### Database Optimization

```python
# Use connection pooling for concurrent requests (not needed with SQLite)
# Use indexes on frequently queried columns
db.execute("CREATE INDEX IF NOT EXISTS idx_animals_status ON animals(status)")
db.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

# Use parameterized queries to prevent SQL injection and enable query caching
db.execute("SELECT * FROM animals WHERE species = ?", (species,))
```

### File Storage Optimization

```python
# Store only filenames in database, not base64 (reduces DB size)
# Lazy load photos (load when displayed, not when fetching records)
# Use thumbnails for list views (future enhancement)
```

---

## Security Architecture

See **[SECURITY.md](SECURITY.md)** for detailed security implementation.

**Key Security Layers**:

1. **Authentication Layer**: Password hashing, OAuth, lockout
2. **Authorization Layer**: RBAC, route protection, session validation
3. **Data Layer**: Foreign keys, input validation, SQL injection prevention
4. **Audit Layer**: Comprehensive logging of security events

---

## Scalability Considerations

### Current Limits

- **Database**: SQLite suitable for <10,000 records and <10 concurrent users
- **File Storage**: Local filesystem suitable for <10GB of photos
- **AI Models**: Models loaded into memory (~2GB RAM when active)

### Future Migration Paths

1. **Database**: Migrate to PostgreSQL for higher concurrency
2. **File Storage**: Migrate to S3/Azure Blob for cloud storage
3. **AI**: Deploy models as separate microservice with GPU acceleration
4. **Caching**: Migrate to Redis for distributed caching

---

## Deployment Architecture

### Single-Server Deployment (Current)

```
┌─────────────────────────────────────┐
│         Physical Server             │
│  ┌─────────────────────────────┐   │
│  │   Flet Application          │   │
│  │   - Web Server (port 8080)  │   │
│  │   - SQLite Database         │   │
│  │   - File Storage            │   │
│  │   - AI Models (in-memory)   │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### Microservices Deployment (Future)

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Flet Web    │──────│  API Gateway │──────│   Database   │
│   Server     │      │   (FastAPI)  │      │ (PostgreSQL) │
└──────────────┘      └──────────────┘      └──────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
            ┌───────▼──────┐  ┌──────▼──────┐
            │ AI Service   │  │File Service │
            │  (GPU)       │  │   (S3)      │
            └──────────────┘  └─────────────┘
```

---

**Last Updated**: December 8, 2025  
**Maintained by**: clepord34 (viaguilar@my.cspc.edu.ph) - Lead Developer
