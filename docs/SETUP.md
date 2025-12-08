# PawRes Setup Guide

Complete installation and configuration guide for PawRes - Animal Rescue & Adoption Management System.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation Steps](#installation-steps)
- [Environment Configuration](#environment-configuration)
- [Dependencies Overview](#dependencies-overview)
- [First Run](#first-run)
- [Running the Application](#running-the-application)
- [Testing Setup](#testing-setup)
- [Google OAuth Setup](#google-oauth-setup-optional)
- [Directory Structure](#directory-structure)
- [Troubleshooting](#troubleshooting)
- [Deployment Considerations](#deployment-considerations)

---

## Prerequisites

Before installing PawRes, ensure your system meets these requirements:

- **Python**: Version 3.9 or higher
- **pip**: Python package installer (usually included with Python)
- **Disk Space**: Minimum 1GB free space (for application, dependencies, and AI models)
- **Operating System**: Windows, macOS, or Linux
- **Internet Connection**: Required for initial setup and AI model downloads
- **Git**: For cloning the repository

### Verify Prerequisites

```powershell
# Check Python version (should be 3.9+)
python --version

# Check pip version
pip --version

# Check Git installation
git --version
```

---

## Installation Steps

### 1. Clone the Repository

```powershell
# Navigate to your desired directory
cd C:\Users\YourUsername\Desktop

# Clone the repository
git clone https://github.com/clepord34/PawRes.git

# Navigate into the project
cd PawRes
```

### 2. Create Virtual Environment

Creating a virtual environment isolates project dependencies from your system Python.

```powershell
# Create virtual environment
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**
```cmd
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

> **Note**: If you encounter execution policy errors on Windows PowerShell, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 4. Install Dependencies

```powershell
# Upgrade pip to latest version
python -m pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

This will install all dependencies declared in `requirements.txt`, including for example:
- Flet and related packages (UI framework)
- PyTorch and Transformers (AI classification)
- Matplotlib and Plotly (data visualization)
- Geopy and flet-map (mapping features)
- pytest and pytest-cov (testing and coverage)

**Installation Time**: Actual time depends on your internet speed and hardware; large ML
packages may take several minutes to download and build.

### 5. Configure Environment

Create your environment configuration file:

```powershell
# Copy the example environment file
Copy-Item .env.example .env
```

Edit `.env` with your preferred text editor and configure the settings (see [Environment Configuration](#environment-configuration) section below).

### 6. Initialize Database

The database will be automatically created on first run. You can verify the location:

```powershell
# Default database path
# app/storage/data/app.db
```

### 7. Run the Application

```powershell
# Navigate to the app directory
cd app

# Launch PawRes in desktop mode
flet run
```

The application window should open automatically. Use the default admin credentials from your `.env` file to log in.

---

## Environment Configuration

Edit the `.env` file in the project root directory. Here's a complete reference of all available settings:

### Admin Account Configuration

Default administrator credentials (change these in production!):

```dotenv
ADMIN_EMAIL=admin@gmail.com
ADMIN_PASSWORD=Admin@123
ADMIN_NAME=Admin User
```

> **Security Warning**: Change these defaults before deploying to production. The password must meet the password policy requirements.

### Security Settings

```dotenv
# Login attempt limits
MAX_FAILED_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15

# Session management
SESSION_TIMEOUT_MINUTES=30
```

### Password Policy

```dotenv
# Password requirements
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGIT=true
PASSWORD_REQUIRE_SPECIAL=true

# Password history (prevents reuse of recent passwords)
# Note: Password history tracking is not currently implemented
PASSWORD_HISTORY_COUNT=5
```

### Google OAuth (Optional)

Enable Google Sign-In for users:

```dotenv
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

See [Google OAuth Setup](#google-oauth-setup-optional) for detailed configuration steps.

### Database Path (Optional)

Override the default database location:

```dotenv
PAWRES_DB_PATH=C:/custom/path/to/database.db
```

If not set, defaults to `app/storage/data/app.db`.

### AI Model Settings

AI models are automatically downloaded on first use. They will be cached in:
```
app/storage/ai_models/
```

---

## Dependencies Overview

Key packages from `requirements.txt`:

### UI Framework
- **flet==0.28.3** - Cross-platform UI framework (Python to Flutter)
- **flet-map==0.1.0** - Interactive mapping component
- **flet-geolocator==0.1.0** - Geolocation services

### AI & Machine Learning
- **torch==2.9.1** - PyTorch deep learning framework
- **torchvision==0.24.1** - Computer vision models and utilities
- **transformers==4.57.3** - Hugging Face transformers for NLP and vision
- **huggingface-hub==0.36.0** - Model downloading and management

### Data Visualization
- **matplotlib==3.10.7** - Static plotting library
- **plotly==6.5.0** - Interactive charts and graphs
- **folium==0.20.0** - Leaflet maps for Python

### Geolocation
- **geopy==2.4.1** - Geocoding and distance calculations
- **geocoder==1.38.1** - Address geocoding

### Web Framework
- **fastapi==0.121.3** - Modern web framework for APIs
- **uvicorn==0.38.0** - ASGI server

### Data Processing
- **pandas==2.3.3** - Data manipulation and analysis
- **numpy==2.3.5** - Numerical computing
- **openpyxl==3.1.5** - Excel file reading/writing

### Testing
- **pytest==9.0.1** - Testing framework
- **pytest-cov==7.0.0** - Code coverage reporting

### Utilities
- **python-dotenv==1.2.1** - Environment variable management
- **Pillow==12.0.0** - Image processing
- **requests==2.32.5** - HTTP library
- **tqdm==4.67.1** - Progress bars

---

## First Run

When you run PawRes for the first time, the following initialization occurs automatically:

### 1. Database Initialization
- SQLite database file created at `app/storage/data/app.db`
- Core tables created (see `docs/DATABASE.md` for full schema):
   - `users` - User accounts and authentication (includes failed-attempt and lockout fields)
   - `animals` - Animal records
   - `rescue_missions` - Rescue operation tracking
   - `adoption_requests` - Adoption applications

### 2. Default Admin Account
- Admin user created with credentials from `.env`
- Default email: `admin@gmail.com`
- Default password: `Admin@123` (change this!)
- Role: `admin` with full system access

### 3. Storage Directories
The following directory structure is created automatically:

```
app/storage/
├── data/
│   ├── app.db           # Main database
│   └── logs/            # Audit logs
│       ├── auth.log     # Authentication events
│       ├── admin.log    # Admin actions
│       └── security.log # Security incidents
├── uploads/             # User-uploaded photos
├── ai_models/           # Cached AI models
├── temp/                # Temporary files
└── cache/               # Application cache
```

### 4. First Login

1. Launch the application: `cd app; flet run`
2. The login page will appear
3. Use admin credentials from your `.env` file
4. You'll be taken to the admin dashboard

---

## Running the Application

### Desktop Mode (Default)

Launch as a native desktop application:

```powershell
# From the project root
cd app
flet run
```

The application opens in a dedicated window with native OS integration.

### Web Mode

Run as a web application accessible via browser:

```powershell
cd app
flet run --web --port 8080
```

Then open your browser to: `http://localhost:8080`

**Web Mode Features:**
- Accessible from multiple devices on the same network
- No installation required on client devices
- Use the host machine's IP address for network access

### Background Process Management

When running as a background process (servers, development):

```powershell
# Start in background (for development/testing)
cd app
Start-Process -NoNewWindow flet run

# Stop all flet processes
Get-Process | Where-Object {$_.ProcessName -like "*flet*"} | Stop-Process
```

### Command-Line Options

```powershell
# Show all available options
flet run --help

# Common options:
flet run --web                    # Web mode
flet run --web --port 3000        # Custom port
flet run --verbose                # Detailed logging
flet run --directory app          # Specify app directory
```

---

## Testing Setup

PawRes includes a comprehensive test suite using pytest.

### Running All Tests

```powershell
# From project root
python -m pytest app/tests -v
```

### Running Specific Test Files

```powershell
# Test authentication service
python -m pytest app/tests/test_auth_service.py -v

# Test animal service
python -m pytest app/tests/test_animal_service.py -v

# Test adoption workflow
python -m pytest app/tests/test_adoption_service.py -v
```

### Running Tests with Coverage

```powershell
# Generate coverage report
python -m pytest app/tests --cov=app --cov-report=html

# View the report
# Open htmlcov/index.html in your browser
```

### Test Database Isolation

Tests use temporary databases via fixtures in `app/tests/conftest.py`:

- Each test gets a fresh, empty database
- No interference with production data
- Automatic cleanup after tests complete

### Available Test Fixtures

```python
# conftest.py provides these fixtures:
- temp_db_path          # Temporary database file
- database              # Database instance
- auth_service          # Authentication service
- animal_service        # Animal management service
- rescue_service        # Rescue mission service
- adoption_service      # Adoption request service
- sample_user           # Pre-created test user
- sample_admin          # Pre-created test admin
```

### Running Specific Tests

```powershell
# Run tests matching a keyword
python -m pytest app/tests -k "test_login" -v

# Run tests from multiple files
python -m pytest app/tests/test_auth_service.py app/tests/test_user_service.py -v

# Run with markers (if defined)
python -m pytest app/tests -m "integration" -v
```

---

## Google OAuth Setup (Optional)

Enable Google Sign-In for user authentication.

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Enter project name: "PawRes" (or your preference)
4. Click **Create**

### 2. Enable Required APIs

1. In the navigation menu, go to **APIs & Services** → **Library**
2. Search for and enable:
   - **Google+ API** (deprecated but may still work)
   - **Google Identity Services API** (recommended)
   - **People API** (for profile information)

### 3. Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type (unless you have Google Workspace)
3. Fill in required information:
   - **App name**: PawRes
   - **User support email**: Your email
   - **Developer contact**: Your email
4. Add scopes:
   - `openid`
   - `email`
   - `profile`
5. Add test users (your email address for testing)
6. Click **Save and Continue**

### 4. Create OAuth Client ID

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: "PawRes Desktop Client"
5. Click **Create**

### 5. Configure Redirect URI

**Important**: Add this exact redirect URI:
```
http://localhost:8085/oauth/callback
```

If the UI doesn't allow editing redirect URIs for Desktop apps:
1. Download the client configuration JSON
2. Note the client ID and secret
3. Or create a **Web application** type instead with the redirect URI

### 6. Add Credentials to .env

Copy your credentials to the `.env` file:

```dotenv
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your_secret_here
```

### 7. Test OAuth Flow

1. Restart the application
2. On the login page, click **Sign in with Google**
3. Complete the Google authentication flow
4. You should be redirected back and logged in

### Troubleshooting OAuth

**Error: redirect_uri_mismatch**
- Verify the redirect URI is exactly: `http://localhost:8085/oauth/callback`
- Check for trailing slashes or typos

**Error: invalid_client**
- Verify credentials are correctly copied to `.env`
- Ensure no extra spaces or quotes

**Error: access_denied**
- User clicked "Cancel" on Google consent screen
- Or your email isn't added as a test user

---

## Directory Structure

Important paths and their purposes:

### Application Structure

```
PawRes/
├── app/                          # Main application directory
│   ├── main.py                   # Application entry point
│   ├── app_config.py             # Configuration management
│   ├── pytest.ini                # pytest configuration
│   │
│   ├── assets/                   # Static assets
│   │   ├── icons/                # Application icons
│   │   ├── images/               # Images and graphics
│   │   └── templates/            # Document templates
│   │
│   ├── components/               # Reusable UI components
│   │   ├── form_fields.py        # Form input components
│   │   ├── dialogs.py            # Dialog windows
│   │   ├── charts.py             # Data visualization
│   │   └── ...
│   │
│   ├── views/                    # Page views
│   │   ├── login_page.py         # Login interface
│   │   ├── admin_dashboard.py   # Admin dashboard
│   │   ├── animals_list_page.py # Animal listing
│   │   └── ...
│   │
│   ├── services/                 # Business logic layer
│   │   ├── auth_service.py       # Authentication
│   │   ├── animal_service.py     # Animal management
│   │   ├── rescue_service.py     # Rescue operations
│   │   ├── adoption_service.py   # Adoption processing
│   │   └── ...
│   │
│   ├── storage/                  # Data storage
│   │   ├── database.py           # Database management
│   │   ├── file_store.py         # File storage
│   │   │
│   │   ├── data/                 # Database and logs
│   │   │   ├── app.db            # SQLite database
│   │   │   └── logs/             # Audit logs
│   │   │
│   │   ├── uploads/              # User-uploaded photos
│   │   ├── ai_models/            # Cached AI models
│   │   ├── temp/                 # Temporary files
│   │   └── cache/                # Application cache
│   │
│   ├── routes/                   # Route management
│   │   ├── auth_routes.py        # Authentication routes
│   │   ├── admin_routes.py       # Admin routes
│   │   ├── user_routes.py        # User routes
│   │   └── ...
│   │
│   ├── state/                    # State management
│   │   ├── app_state.py          # Application state
│   │   ├── auth_state.py         # Authentication state
│   │   └── ...
│   │
│   ├── models/                   # Data models
│   │   ├── user.py               # User model
│   │   ├── animal.py             # Animal model
│   │   └── ...
│   │
│   └── tests/                    # Test suite
│       ├── conftest.py           # Test fixtures
│       ├── test_auth_service.py  # Auth tests
│       └── ...
│
├── docs/                         # Documentation
│   ├── SETUP.md                  # This file
│   ├── README.md                 # Project overview
│   ├── ARCHITECTURE.md           # System architecture
│   ├── DATABASE.md               # Database schema
│   └── SECURITY.md               # Security documentation
│
├── .env                          # Environment configuration (create from .env.example)
├── .env.example                  # Environment template
├── requirements.txt              # Python dependencies
├── setup.cfg                     # Tool configuration
└── README.md                     # Project README
```

### Critical Paths

- **Database**: `app/storage/data/app.db`
- **Audit Logs**: `app/storage/data/logs/`
- **Uploaded Photos**: `app/storage/uploads/`
- **AI Models Cache**: `app/storage/ai_models/`
- **Environment Config**: `.env` (project root)

---

## Troubleshooting

### Common Issues and Solutions

#### 1. "No module named 'flet'"

**Problem**: Python can't find the flet package.

**Solution**:
```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip show flet
```

#### 2. "Database is locked"

**Problem**: Multiple instances trying to access the database.

**Solution**:
```powershell
# Close all running instances
Get-Process | Where-Object {$_.ProcessName -like "*flet*"} | Stop-Process

# If issue persists, check for zombie connections
# Restart your computer (last resort)
```

**Prevention**: Only run one instance of the app at a time.

#### 3. "Permission denied" on storage/

**Problem**: Application lacks write permissions.

**Solution**:
```powershell
# Check permissions (Windows)
icacls app\storage

# Grant full control to current user
icacls app\storage /grant:r "$env:USERNAME:(OI)(CI)F" /T

# On macOS/Linux
chmod -R 755 app/storage
```

#### 4. AI Model Download Failed

**Problem**: Network issues or insufficient disk space.

**Solution**:
```powershell
# Check internet connection
Test-Connection huggingface.co

# Check disk space
Get-PSDrive C

# Clear cache and retry
Remove-Item -Recurse app\storage\ai_models\*
```

**Manual Download**: If automatic download fails, manually download models from Hugging Face and place in `app/storage/ai_models/`.

#### 5. OAuth Error: redirect_uri_mismatch

**Problem**: Google OAuth redirect URI mismatch.

**Solution**:
1. In Google Cloud Console, verify redirect URI is: `http://localhost:8085/oauth/callback`
2. Check for typos, trailing slashes, or http vs https
3. Ensure the OAuth client type matches (Desktop or Web)

#### 6. Session Timeout Too Aggressive

**Problem**: Users logged out too quickly.

**Solution**: Adjust session timeout in `.env`:
```dotenv
SESSION_TIMEOUT_MINUTES=60  # Increase to 60 minutes
```

#### 7. Password Policy Too Strict

**Problem**: Users can't create accounts due to password requirements.

**Solution**: Adjust password policy in `.env`:
```dotenv
PASSWORD_MIN_LENGTH=6
PASSWORD_REQUIRE_UPPERCASE=false
PASSWORD_REQUIRE_LOWERCASE=false
PASSWORD_REQUIRE_DIGIT=true
PASSWORD_REQUIRE_SPECIAL=false
```

#### 8. Port Already in Use (Web Mode)

**Problem**: Port 8080 is occupied.

**Solution**:
```powershell
# Use a different port
flet run --web --port 3000

# Or find and kill the process using port 8080
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

#### 9. Virtual Environment Not Activating

**Problem**: PowerShell execution policy blocking scripts.

**Solution**:
```powershell
# Allow script execution for current user
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate
.\venv\Scripts\Activate.ps1
```

#### 10. Import Errors After Update

**Problem**: Cached bytecode conflicts with new code.

**Solution**:
```powershell
# Clear all __pycache__ directories
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# Restart the application
cd app
flet run
```

---

## Deployment Considerations

### Production Checklist

Before deploying PawRes to production:

#### 1. Security

```dotenv
# Change default admin credentials
ADMIN_EMAIL=your-admin@company.com
ADMIN_PASSWORD=StrongP@ssw0rd!2024

# Enable strict password policy
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGIT=true
PASSWORD_REQUIRE_SPECIAL=true
PASSWORD_HISTORY_COUNT=10  # Note: Not currently implemented

# Reasonable security settings
MAX_FAILED_LOGIN_ATTEMPTS=3
LOCKOUT_DURATION_MINUTES=30
SESSION_TIMEOUT_MINUTES=15
```

#### 2. HTTPS Configuration

For web deployments, use a reverse proxy (nginx, Apache, or IIS):

**nginx example:**
```nginx
server {
    listen 443 ssl;
    server_name pawres.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 3. Database Backups

Implement regular database backups:

```powershell
# Create backup script (backup_db.ps1)
$BackupDir = "C:\Backups\PawRes"
$Date = Get-Date -Format "yyyy-MM-dd_HHmmss"
$BackupPath = "$BackupDir\app_db_$Date.db"

New-Item -ItemType Directory -Force -Path $BackupDir
Copy-Item "app\storage\data\app.db" -Destination $BackupPath
Compress-Archive -Path $BackupPath -DestinationPath "$BackupPath.zip"
Remove-Item $BackupPath

# Keep only last 30 backups
Get-ChildItem $BackupDir -Filter "*.zip" | 
    Sort-Object CreationTime -Descending | 
    Select-Object -Skip 30 | 
    Remove-Item
```

Schedule with Windows Task Scheduler (daily at 2 AM):
```powershell
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\path\to\backup_db.ps1"
$Trigger = New-ScheduledTaskTrigger -Daily -At 2AM
Register-ScheduledTask -TaskName "PawRes-Backup" -Action $Action -Trigger $Trigger
```

#### 4. Log Monitoring

Implement log rotation and monitoring:

```powershell
# Monitor log size
Get-ChildItem app\storage\data\logs\ | Where-Object {$_.Length -gt 100MB}

# Rotate logs (monthly)
$LogDir = "app\storage\data\logs"
$ArchiveDir = "$LogDir\archive"
New-Item -ItemType Directory -Force -Path $ArchiveDir

Get-ChildItem $LogDir -Filter "*.log" | ForEach-Object {
    $NewName = "$($_.BaseName)_$(Get-Date -Format 'yyyy-MM').log"
    Move-Item $_.FullName -Destination "$ArchiveDir\$NewName"
}
```

Review security logs regularly:
```powershell
# View recent security events
Get-Content app\storage\data\logs\security.log -Tail 50
```

#### 5. Performance Optimization

- **Database**: Consider PostgreSQL for production instead of SQLite
- **Caching**: Enable application caching for better performance
- **AI Models**: Pre-download models during deployment
- **Static Assets**: Use CDN for assets in web mode

#### 6. Monitoring

Set up monitoring for:
- Application uptime
- Database size and performance
- Failed login attempts
- Error logs
- Disk space usage

#### 7. Update Strategy

```powershell
# Update process
cd PawRes

# Backup database
Copy-Item app\storage\data\app.db app\storage\data\app.db.backup

# Pull latest changes
git pull origin main

# Update dependencies
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt --upgrade

# Run tests
python -m pytest app/tests -v

# Restart application
# (Manual restart or use process manager)
```

#### 8. Resource Management

**Minimum Production Requirements:**
- **CPU**: 2 cores
- **RAM**: 4GB (8GB recommended with AI features)
- **Disk**: 10GB free space
- **Network**: Stable connection for AI model downloads

#### 9. User Management

- Regularly review user accounts
- Disable inactive accounts
- Audit admin actions via logs
- Implement proper role-based access control

#### 10. Disaster Recovery

Document and test:
- Database restore procedures
- Application recovery steps
- Data migration processes
- Rollback procedures

---

## Getting Help

### Resources

- **Documentation**: See `docs/` directory
  - [README.md](README.md) - Project overview
  - [ARCHITECTURE.md](ARCHITECTURE.md) - System design
  - [DATABASE.md](DATABASE.md) - Database schema
  - [SECURITY.md](SECURITY.md) - Security features

- **Flet Documentation**: https://flet.dev/docs/ (v0.28.3)

- **GitHub Issues**: https://github.com/clepord34/PawRes/issues

### Support

For issues or questions:
1. Check this documentation first
2. Review existing GitHub issues
3. Create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Error messages or logs
   - System information (OS, Python version)

---

## Next Steps

After successful setup:

1. **Explore the Application**
   - Log in with admin credentials
   - Browse the admin dashboard
   - Test animal management features
   - Try rescue mission workflows
   - Test adoption request processing

2. **Customize Configuration**
   - Adjust security settings as needed
   - Configure map defaults for your location
   - Set up Google OAuth if desired
   - Customize UI settings

3. **Import Data** (if migrating)
   - Use the import service for bulk data
   - Verify all data imported correctly
   - Test all workflows

4. **Train Staff**
   - Document your specific workflows
   - Create user accounts with appropriate roles
   - Provide training on key features

5. **Go Live**
   - Start with a pilot phase
   - Monitor logs and performance
   - Gather user feedback
   - Iterate and improve

---

**Version**: 1.0.0  
**Last Updated**: December 8, 2025  
**Maintained by**: PawRes Development Team
