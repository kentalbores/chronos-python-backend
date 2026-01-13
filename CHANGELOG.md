# Changelog

All notable changes to the Chronos Attendance Management API project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-09

### ✨ Added

#### 🏗️ Core Architecture

- **FastAPI Application Framework**
  - Modern Python 3.9+ REST API using FastAPI framework
  - Clean layered architecture following best practices
  - API Layer (`src/api/v1/`): REST endpoints and request/response handling
  - Services Layer (`src/services/`): Business logic separation
  - Models Layer (`src/models/`): Pydantic schemas for data validation
  - Core Layer (`src/core/`): Configuration and settings management
  - Helpers/Utils Layer: Reusable utility functions

- **Poetry Dependency Management**
  - Full Poetry integration for dependency management
  - Lock file for reproducible builds
  - Custom scripts: `poetry run start` and `poetry run test`

#### 👥 User Management Module

- **Complete User CRUD Operations**
  - `GET /v1/users` - Retrieve all users with advanced filtering
  - `GET /v1/users/{user_id}` - Get specific user by ID
  - `POST /v1/users` - Create new user with Auth0 integration
  - `PATCH /v1/users/{user_id}` - Update existing user
  - `DELETE /v1/users` - Soft delete user (sets `deleted_at`, blocks Auth0 login)
  - `POST /v1/users/{user_id}/restore` - Restore soft-deleted user

- **Advanced User Filtering & Search**
  - Search by name or email (partial match, case-insensitive)
  - Filter by department name
  - Filter by work status (on_site, wfh)
  - Filter by shift type (day, night)
  - Filter by employment type (Intern, Regular)
  - Filter by RFID status
  - Date range filtering by hire date
  - Pagination with configurable limit and offset

- **Employee & Intern Support**
  - Combined user response with employee details
  - Automatic intern detection based on university fields
  - Support for intern-specific data (university, hourly rate, required hours, etc.)
  - Employment type classification (Intern vs Regular)

- **Auth0 Login Info Endpoint**
  - `GET /v1/users/auth0/{auth0_id}` - Get user login info by Auth0 ID
  - Validates `canLogin` status in app_metadata
  - Determines first login status based on password reset/login timestamps
  - Returns user roles, profile, and authentication status

#### 📋 Attendance Management Module

- **Daily Attendance Tracking**
  - `GET /v1/attendance/today` - Get today's attendance for all employees
  - `GET /v1/attendance/date/{target_date}` - Get attendance for specific date
  - Real-time attendance status calculation (early-in, on-time, late-entry, absent)
  - Automatic clock-in/clock-out detection from RFID logs

- **Employee-Specific Attendance**
  - `GET /v1/attendance/employee/{user_id}` - Get employee's today attendance
  - `GET /v1/attendance/employee/{user_id}/date/{target_date}` - Get attendance by date
  - Complete tap-in/tap-out session logs
  - Total hours worked calculation

- **Period-Based Attendance**
  - `GET /v1/attendance/employee/{user_id}/period?period=week|month` - Weekly/monthly attendance
  - `GET /v1/attendance/employee/{user_id}/range` - Custom date range attendance
  - Daily breakdown with clock-in/out times and status
  - Aggregated statistics (presents, lates, absences, total hours)

- **Attendance Distribution & Charts**
  - `GET /v1/attendance/distribution` - Today's employee distribution by department
  - `GET /v1/attendance/distribution/date/{target_date}` - Distribution for specific date
  - Pie chart data with department colors
  - Present/absent counts per department

- **Attendance Reporting**
  - `GET /v1/attendance/report?start_date=&end_date=` - Comprehensive attendance report
  - Aggregated data: presents, lates, absences, total hours
  - Attendance score calculation with late penalty
  - Performance rating (Excellent, Fair, Poor, Very Poor)
  - Working days calculation (Monday-Friday only)

- **Attendance Status Logic**
  - Early-in: Clock in before 9:00 AM
  - On-time: Clock in before 9:30 AM
  - Late-entry: Clock in after 9:30 AM
  - Absent: No clock-in recorded

#### 🏢 Department Management Module

- **Full Department CRUD**
  - `GET /v1/departments` - List all departments
  - `GET /v1/departments/{dep_id}` - Get department by ID
  - `POST /v1/departments` - Create new department
  - `PATCH /v1/departments` - Update department (name, color)
  - `DELETE /v1/departments` - Delete department
  - Duplicate department detection (409 Conflict)

- **Department Features**
  - Hex color support for UI visualization
  - Employee count per department
  - Creation timestamp tracking

#### 🔐 Roles Management Module

- **Role Retrieval**
  - `GET /v1/roles` - List all roles (excluding admin)
  - Role-based access control support

### 🔧 Service Integrations

#### 📊 Supabase Integration

- **Database Client Service**
  - Server-side Supabase client for secure database access
  - Complete CRUD operations for all entities
  - Soft delete pattern with `deleted_at` field
  - Foreign key relationship handling

- **Database Tables Supported**
  - `users` - Core user information with Auth0 linkage
  - `employees` - Employee details (RFID, contact, shift, etc.)
  - `interns` - Intern-specific information
  - `departments` - Department configuration
  - `user_roles` - Role assignments with role_name arrays

#### 🔑 Auth0 Integration

- **Auth0 Management API Client**
  - Machine-to-machine authentication with client credentials
  - Automatic token caching and refresh (24-hour tokens)
  - Token refresh 5 minutes before expiration

