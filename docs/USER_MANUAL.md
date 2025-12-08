# PawRes User Manual

## Table of Contents

1. [Getting Started](#getting-started)
2. [Role-Based Capabilities](#role-based-capabilities)
3. [User Workflows](#user-workflows)
4. [Admin Workflows](#admin-workflows)
5. [Feature Guides](#feature-guides)
6. [Common Tasks](#common-tasks)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### First-Time Login

Welcome to **PawRes** - your animal rescue and adoption management system!

#### Accessing the Application

Run the application from the `app/` directory using Flet. For local development use PowerShell and your virtual environment (if present):

```powershell
# From the project root (activate venv if you created one)
cd app
.\venv\Scripts\Activate.ps1    # optional: activate virtualenv from project root
flet run                         # Launches a desktop window for the app

# Or run in web mode (accessible from a browser):
flet run --web --port 8080
```

When running in web mode, open the URL printed in the console (for example `http://localhost:8080`).

#### Default Admin Credentials

If you're setting up PawRes for the first time, use these credentials:

- **Email**: Value from `.env` file (`ADMIN_EMAIL`)
- **Password**: Value from `.env` file (`ADMIN_PASSWORD`)

⚠️ **Security Warning**: Change the default admin password immediately after first login!

#### Logging In

![Login Page with Logo and Form Fields](screenshots/01_login_page.png)

1. Enter your **email address**
2. Enter your **password**
3. Click **"Login"** button

**Alternative Login Method**:
- Click **"Sign in with Google"** to use your Google account (if OAuth is configured)

#### First-Time Setup Checklist (Admins)

After logging in as admin:

- [ ] Change default password (Profile → Change Password)
- [ ] Review system settings
- [ ] Create additional admin accounts (User Management → Add User)
- [ ] Import existing animal data (View Animal List → Add Animal → Bulk Import)

### Password Setting Guidelines

When creating or changing your password, ensure it meets the following criteria:

**Password Requirements**:
- Minimum 8 characters
- At least 1 uppercase letter (A-Z)
- At least 1 lowercase letter (a-z)
- At least 1 number (0-9)
- At least 1 special character (!@#$%^&*)

### Account Lockout

**Security Feature**: After 5 consecutive failed login attempts, your account will be locked for 15 minutes.

**If Locked**:
- Wait 15 minutes before trying again
- Contact an administrator to unlock your account immediately
- Ensure you're using the correct password

---

## Role-Based Capabilities

PawRes has two user roles with different permission levels:

### Capabilities Matrix

| Feature | User | Admin |
|---------|------|-------|
| **Dashboard** | Personal analytics (own submissions) | Full system analytics |
| **Animals** | View adoptable animals only | Full CRUD (Create, Read, Update, Delete) + Archive |
| **Rescue Missions** | Submit + view own missions | View all + change status + add admin messages |
| **Adoption Requests** | Submit + view own applications | Approve/deny all + view user details |
| **User Management** | View/edit own profile only | View/edit all users + enable/disable + reset passwords |
| **Audit Logs** | No access | Full access with filtering |
| **Import/Export** | No access | Import CSV/Excel + export data |
| **AI Features** | Use breed detection on rescue form | Use breed detection on animal management |
| **Hidden Items** | No access | View archived/hidden animals, missions, adoptions |

### Navigation Differences

**User Sidebar**:
- User Dashboard
- Apply for Adoption
- Report Rescue Mission
- Check Application Status
- View Animal List
- Your Analytics
- Profile (click profile section at bottom)

**Admin Sidebar**:
- Admin Dashboard
- View Animal List
- Manage Records (includes Rescue Missions, Adoption Requests, Hidden Items)
- View Data Charts
- User Management
- Audit Logs
- Profile (click profile section at bottom)

---

## User Workflows

### Submit Rescue Mission

Report an animal in need of rescue through our emergency rescue system.

![Emergency Rescue Form](screenshots/02_emergency_rescue_form.png)

#### Step-by-Step Instructions

1. **Navigate to Rescue Form**
   - Click **"Report Rescue Mission"** in sidebar
   - Or access emergency form (no login required): `/emergency_rescue` route

2. **Fill Animal Information**
   - **Animal Type**: Select from dropdown (Dog, Cat, Bird, etc.)
   - **Breed**: Enter breed if known (AI can help detect this from photo)
   - **Name**: Give the animal a temporary name (or leave as "Unknown")
   - **Age**: Select age range (Puppy/Kitten, Young, Adult, Senior)
   - **Gender**: Select if known (Male, Female, Unknown)

3. **Upload Photo** (Highly Recommended)
   - Click **"Upload Photo"** or drag-and-drop image
   - Accepted formats: JPG, PNG, GIF, WEBP
   - Maximum size: 5 MB
   - Photo preview displays after upload

4. **Use AI Breed Detection** (Optional)
   - After uploading photo, click **"Analyze with AI"** button
   - Wait for analysis (5-10 seconds)
   - Review AI suggestions with confidence scores
   - Click suggested breed to auto-fill breed field

   ![AI Suggestion Card with Confidence Scores](screenshots/03_ai_suggestion_card.png)

5. **Set Location**
   - **Option A**: Type address in "Location" field and submit (address will be geocoded automatically)
   - **Option B**: Click the GPS button (📍) to use your current location (requires location permission)

   ![Current Location / Map Marker](screenshots/04_rescue_gps_button.png)

6. **Enter Contact Information**
   - **Contact**: Your phone or email (pre-filled if logged in)
   - Ensure you can be reached for updates

7. **Set Urgency Level**
   - **Low - Animal appears safe**: Animal is stable but needs eventual rescue
   - **Medium - Needs attention soon**: Animal needs rescue within 24-48 hours
   - **High - Immediate help needed**: Animal is injured or in immediate danger

8. **Add Details**
   - Describe the situation (injuries, behavior, surroundings)
   - Include landmarks or specific directions
   - Mention any immediate dangers

9. **Submit Request**
   - Click **"Submit Rescue Request"** button
   - Confirmation message displays
   - You'll receive a tracking ID

10. **Track Your Request**
    - Navigate to **"Check Application Status"** in sidebar (logged-in users)
    - Or use status checking with your tracking ID

#### Status Progression

Your rescue mission will move through these statuses:

1. **Pending** - Waiting for admin review
2. **On-Going** - Rescue team is en route or actively rescuing
3. **Rescued** - Animal has been safely rescued (creates animal record)
4. **Failed** - Rescue attempt unsuccessful
5. **Cancelled** - You cancelled the request before processing

You'll see status updates and admin messages in the mission detail view.

---

### Browse Adoptable Animals

Explore animals available for adoption and find your perfect companion.

![Animals List with Filter and Sidebar](screenshots/05_animals_list_filters.png)

#### Step-by-Step Instructions

1. **Navigate to Animals**
   - Click **"View Animal List"** in sidebar (available for both users and admins)
   - For admins: Can also access via `/animals_list?admin=1` for management view

2. **Browse Animal Cards**
   - Each card shows:
     - Photo
     - Name
     - Species and breed
     - Age
     - Status badge (Available, Pending, Adopted)

3. **Use Filters** (Left Sidebar)
   - **Species**: Dog, Cat, Other
   - **Age Range**: Puppy/Kitten, Young, Adult, Senior
   - **Gender**: Male, Female, Unknown

4. **Search by Name and Breed**
   - Use search box at top: "Search by animal name or breed..."
   - Type animal name or breed
   - Results update in real-time

5. **Apply for Adoption**
   - Click **"Apply for Adoption"** button
   - Fill adoption application form

---

### Submit Adoption Application

Apply to adopt an animal through our adoption management system.

![Animal Adoption Form](screenshots/06_animal_adoption_form.png)

#### Step-by-Step Instructions

1. **Select Animal**
   - Navigate to **"Apply for Adoption"** from sidebar
   - Animal information auto-populates

2. **Review Animal Details**
   - Verify you're applying for the correct animal
   - Review adoption requirements

3. **Enter Contact Information**
   - **Contact**: Pre-filled from profile (email or phone)
   - Update if you prefer different contact method

4. **Write Your Reason (Optional)**
   - **Why do you want to adopt this animal?**
   - This field is optional but recommended
   - Include information about:
     - Your living situation (house, apartment, yard size)
     - Experience with pets
     - Other pets in household
     - Family members and ages
     - Work schedule and time commitment

5. **Submit Application**
   - Click **"Submit Application"** button

6. **Track Your Application**
   - Navigate to **"Check Application Status"** in sidebar

#### Application Status Progression

1. **Pending** - Waiting for admin review
2. **Approved** - Congratulations! Contact shelter to arrange pickup
3. **Denied** - Application was not approved (reason provided)
4. **Cancelled** - You cancelled the application

---

### Check Status

Track your rescue missions and adoption applications in one place.

![Check Application Status](screenshots/07_check_applicationreport_status.png)


#### Step-by-Step Instructions

1. **Navigate to Status Page**
   - Click **"Check Application Status"** in sidebar

2. **View Rescue Missions Tab**
   - Lists all your submitted rescue missions
   - Shows current status with colored badges
   - Displays admin messages (if any)
   - Click row to expand details

3. **View Adoption Requests Tab**
   - Lists all your adoption applications
   - Shows current status
   - Displays approval/denial messages
   - Click row to expand details

4. **Filter by Status**
   - Use dropdown filters to show:
     - All statuses
     - Active only (pending, on-going, under review)
     - Completed (rescued, approved)
     - Archived

5. **Search**
   - Use search box to find specific animal name or mission

6. **Action Buttons**
   - **View Details**: Opens full detail page
   - **Cancel**: Cancel pending request (confirmation required)
   - **Archive**: Hide completed items from list

---

### Update Profile

Manage your personal information and account settings.

![Profile User Page](screenshots/08_profile_user_page.png)


#### Step-by-Step Instructions

1. **Navigate to Profile**
   - Click **"Profile"** in sidebar

2. **Update Personal Information**
   - **Name**: Click edit icon → Change name → Save
   - **Phone**: Click edit icon → Change phone → Save (must be unique)
   - **Email**: Click edit icon → Change email → Save (requires password confirmation)

3. **Change Password**
   - Click **"Change Password"** button
   - Enter **current password**
   - Enter **new password** (must meet requirements)
   - Enter **confirm new password**
   - Click **"Update Password"**

4. **Upload Profile Photo**
   - Click **"Change Photo"** button below your photo
   - Select image file (JPG, JPEG, PNG, GIF)
   - Photo preview updates immediately
   - Click **"Save Changes"** to save the new photo**

5. **Link Google Account**
   - Click **"Link Google Account"** button
   - Authorize PawRes to access Google profile
   - Once linked, you can login with Google

6. **Unlink Google Account**
   - Click **"Unlink Google Account"** button (requires password to be set first)
   - After unlinking, you'll need to use email/password login

---

## Admin Workflows

### Review Rescue Missions

Manage incoming rescue missions and coordinate rescue operations.

![Rescue Mission List with Status Filters](screenshots/9_rescue_mission_list.png)

#### Step-by-Step Instructions

1. **Navigate to Rescue Missions**
   - Click **"Manage Records"** in sidebar
   - Then select **"Rescue Missions"** tab or section

2. **View Pending Approvals**
   - Unreviewed missions appear with **"!" symbol**
   - Filter or search for pending missions

   ![Rescue Mission Detail with Photo and Map](screenshots/10_rescue_mission_detail.png)

3. **Update Mission Status**
   - Click the status badge dropdown
   - Select new status:
     - **On-Going**: Rescue team dispatched
     - **Rescued**: Animal successfully rescued
     - **Failed**: Rescue attempt unsuccessful

4. **Rescued Status Special Behavior**
   - When you mark mission as **"Rescued"**:
     - System automatically creates an animal record
     - Animal inherits details from rescue mission (species, breed, photo, etc.)
     - Animal status set to "Available"
     - Mission links to new animal record
   - You can then edit animal details in **Animals → Animals List**

5. **Archive or Remove Mission**
   - **Archive**: Hides completed missions from the active list
   - **Remove**: Marks invalid/spam reports as removed
   - Use action buttons (archive/delete icons) in the Actions column

6. **Filter and Search**
   - Use status filter: All, Pending, On-Going, Rescued, Failed, Cancelled
   - Use urgency filter: All, Low, Medium, High

---

### Manage Animals

Create, edit, and organize animal records in the system.

![Animal Management List with Action Buttons](screenshots/11_animal_management_list.png)

#### Add New Animal

1. **Navigate to Add Animal**
   - Click **"View Animal List"** in sidebar
   - Then click **"Add Animal"** button on the animal list page

2. **Upload Photo**
   - Click **"Upload Photo"** or drag-and-drop
   - Photo preview displays

3. **Use AI Breed Detection** (Optional)
   - Click **"Analyze with AI"** button
   - Review suggestions
   - Click suggestion to auto-fill breed

   ![AI Breed Detection Results](screenshots/12_ai_breed_detection.png)

4. **Fill Required Fields**
   - **Name**: Give animal a unique name
   - **Species**: Select from dropdown (Dog, Cat, etc.)
   - **Breed**: Enter specific breed (or "Mixed")
   - **Age**: Select age range
   - **Description**: Detailed description of the animal

5. **Submit**
   - Click **"Add Animal"** button
   - Success message displays
   - Animal appears in Animals List

#### Edit Existing Animal

1. **Navigate to Animals List**
   - Click **"View Animal List"** in sidebar

2. **Find Animal**
   - Use filters or search box
   - Click **"Edit"** button on animal card

3. **Update Fields**
   - Modify any field as needed
   - Change photo if desired
   - Update health status as animal receives care

4. **Save Changes**
   - Click **"Update Animal"** button
   - Confirmation message displays

#### Archive Animal

**When to Archive**:
- Animal has been adopted
- Animal has been transferred to another facility
- Animal is deceased (record keeping)

**How to Archive**:
1. Open animal detail page
2. Click **"Archive"** button
3. Confirm action
4. Animal removed from public "Available Animals" list
5. Still viewable by admins in **"Hidden Items"** page

**Restore from Archive**:
1. Navigate to **"Manage Records"** → **"Hidden Items"** section or tab
2. Select **"Animals"** tab
3. Find archived animal
4. Click **"Restore"** button

---

### Approve Adoption Requests

Review and process adoption applications from users.

![Adoption Request List with User Info](screenshots/13_adoption_request_list.png)

#### Step-by-Step Instructions

1. **Navigate to Adoption Requests**
   - Click **"Manage Records"** in sidebar
   - Then select **"Adoption Requests"** tab or section

2. **View Pending Approvals**
   - Unreviewed requests highlighted
   - Filter or search for pending requests

3. **Change Application Status**
   - Click the status badge dropdown on the request row
   - Select new status:
     - **Pending**: Mark as pending (waiting for review)
     - **Approved**: Approve the adoption
     - **Denied**: Deny the application
   - Status updates immediately
   - When approved, animal status changes to "Adopted"
   - User can check updated status in **"Check Application Status"** page

4. **Archive or Remove Request**
   - **Archive**: Use archive button (clock icon) to hide completed requests
   - **Remove**: Use remove button (trash icon) to mark invalid requests

5. **Filter Requests**
   - Filter by status: All, Pending, Approved, Denied, Cancelled

---

### Manage Users

Administer user accounts and permissions.

![User Management Table with Actions](screenshots/14_user_management_table.png)

#### Step-by-Step Instructions

1. **Navigate to User Management**
   - Click **"User Management"** in sidebar

2. **View All Users**
   - Table displays:
     - Name
     - Email
     - Role (User, Admin)
     - Status (Enabled, Disabled)
     - Registration date
     - Last login

3. **Search Users**
   - Use search box: "Search by name or email..."
   - Results filter in real-time

4. **Filter by Role**
   - Click **"All Roles"** dropdown
   - Select: All, Admin, User

5. **Filter by Status**
   - Click **"All Statuses"** dropdown
   - Select: All, Enabled, Disabled

6. **Disable User Account**
   - Click **"Disable"** button next to user
   - Confirmation dialog: "Are you sure you want to disable [User Name]?"
   - Click **"Confirm"**
   - User immediately locked out
   - User receives "Account disabled" message on login attempt

7. **Enable User Account**
   - Find disabled user (use status filter)
   - Click **"Enable"** button
   - Confirmation dialog
   - Click **"Confirm"**
   - User can login again

8. **Reset User Password**
   - Click **"Reset Password"** button (lock icon)
   - Enter new password in dialog
   - Confirm new password
   - Click **"Reset Password"** to save
   - Share new password with user via secure channel (email, phone)

9. **Delete User** (Use with Caution)
   - Click **"Delete"** button (trash icon)
   - Confirmation dialog appears with warning
   - Click **"Delete"** to confirm
   - User account removed
   - Consider disabling users instead of deleting them

10. **View User Details**
    - Click **"Edit"** button to view and edit user information
    - User table shows:
      - Name and email
      - Role and status
      - Last login date

---

### View Audit Logs

Monitor system activity and security events.

![Audit Log Viewer with Filters](screenshots/15_audit_log_view.png)

#### Step-by-Step Instructions

1. **Navigate to Audit Logs**
   - Click **"Audit Logs"** in sidebar

2. **View Recent Events**
   - Logs display in reverse chronological order (newest first)
   - Each entry shows:
     - **Timestamp**: Date and time of event
     - **Event Type**: Category of event (see below)
     - **User**: Who performed the action
     - **Details**: Specific action details
     - **IP Address**: Request origin (if applicable)

3. **Filter by Event Type**
   - Click **"Event Type"** dropdown
   - Select:
     - **All Events**: Everything
     - **Authentication**: Login, logout, failed login, lockout
     - **Admin Actions**: Approve, deny, status changes, user management
     - **Security**: Password changes, account disable/enable, suspicious activity
     - **Data Changes**: Create, update, delete operations
     - **System**: Startup, shutdown, configuration changes

4. **Export Logs**
   - Click **"Export CSV"** button
   - CSV file is saved to storage/data/exports/
   - Contains timestamp, level, and message columns

#### Event Types Explained

| Event Type | Examples |
|------------|----------|
| **Authentication** | User login, logout, failed login attempt, account lockout |
| **Admin Actions** | Rescue status changed, adoption approved/denied, user disabled |
| **Security** | Password changed, multiple failed logins, permission denied |
| **Data Changes** | Animal created/updated/deleted, user profile updated |
| **System** | Application started, configuration loaded, backup created |

---

### Import Animals from CSV/Excel

Bulk import animal records from spreadsheet files.

![Import Dialog with File Upload and Preview](screenshots/16_bulk_import_dialog.png)

#### Step-by-Step Instructions

1. **Prepare Import File**
   - Create CSV or Excel file with these columns (in order):
     1. `name` - Animal name (required)
     2. `species` - Dog, Cat, Other (required)
     3. `breed` - Breed name (optional)
     4. `age` - Number 0-21 (optional)
     5. `health_status` - Healthy, Recovering, Injured (optional)
     6. `photo` - Photo filename relative to import file (optional)

2. **Navigate to Import**
   - Click **"View Animal List"** in sidebar
   - Click **"Add Animal"** button
   - Click **"Bulk Import"** button in the Add Animal page

3. **Upload File**
   - Click **"Choose File"** button
   - Select your CSV or Excel file
   - Click **"Open"**

4. **Confirm Import**
   - If no errors, click **"Import [X] Animals"** button
   - Progress bar displays
   - Wait for completion (may take several seconds for large files)

5. **Review Results**
   - Success message shows:
     - **Imported**: Number of animals successfully added
     - **Skipped**: Number of rows with errors
     - **Duplicates**: Rows skipped due to duplicate names
   - Click **"View Import Log"** for details

6. **Verify Imported Animals**
   - Navigate to **"Animals"** → **"Animals List"**
   - Use filters to find imported animals
   - Spot-check a few records for accuracy

#### Import Tips

- **Photo Handling**: If photo column contains filenames, place image files in `storage/uploads/` before importing
- **Duplicate Detection**: Animals with matching names are skipped (case-insensitive)
- **Batch Size**: For large imports (>500 animals), split into multiple files
- **Encoding**: Save CSV as UTF-8 to handle special characters

---

## Feature Guides

### AI Breed Detection

PawRes includes AI-powered breed classification to assist with animal identification.

![AI Analysis with Confidence Scores](screenshots/17_AI_analysis.png)

#### How It Works

1. **Model Requirements**
   - First-time use requires downloading AI models (~100 MB)
   - Click **"Download Models"** when prompted
   - Progress bar displays during download
   - Models stored locally for offline use

2. **Classify Animal Photo**
   - Upload a clear photo of the animal (close-up of face/body preferred)
   - Click **"Analyze with AI"** button
   - Wait 5-10 seconds for analysis

3. **Review Results**
   - AI returns top 3 breed predictions with confidence scores
   - Example:
     - **Labrador Retriever** - 87% confidence
     - **Golden Retriever** - 8% confidence
     - **Mixed Breed** - 5% confidence

4. **Apply Suggestion**
   - Click any suggestion to auto-fill the breed field
   - You can manually edit the breed after selection

5. **Interpretation**
   - **High confidence (>70%)**: Likely accurate, trust the suggestion
   - **Medium confidence (40-70%)**: Consider suggestion but verify
   - **Low confidence (<40%)**: Manual identification recommended

#### Limitations

- **Accuracy**: AI is trained on common breeds; rare breeds may not be recognized
- **Photo Quality**: Blurry, dark, or distant photos reduce accuracy
- **Mixed Breeds**: AI may struggle with mixed breeds
- **Species**: Currently supports dogs and cats only

#### Best Practices

✅ **Do**:
- Use clear, well-lit photos
- Capture animal from multiple angles
- Re-run analysis if first result seems incorrect

❌ **Don't**:
- Rely solely on AI for critical decisions
- Use AI for species identification (human verification required)
- Expect 100% accuracy for mixed breeds

---

### Map Usage

Interactive maps help visualize rescue locations and shelter boundaries.

![Map Interface with Marker and Controls](screenshots/18_interactive_map.png)

#### Map Features

1. **View Map**
   - Displays on rescue form and rescue mission detail pages
   - Default view: Centered on shelter location
   - Zoom controls: +/- buttons or mouse wheel

2. **Set Location (Rescue Form)**
   - **Method 1**: Type address
     - Enter address in "Location" field
     - Address will be geocoded when you submit the form
   - **Method 2**: Use current location
     - Click the GPS button (📍) next to the location field
     - Allow browser location permission
     - Your coordinates will be captured automatically

3. **View Location (Mission Detail)**
   - Red marker shows reported location
   - Zoom in for street-level detail
   - Click marker for address popup

4. **Map Controls**
   - **Zoom In/Out**: +/- buttons or mouse wheel
   - **Pan**: Click and drag to move the map
   - **Lock/Unlock**: Toggle map interaction (admin view)

#### Troubleshooting

**Map Not Loading**:
- Check internet connection
- Refresh page
- Clear browser cache

**"Use My Current Location" Not Working**:
- Allow location permission in browser
- Ensure device has GPS or location services enabled
- Try entering address manually instead

**Geocoding Failed**:
- Check address spelling
- Try using landmark + city name
- Click the GPS button (📍) to capture your current location instead

---

### Charts & Analytics

Visualize data trends with interactive charts on the dashboard.

![Dashboard with Multiple Chart Types](screenshots/19_dashboard_charts.png)

#### Chart Types

1. **Bar Charts**
   - Display counts by category (e.g., animals by species)
   - Labels show counts
   - Legend on right side for color mapping

2. **Pie Charts**
   - Show proportions (e.g., adoption status distribution)
   - Percentages displayed on slices
   - Legend on right side

3. **Line Charts**
   - Show trends over time (e.g., rescues per month)
   - Data points marked with dots
   - Legend shows series colors and totals

4. **Stat Cards**
   - Quick overview numbers
   - Color-coded by status (green=good, yellow=warning, red=urgent)
   - Click card to navigate to related page

#### Interacting with Charts

1. **View Chart Details**
   - Click the expand icon on chart cards to see detailed breakdown
   - Popup dialogs show complete data with all items listed

2. **Refresh Data**
   - Navigate away and back to refresh charts
   - Charts show data for the last 30 days by default

#### Available Charts

**Admin Dashboard**:
- **Rescued vs. Adopted (14 Days)**: Line chart showing rescue and adoption trends
- **Breed Distribution**: Pie chart of most common breeds

**Charts Page**:
- **Rescued vs. Adopted (30 Days)**: Line chart showing monthly trends
- **Animals by Species**: Pie chart of species distribution
- **Health Status**: Bar chart showing healthy, recovering, injured counts
- **Rescue Status**: Pie chart showing pending, on-going, rescued, failed counts
- **Adoption Status**: Pie chart showing pending, approved, denied counts
- **Urgency Distribution**: Bar chart showing low, medium, high urgency counts
- **Species Ranking**: Bar chart of most adopted species
- **Breed Distribution**: Pie chart of all breeds
- **Rescue Mission Map**: Interactive map showing rescue locations

---

## Common Tasks

### Change Your Password

1. Navigate to **Profile** (click profile section at bottom of sidebar)
2. Scroll to **"Change Password"** section
3. Enter current password
4. Enter new password (must meet requirements)
5. Confirm new password
6. Click **"Change Password"** button
7. Success message displays

---

### Upload Photo

#### For Animal Records (Admin)

1. Open add/edit animal form
2. Click **"Upload Photo"** button or drag-and-drop
3. Select image file (JPG, PNG, GIF, WEBP)
4. Photo preview displays
5. Click **"Save"** or **"Update"** to commit

#### For Rescue Missions (User)

1. Open rescue form
2. Click **"Upload Photo"** in photo section
3. Select image file
4. Photo preview displays
5. (Optional) Click **"Analyze with AI"** for breed detection
6. Submit form

#### Photo Requirements

- **Formats**: JPG, JPEG, PNG, GIF, WEBP
- **Maximum Size**: 5 MB
- **Recommended**: Clear, well-lit, close-up shots

---

### Cancel Pending Request

#### Cancel Rescue Mission

1. Navigate to **"Check Application Status"** in sidebar
2. Find pending mission
3. Click **"Cancel"** button
4. Confirmation dialog: "Are you sure? This action cannot be undone."
5. Click **"Confirm"**
6. Mission status changes to "Cancelled"

#### Cancel Adoption Application

1. Navigate to **"Check Application Status"** in sidebar
2. Find pending application
3. Click **"Cancel"** button
4. Confirmation dialog
5. Click **"Confirm"**
6. Application status changes to "Cancelled"

**Note**: You cannot cancel requests that are already being processed (On-Going, Under Review) or completed.

---

### Archive Completed Items

#### Archive Rescue Mission (User)

1. Navigate to **"Check Application Status"** in sidebar
2. Find completed mission (Rescued, Cancelled)
3. Click **"Archive"** button
4. Mission hidden from main list
5. May be viewable in archived items section (if enabled for users)

#### Archive Animal (Admin)

1. Navigate to **"View Animal List"** in sidebar
2. Find animal to archive
3. Click **"Archive"** button
4. Confirmation: "This will hide the animal from public view."
5. Click **"Confirm"**
6. Animal removed from public animal list
7. Still viewable in **"Manage Records"** → **"Hidden Items"** section

---

### Export Data (Admin Only)

#### Export Animals to CSV

1. Navigate to **"View Animal List"** in sidebar (admin view)
2. Click **"Export"** button (top-right)
3. CSV file is saved to `storage/data/exports/`
4. Success message shows filename

#### Export Adoption Records

1. Navigate to **"Manage Records"** in sidebar
2. Select **"Adoptions"** tab
3. Click **"Export"** button
4. CSV file is saved to `storage/data/exports/`

#### Export Rescue Missions

1. Navigate to **"Manage Records"** in sidebar
2. Select **"Rescues"** tab
3. Click **"Export"** button
4. CSV file is saved to `storage/data/exports/`

**Note**: Exported files are saved on the server in `app/storage/data/exports/`. Access them directly from that folder.

---

## Troubleshooting

### Forgot Password

**Solution**:
- Contact an administrator to reset your password
- Admin can reset passwords via **User Management** page (lock icon button)
- Admin will set a new password for you
- You can change it later from your Profile page

---

### Account Locked

**Cause**: 5 consecutive failed login attempts

**Solution 1 - Wait**:
- Wait 15 minutes
- Account automatically unlocks
- Try logging in again

**Solution 2 - Contact Admin**:
- Email your admin team
- Provide your registered email
- Admin can manually unlock account

**Prevention**:
- Use password manager to avoid typos
- Write down your password securely if needed
- Reset password if you've forgotten it

---

### Session Expired

**Cause**: Inactivity for 30+ minutes (default timeout, configurable via SESSION_TIMEOUT_MINUTES)

**What to do**:
1. You'll be automatically redirected to login page
2. Message displays: "Your session has expired. Please login again."
3. Enter credentials
4. You'll return to your previous page

**Prevention**:
- Save work frequently
- Keep the application active if working on long tasks
- Adjust session timeout (admin setting)

---

### Photo Upload Failed

**Common Causes & Solutions**:

1. **File Too Large**
   - Error: "File size exceeds 5 MB limit"
   - Solution: Resize image using image editor or online tool

2. **Invalid File Type**
   - Error: "Unsupported file format"
   - Solution: Convert to JPG or PNG

3. **Network Error**
   - Error: "Upload failed. Please try again."
   - Solution: Check internet connection, retry upload

4. **Storage Full (Admin)**
   - Error: "Server storage full"
   - Solution: Contact system administrator to expand storage

**Tips**:
- Compress images before upload (use online tools like TinyPNG)
- Use JPG for photos, PNG for graphics
- Ensure stable internet connection

---

### AI Model Download Stuck

**Symptoms**:
- Download progress bar frozen
- "Downloading models..." message for >5 minutes

**Solutions**:

1. **Refresh Page**
   - Close AI dialog
   - Refresh browser (F5)
   - Try download again

2. **Check Disk Space**
   - Models require ~100 MB free space
   - Free up space if needed

3. **Check Internet Connection**
   - Ensure stable, fast connection
   - Avoid mobile data (large download)

4. **Manual Download (Admin)**
   - Contact admin to manually place model files in `storage/ai_models/`

5. **Skip AI Detection**
   - You can manually enter breed without AI
   - AI is a helper, not required

---

### Can't Find Animal in List

**Possible Reasons**:

1. **Animal is Archived**
   - Solution: Admin can check **"Hidden Items"** → **"Animals"** tab

2. **Filters Applied**
   - Solution: Reset all filters (click "Clear Filters")

3. **Wrong Species Selected**
   - Solution: Change species filter to "All"

4. **Search Typo**
   - Solution: Clear search box or try different keywords

5. **Animal Not Yet Created**
   - Solution: Check if rescue mission is marked "Rescued" (triggers animal creation)

---

### Charts Not Loading

**Solutions**:

1. **Refresh Page**
   - Click browser refresh (F5)

2. **Clear Cache**
   - Ctrl+Shift+Delete (Chrome/Edge)
   - Clear cached images and files
   - Refresh page

3. **Check Permissions**
   - Ensure you have admin access (if admin-only charts)

4. **Check Data**
   - Charts require data to display
   - If no animals/rescues exist, charts show "No data available"

---

### Lost Data After Editing

**Prevention**:
- Always click **"Save"** or **"Update"** button
- Don't navigate away without saving
- Look for unsaved changes warning

**Recovery**:
- Unfortunately, unsaved changes are lost
- Re-enter data and save again
- Use browser "Back" button only if you haven't navigated to another page

---

### Admin Can't Approve Adoption

**Possible Causes**:

1. **Animal Already Adopted**
   - Check if another admin already approved a different application
   - View animal details to confirm status

2. **Application Already Processed**
   - Check if you already denied this application
   - View adoption request history

3. **Database Lock**
   - Rare concurrency issue
   - Wait 30 seconds and try again

---

### Google Login Not Working

**Common Issues**:

1. **OAuth Not Configured**
   - Contact admin to configure Google OAuth
   - Check if Google credentials are set in `.env` file

2. **Browser Blocking Popup**
   - Allow popups for PawRes domain
   - Try again after allowing popups

3. **Google Account Not Linked**
   - First-time users must register with email/password
   - Then link Google account from Profile page

4. **Google Account Mismatch**
   - Ensure you're using the same Google account linked to your PawRes profile

---

## Need More Help?

### Contact Information

- **Technical Support**: [Contact your system administrator]
- **User Guides**: Check this manual first
- **Bug Reports**: [Link to issue tracker if available]

### Additional Resources

- **[Architecture Documentation](ARCHITECTURE.md)** - System design details
- **[Database Schema](DATABASE.md)** - Data structure reference
- **[Security Policies](SECURITY.md)** - Security best practices
- **[Setup Guide](SETUP.md)** - Installation instructions

---

## Document Version

**Version**: 1.0  
**Last Updated**: December 8, 2025  
**Maintained By**: PawRes Development Team

---

*Thank you for using PawRes to help rescue and rehome animals! Together, we make a difference.* 🐾
