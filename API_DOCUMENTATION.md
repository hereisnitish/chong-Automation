# Make.com Webhook API Documentation

## Create Dashboard Record Endpoint

**URL:** `http://your-domain.com/api/create-record/`  
**Method:** `POST`  
**Content-Type:** `application/json` or `application/x-www-form-urlencoded`

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `email` | string | Email address for the record | `"user@example.com"` |
| `phone_number` | string | Phone number | `"+1234567890"` |
| `type` | string | Type of automation (whatsapp, gmail, sms) | `"whatsapp"` |

### Optional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `google_drive_link` | string | Google Drive link URL | `"https://drive.google.com/..."` |
| `user_email` | string | Email of the user to associate this record with | `"admin@example.com"` |

**Note:** If `user_email` is not provided, the record will be associated with the first user in the database.

### Request Examples

#### JSON Format (Recommended for Make.com)

```json
{
  "email": "contact@example.com",
  "phone_number": "+1234567890",
  "type": "whatsapp",
  "google_drive_link": "https://drive.google.com/file/d/abc123",
  "user_email": "admin@yoursite.com"
}
```

#### cURL Example

```bash
curl -X POST http://your-domain.com/api/create-record/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "contact@example.com",
    "phone_number": "+1234567890",
    "type": "whatsapp",
    "google_drive_link": "https://drive.google.com/file/d/abc123",
    "user_email": "admin@yoursite.com"
  }'
```

### Response Examples

#### Success Response (201 Created)

```json
{
  "status": "success",
  "message": "Dashboard record created successfully",
  "data": {
    "id": 1,
    "email": "contact@example.com",
    "phone_number": "+1234567890",
    "type": "whatsapp",
    "google_drive_link": "https://drive.google.com/file/d/abc123",
    "created_date": "2025-11-06T10:30:45.123456",
    "user": "admin@yoursite.com"
  }
}
```

#### Error Response - Missing Fields (400 Bad Request)

```json
{
  "status": "error",
  "message": "Missing required fields: email, phone_number, type"
}
```

#### Error Response - Invalid Type (400 Bad Request)

```json
{
  "status": "error",
  "message": "Invalid type. Must be: whatsapp, gmail, or sms"
}
```

#### Error Response - User Not Found (404 Not Found)

```json
{
  "status": "error",
  "message": "User with email admin@yoursite.com not found"
}
```

### Make.com Configuration

1. **Add HTTP Module** in your Make.com scenario
2. **Select "Make a request"**
3. Configure:
   - **URL:** `http://your-domain.com/api/create-record/`
   - **Method:** `POST`
   - **Headers:**
     - `Content-Type`: `application/json`
   - **Body type:** `Raw`
   - **Content type:** `JSON (application/json)`
   - **Request content:**
     ```json
     {
       "email": "{{email}}",
       "phone_number": "{{phone}}",
       "type": "{{type}}",
       "google_drive_link": "{{drive_link}}",
       "user_email": "{{user_email}}"
     }
     ```

4. Map your Make.com variables to the JSON fields

### Valid Type Values

- `whatsapp` - WhatsApp Message
- `gmail` - Gmail
- `sms` - SMS

### Important Notes

- This endpoint does **NOT** require authentication (CSRF exempt)
- The endpoint only accepts POST requests
- If `user_email` is not provided, it uses the first user in the database
- All timestamps are returned in ISO 8601 format
- Phone numbers should include country code (e.g., +1234567890)

### Testing Locally

```bash
# Start your Django server
python manage.py runserver

# Test with curl
curl -X POST http://127.0.0.1:8000/api/create-record/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "phone_number": "+1234567890",
    "type": "whatsapp",
    "google_drive_link": "https://drive.google.com/test"
  }'
```

### Production Deployment

When deploying to production:
1. Replace `http://your-domain.com` with your actual domain
2. Ensure ALLOWED_HOSTS includes your domain in settings.py
3. Use HTTPS for secure communication
4. Consider adding API authentication/rate limiting for production use

---

## Search Email Folder Records Endpoint

**URL:** `http://your-domain.com/api/search-email/`  
**Method:** `GET` or `POST`  
**Content-Type:** `application/json` (for POST) or URL parameters (for GET)

### Purpose

This endpoint searches for folder structure records associated with a specific email in the **EmailFolder** table and provides boolean checks about:
- Whether the email has any folder records in the database
- Folder records from the current year
- Folder records from the current month
- Folder records from today