- **User Lifecycle Operations**
  - `create_user()` - Create user in Auth0 with `canLogin: true`
  - `soft_delete_user()` - Set `canLogin: false` in app_metadata
  - `restore_user()` - Re-enable login capability
  - `hard_delete_user()` - Permanent deletion (with warning)
  - `get_user()` - Retrieve user details from Auth0
  - `update_user()` - Update user metadata

#### 🔍 OpenSearch Integration

- **Attendance Log Queries**
  - SQL plugin queries for attendance data
  - `get_attendance_logs()` - Get logs for a specific date
  - `get_attendance_by_card_id()` - Get logs for specific RFID card
  - `get_attendance_logs_date_range()` - Get logs for date range
  - Index not found handling (returns empty results)

- **Query Features**
  - Basic authentication with Base64 encoding
  - Configurable SSL verification
  - Automatic response parsing to dictionaries

### 🛡️ Error Handling & Validation

- **Custom Exception Handlers**
  - `RequestValidationError` handler for Pydantic validation errors
  - `HTTPStatusError` handler for HTTP client errors
  - Structured JSON error responses

- **Pydantic v2 Validation**
  - Comprehensive request/response schemas
  - Field validation with descriptions
  - Optional fields with defaults
  - Enum support for status values

### 📝 Data Models

#### User Models
- `UserCreate` - Create user with Auth0 credentials
- `UserUpdate` - Partial user update
- `CombinedUserResponse` - Full user with employee/intern/department details
- `UserFilter` - Search and filter parameters
- `UserLoginInfoResponse` - Auth0 login info with roles

#### Attendance Models
- `EmployeeAttendance` - Individual employee attendance record
- `AttendanceSummary` - Daily statistics summary
- `DailyAttendanceResponse` - Complete daily response
- `EmployeeAttendanceReport` - Aggregated report data
- `AttendanceReportResponse` - Full report with summary
- `EmployeeAttendancePeriodResponse` - Period-based attendance
- `DepartmentDistribution` - Chart data per department

#### Department Models
- `DepartmentCreate` - Create department
- `DepartmentUpdate` - Update department
- `DepartmentResponse` - Department with employee count

#### Role Models
- `Role` - Role ID and name

### ⚙️ Configuration & Environment

- **Pydantic Settings Management**
  - Environment variable loading from `.env` file
  - Case-insensitive environment variables
  - Validation aliases for all settings

- **Configuration Options**
  - `APP_HOST` / `APP_PORT` - Server binding (default: localhost:8000)
  - `DEBUG_MODE` - Enable debug mode and Uvicorn reload
  - `LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)
  - `SUPABASE_URL` / `SUPABASE_KEY` - Supabase connection
  - `AUTH0_DOMAIN` / `AUTH0_CLIENT_ID` / `AUTH0_CLIENT_SECRET` - Auth0 credentials
  - `AUTH0_CONNECTION` - Auth0 database connection name
  - `OPENSEARCH_URL` / `OPENSEARCH_USERNAME` / `OPENSEARCH_PASSWORD` - OpenSearch connection
  - `OPENSEARCH_VERIFY_SSL` - SSL verification toggle

### 🐳 Docker Support

- **Production-Ready Dockerfile**
  - Ubuntu-based image with Python 3
  - Poetry installation via official installer
  - Optimized layer caching (dependencies before code)
  - Exposes port 9000 for containerized deployment
  - Uvicorn server with production settings

### 🧹 Code Quality & Development

- **Pre-commit Hooks**
  - Black code formatter (line length: 88)
  - isort import sorting (black profile)
  - Flake8 linting
  - mypy type checking with Pydantic plugin

- **Testing Infrastructure**
  - pytest with async support (pytest-asyncio)
  - pytest-mock for mocking dependencies
  - httpx for async HTTP client testing
  - Unit and integration test structure

- **Logging**
  - Colored logging output with colorlog
  - Configurable log levels
  - Child loggers for component-specific logging

### 📚 Documentation

- **Automatic API Documentation**
  - Swagger UI at `/docs`
  - ReDoc at `/redoc`
  - OpenAPI schema generation

- **Project Documentation**
  - Comprehensive README with setup instructions
  - WARP.md with AI agent guidelines and architecture
  - Code quality and testing guidelines

### 📋 Technical Specifications

#### Dependencies

- **Framework**: FastAPI 0.115.12
- **Validation**: Pydantic 2.11.4 with pydantic-settings
- **Server**: Uvicorn 0.34.2
- **Database**: Supabase Python Client 2.27.0
- **HTTP Client**: httpx 0.28.1
- **Logging**: colorlog 6.9.0

#### Development Dependencies

- **Testing**: pytest 8.3.5, pytest-asyncio 0.26.0, pytest-mock 3.14.0
- **Formatting**: black 25.1.0, isort 6.0.1
- **Linting**: flake8 7.2.0
- **Type Checking**: mypy 1.15.0
- **Git Hooks**: pre-commit 4.2.0

#### Architecture Patterns

- **Layered Architecture**: Clean separation between API, Service, and Data layers
- **Repository Pattern**: Service layer abstracts data access
- **Dependency Injection**: FastAPI's built-in DI system
- **Configuration Management**: Centralized config with environment variables

#### Performance Features

- **Async/Await**: Non-blocking I/O for all database and external API calls
- **Token Caching**: Auth0 tokens cached with automatic refresh
- **Connection Reuse**: Global client instances for Supabase and OpenSearch

### 🔗 Related Documentation

- [README.md](./README.md) - Setup and usage instructions
- [WARP.md](./WARP.md) - AI agent guidelines and architecture documentation

---

**Initial Release**: v0.1.0
**Release Date**: January 9, 2025
**Development Team**: N-Compass TV Development Team