### Required Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `email` | string | Email address to search for | `"user@example.com"` |

### Request Examples

#### GET Request (URL Parameter)

```bash
curl -X GET "http://your-domain.com/api/search-email/?email=contact@example.com"
```

#### POST Request (JSON)

```bash
curl -X POST http://your-domain.com/api/search-email/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "contact@example.com"
  }'
```

#### POST Request (Form Data)

```bash
curl -X POST http://your-domain.com/api/search-email/ \
  -d "email=contact@example.com"
```

### Response Examples

#### Success Response - Email Found (200 OK)

**All folder IDs exist:**
```json
{
  "status": "success",
  "email": "contact@example.com",
  "exists": true,
  "has_current_year": true,
  "has_current_month": true,
  "has_today": true,
  "message": "Folder records found for this email",
  "email_folder_id": "1a2b3c4d5e6f",
  "year_folder_id": "7g8h9i0j1k2l",
  "month_folder_id": "3m4n5o6p7q8r",
  "date_folder_id": "9s0t1u2v3w4x"
}
```

**Only email and year folders exist:**
```json
{
  "status": "success",
  "email": "contact@example.com",
  "exists": true,
  "has_current_year": true,
  "has_current_month": false,
  "has_today": false,
  "message": "Folder records found for this email",
  "email_folder_id": "1a2b3c4d5e6f",
  "year_folder_id": "7g8h9i0j1k2l"
}
```

#### Success Response - Email Not Found (200 OK)

```json
{
  "status": "success",
  "email": "newuser@example.com",
  "exists": false,
  "has_current_year": false,
  "has_current_month": false,
  "has_today": false,
  "message": "No folder records found for this email"
}
```

#### Error Response - Missing Email (400 Bad Request)

```json
{
  "status": "error",
  "message": "Email parameter is required"
}
```

### Response Fields Explanation

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Request status ("success" or "error") |
| `email` | string | The email address that was searched |
| `exists` | boolean | Whether any folder records exist for this email (all time) |
| `has_current_year` | boolean | Whether folder records exist for the current year |
| `has_current_month` | boolean | Whether folder records exist for the current month |
| `has_today` | boolean | Whether folder records were created today |
| `message` | string | Human-readable message about the result |
| `email_folder_id` | string | *(Optional)* Google Drive folder ID for email - returned if exists |
| `year_folder_id` | string | *(Optional)* Google Drive folder ID for year - returned if has_current_year is true |
| `month_folder_id` | string | *(Optional)* Google Drive folder ID for month - returned if has_current_month is true |
| `date_folder_id` | string | *(Optional)* Google Drive folder ID for date - returned if has_today is true |

### Use Cases

1. **Check if folder structure already created today and use existing IDs:**
   ```javascript
   // In Make.com or other automation tool
   if (response.has_today === true) {
     // Use existing folder IDs
     const emailFolderId = response.email_folder_id;
     const yearFolderId = response.year_folder_id;
     const monthFolderId = response.month_folder_id;
     const dateFolderId = response.date_folder_id;
     console.log("Upload file to existing folder:", dateFolderId);
   } else {
     // Create new date folder
     console.log("Create new date folder for today");
   }
   ```

2. **Smart folder creation based on existing structure:**
   ```javascript
   if (response.has_current_month === true) {
     // Month folder exists - only create date folder
     const parentFolderId = response.month_folder_id;
     console.log("Create date folder inside:", parentFolderId);
   } else if (response.has_current_year === true) {
     // Year exists - create month and date folders
     const parentFolderId = response.year_folder_id;
     console.log("Create month/date folders inside:", parentFolderId);
   } else if (response.exists === true) {
     // Email exists - create year/month/date folders
     const parentFolderId = response.email_folder_id;
     console.log("Create year/month/date folders inside:", parentFolderId);
   } else {
     // New email - create complete hierarchy
     console.log("Create email/year/month/date folders");
   }
   ```

3. **Reuse existing folder structure:**
   ```javascript
   if (response.exists === false) {
     // New email - create complete folder hierarchy
     console.log("New email, create all folders");
   } else {
     // Email folder exists - reuse it
     console.log("Email folder ID:", response.email_folder_id);
     
     if (response.has_current_year === false) {
       console.log("Create new year folder inside:", response.email_folder_id);
     }
   }
   ```

4. **Get parent folder ID for file upload:**
   ```javascript
   // Determine where to upload the file
   let uploadFolderId;
   
   if (response.has_today === true) {
     uploadFolderId = response.date_folder_id;
   } else if (response.has_current_month === true) {
     uploadFolderId = response.month_folder_id;
   } else if (response.has_current_year === true) {
     uploadFolderId = response.year_folder_id;
   } else if (response.exists === true) {
     uploadFolderId = response.email_folder_id;
   }
   
   console.log("Upload file to folder:", uploadFolderId);
   ```

### Make.com Configuration

1. **Add HTTP Module** before your main workflow
2. **Configure as a filter/checker:**
   - **URL:** `http://your-domain.com/api/search-email/?email={{email}}`
   - **Method:** `GET`
   - Parse the response to check `has_today` field
   - Use router to decide if processing should continue

### Testing Examples

```bash
# Test with existing email
curl -X GET "http://127.0.0.1:8000/api/search-email/?email=test@example.com"

# Test with non-existing email
curl -X GET "http://127.0.0.1:8000/api/search-email/?email=newuser@example.com"

# Test POST with JSON
curl -X POST http://127.0.0.1:8000/api/search-email/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

### Important Notes

- This endpoint searches the **EmailFolder** table (not Dashboard table)
- Used to check if Google Drive folder structure exists before creating new folders
- Does **NOT** require authentication (CSRF exempt)
- Accepts both GET and POST methods for flexibility
- Returns 200 OK even when email is not found (check `exists` field)
- All boolean fields are explicitly `true` or `false`
- Response is optimized for quick conditional checks in automation workflows
- Uses server's timezone for date/time comparisons based on `created_at` field
- Efficient database queries with minimal overhead
- Perfect for use as a filter/router in Make.com folder creation scenarios

---

## Create Email Folder Endpoint

**URL:** `http://your-domain.com/api/create-email-folder/`  
**Method:** `POST`  
**Content-Type:** `application/json` or `application/x-www-form-urlencoded`

### Purpose

This endpoint creates a new EmailFolder record to store the complete Google Drive folder structure (email folder, year folder, month folder, and date folder IDs) for a specific email address.

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `email` | string | Email address | `"user@example.com"` |
| `email_folder_id` | string | Google Drive folder ID for the email folder | `"1a2b3c4d5e6f"` |
| `year_folder_id` | string | Google Drive folder ID for the year folder | `"7g8h9i0j1k2l"` |
| `month_folder_id` | string | Google Drive folder ID for the month folder | `"3m4n5o6p7q8r"` |
| `date_folder_id` | string | Google Drive folder ID for the date folder | `"9s0t1u2v3w4x"` |
| `folder_year` | integer | The actual year the folder represents | `2025` |
| `folder_month` | integer | The actual month the folder represents (1-12) | `11` |
| `folder_date` | string (YYYY-MM-DD) | The actual date the folder represents | `"2025-11-06"` |

### Request Examples

#### JSON Format (Recommended for Make.com)

```json
{
  "email": "contact@example.com",
  "email_folder_id": "1a2b3c4d5e6f",
  "year_folder_id": "7g8h9i0j1k2l",
  "month_folder_id": "3m4n5o6p7q8r",
  "date_folder_id": "9s0t1u2v3w4x",
  "folder_year": 2025,
  "folder_month": 11,
  "folder_date": "2025-11-06"
}
```

#### cURL Example

```bash
curl -X POST http://your-domain.com/api/create-email-folder/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "contact@example.com",
    "email_folder_id": "1a2b3c4d5e6f",
    "year_folder_id": "7g8h9i0j1k2l",
    "month_folder_id": "3m4n5o6p7q8r",
    "date_folder_id": "9s0t1u2v3w4x",
    "folder_year": 2025,
    "folder_month": 11,
    "folder_date": "2025-11-06"
  }'
```

### Response Examples

#### Success Response (201 Created)

```json
{
  "status": "success",
  "message": "Email folder record created successfully",
  "data": {
    "id": 1,
    "email": "contact@example.com",
    "email_folder_id": "1a2b3c4d5e6f",
    "year_folder_id": "7g8h9i0j1k2l",
    "month_folder_id": "3m4n5o6p7q8r",
    "date_folder_id": "9s0t1u2v3w4x",
    "folder_year": 2025,
    "folder_month": 11,
    "folder_date": "2025-11-06",
    "created_at": "2025-11-06T10:30:45.123456",
    "updated_at": "2025-11-06T10:30:45.123456"
  }
}
```

#### Error Response - Missing Fields (400 Bad Request)

```json
{
  "status": "error",
  "message": "Missing required fields: email, email_folder_id, year_folder_id, month_folder_id, date_folder_id, folder_year, folder_month, folder_date"
}
```

#### Error Response - Duplicate Entry (400 Bad Request)

```json
{
  "status": "error",
  "message": "This folder structure already exists for this email and date"
}
```

### Make.com Configuration

1. **Add HTTP Module** after creating folders in Google Drive
2. **Configure:**
   - **URL:** `http://your-domain.com/api/create-email-folder/`
   - **Method:** `POST`
   - **Headers:**
     - `Content-Type`: `application/json`
   - **Body type:** `Raw`
   - **Content type:** `JSON (application/json)`
   - **Request content:**
     ```json
     {
       "email": "{{email}}",
       "email_folder_id": "{{email_folder_id}}",
       "year_folder_id": "{{year_folder_id}}",
       "month_folder_id": "{{month_folder_id}}",
       "date_folder_id": "{{date_folder_id}}",
       "folder_year": {{formatDate(now; "YYYY")}},
       "folder_month": {{formatDate(now; "M")}},
       "folder_date": "{{formatDate(now; "YYYY-MM-DD")}}"
     }
     ```

3. Map the Google Drive folder IDs from previous steps to the JSON fields
4. Use Make.com's date functions to populate folder_year, folder_month, and folder_date

### Typical Make.com Workflow

```
1. Check if folders exist (api/search-email/)
   ↓
2. If not exists, create folder structure in Google Drive
   ↓
3. Save folder IDs to database (api/create-email-folder/)
   ↓
4. Continue with file upload
```

### Use Cases

1. **After creating new folder structure:**
   ```javascript
   // After creating folders in Google Drive
   const currentDate = new Date();
   const response = await createEmailFolder({
     email: "user@example.com",
     email_folder_id: emailFolder.id,
     year_folder_id: yearFolder.id,
     month_folder_id: monthFolder.id,
     date_folder_id: dateFolder.id,
     folder_year: currentDate.getFullYear(),
     folder_month: currentDate.getMonth() + 1,
     folder_date: currentDate.toISOString().split('T')[0]
   });
   console.log("Folder structure saved:", response.data.id);
   ```

2. **Complete automation workflow:**
   ```javascript
   // Step 1: Check if folders exist
   const checkResponse = await searchEmail(email);
   const currentDate = new Date();
   const year = currentDate.getFullYear();
   const month = currentDate.getMonth() + 1;
   const dateStr = currentDate.toISOString().split('T')[0];
   
   if (!checkResponse.has_today) {
     // Step 2: Create folders in Google Drive
     let emailFolderId = checkResponse.email_folder_id;
     let yearFolderId = checkResponse.year_folder_id;
     let monthFolderId = checkResponse.month_folder_id;
     
     // Create missing folders...
     const dateFolderId = createGoogleDriveFolder(dateStr, monthFolderId);
     
     // Step 3: Save to database
     await createEmailFolder({
       email: email,
       email_folder_id: emailFolderId,
       year_folder_id: yearFolderId,
       month_folder_id: monthFolderId,
       date_folder_id: dateFolderId,
       folder_year: year,
       folder_month: month,
       folder_date: dateStr
     });
   }
   ```

### Important Notes

- This endpoint does **NOT** require authentication (CSRF exempt)
- Only accepts POST requests
- All fields are required - you must provide all folder IDs and date information
- `folder_year`, `folder_month`, and `folder_date` must match the actual year/month/date the folders represent
- Duplicate folder structures are prevented by unique constraint on email + folder_year + folder_month + folder_date
- Folder IDs should be valid Google Drive folder IDs
- `folder_date` must be in YYYY-MM-DD format
- `folder_month` should be 1-12 (integer)
- Created and updated timestamps are automatically generated
- Returns 201 status code on successful creation

### Testing Locally

```bash
# Start your Django server
python manage.py runserver

# Test with curl
curl -X POST http://127.0.0.1:8000/api/create-email-folder/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "email_folder_id": "test_email_folder_123",
    "year_folder_id": "test_year_folder_456",
    "month_folder_id": "test_month_folder_789",
    "date_folder_id": "test_date_folder_012",
    "folder_year": 2025,
    "folder_month": 11,
    "folder_date": "2025-11-06"
  }'
```

