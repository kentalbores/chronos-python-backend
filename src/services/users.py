from typing import Optional
from datetime import date
from src.services.supabase import supabase_client
from src.services.auth0 import auth0_client
from src.models.users import UserCreate, UserUpdate, UserFilter


def _build_combined_user(user: dict, employee: dict, intern: Optional[dict], dep_name: Optional[str]) -> dict:
    """Helper function to build a combined user object."""
    user_id = user['user_id']
    employment_type = "Intern" if intern else "Regular"
    
    combined_user = {}
    
    # Add intern fields first if exists (to match output order)
    if intern:
        combined_user['user_id'] = user_id
        combined_user['university_name'] = intern.get('university_name')
        combined_user['university_advisor_name'] = intern.get('university_advisor_name')
        combined_user['university_advisor_contact_number'] = intern.get('university_advisor_contact_number')
        combined_user['university_address'] = intern.get('university_address')
        combined_user['university_contact_number'] = intern.get('university_contact_number')
        combined_user['university_email'] = intern.get('university_email')
        combined_user['internship_start_date'] = intern.get('internship_start_date')
        combined_user['internship_end_date'] = intern.get('internship_end_date')
        combined_user['hourly_rate'] = intern.get('hourly_rate')
        combined_user['required_hours'] = intern.get('required_hours')
        combined_user['hours_rendered'] = intern.get('hours_rendered')
    else:
        combined_user['created_at'] = user.get('created_at')
        combined_user['first_name'] = user.get('first_name')
        combined_user['last_name'] = user.get('last_name')
        combined_user['user_id'] = user_id
        combined_user['auth0_id'] = user.get('auth0_id')
        combined_user['profile_url'] = user.get('profile_url')
        combined_user['deleted_at'] = user.get('deleted_at')
    
    # Add employee fields
    combined_user['work_status'] = employee.get('work_status')
    combined_user['has_rfid'] = employee.get('has_rfid')
    combined_user['rfid_value'] = employee.get('rfid_value')
    combined_user['email'] = employee.get('email')
    combined_user['contact_number'] = employee.get('contact_number')
    combined_user['birth_date'] = employee.get('birth_date')
    combined_user['emergency_contact_number'] = employee.get('emergency_contact_number')
    combined_user['emergency_contact_person'] = employee.get('emergency_contact_person')
    combined_user['shift_type'] = employee.get('shift_type')
    combined_user['employee_note'] = employee.get('employee_note')
    combined_user['leaves_used'] = employee.get('leaves_used')
    combined_user['date_hired'] = employee.get('date_hired')
    combined_user['address'] = employee.get('address')
    combined_user['remote_days_used'] = employee.get('remote_days_used')
    combined_user['dep_id'] = employee.get('dep_id')
    
    # Add user fields for interns
    if intern:
        combined_user['first_name'] = user.get('first_name')
        combined_user['last_name'] = user.get('last_name')
        combined_user['profile_url'] = user.get('profile_url')
        combined_user['dep_name'] = dep_name
        combined_user['employment_type'] = employment_type
        combined_user['auth0_id'] = user.get('auth0_id')
    else:
        combined_user['dep_name'] = dep_name
        combined_user['employment_type'] = employment_type
    
    return combined_user


def get_all_users(filters: Optional[UserFilter] = None):
    """
    Fetch all active users with their employee, intern, and department details.
    Supports filtering and searching.
    Filters out soft-deleted users (those with deleted_at values).
    
    Args:
        filters: Optional UserFilter object with search/filter criteria
    """
    try:
        # Get all users that are NOT soft-deleted (deleted_at is null)
        users_response = supabase_client.table('users').select('*').is_('deleted_at', 'null').execute()
        users = users_response.data
        
        if not users:
            return []
        
        # Get all employees
        employees_response = supabase_client.table('employees').select('*').execute()
        employees = {emp['user_id']: emp for emp in employees_response.data}
        
        # Get all interns
        interns_response = supabase_client.table('interns').select('*').execute()
        interns = {intern['user_id']: intern for intern in interns_response.data}
        
        # Get all departments
        departments_response = supabase_client.table('departments').select('*').execute()
        departments = {dep['dep_id']: dep for dep in departments_response.data}
        
        # Combine and filter data
        combined_users = []
        for user in users:
            user_id = user['user_id']
            employee = employees.get(user_id, {})
            intern = interns.get(user_id)
            
            # Get department name
            dep_id = employee.get('dep_id')
            dep_name = departments.get(dep_id, {}).get('name') if dep_id else None
            
            # Determine employment type
            employment_type = "Intern" if intern else "Regular"
            
            # Apply filters if provided
            if filters:
                # Filter by employment_type
                if filters.employment_type and employment_type != filters.employment_type:
                    continue
                
                # Filter by department
                if filters.dep_id is not None and employee.get('dep_id') != filters.dep_id:
                    continue
                
                # Filter by work_status
                if filters.work_status and employee.get('work_status') != filters.work_status:
                    continue
                
                # Filter by shift_type
                if filters.shift_type and employee.get('shift_type') != filters.shift_type:
                    continue
                
                # Filter by has_rfid
                if filters.has_rfid is not None and employee.get('has_rfid') != filters.has_rfid:
                    continue
                
                # Filter by date_hired range
                date_hired = employee.get('date_hired')
                if date_hired:
                    if filters.date_hired_from and date_hired < str(filters.date_hired_from):
                        continue
                    if filters.date_hired_to and date_hired > str(filters.date_hired_to):
                        continue
                elif filters.date_hired_from or filters.date_hired_to:
                    # Skip users without date_hired if filtering by date
                    continue
                
                # Search by name or email (partial match, case-insensitive)
                if filters.search:
                    search_lower = filters.search.lower()
                    first_name = (user.get('first_name') or '').lower()
                    last_name = (user.get('last_name') or '').lower()
                    email = (employee.get('email') or '').lower()
                    full_name = f"{first_name} {last_name}"
                    
                    if not (
                        search_lower in first_name or
                        search_lower in last_name or
                        search_lower in full_name or
                        search_lower in email
                    ):
                        continue
            
            # Build combined user object
            combined_user = _build_combined_user(user, employee, intern, dep_name)
            combined_users.append(combined_user)
        
        # Apply pagination if filters provided
        if filters:
            offset = filters.offset or 0
            limit = filters.limit or 100
            combined_users = combined_users[offset:offset + limit]
        
        return combined_users
    except Exception as e:
        raise Exception(f"Error fetching users: {str(e)}")


def get_user_by_id(user_id: str, include_deleted: bool = False):
    """
    Fetch a specific user by UUID with employee, intern, and department details.
    By default, excludes soft-deleted users.
    
    Args:
        user_id: The user's UUID
        include_deleted: If True, returns user even if soft-deleted
    """
    try:
        # Get user
        query = supabase_client.table('users').select('*').eq('user_id', user_id)
        if not include_deleted:
            query = query.is_('deleted_at', 'null')
        user_response = query.execute()
        
        if not user_response.data:
            return None
        
        user = user_response.data[0]
        
        # Get employee details
        employee_response = supabase_client.table('employees').select('*').eq('user_id', user_id).execute()
        employee = employee_response.data[0] if employee_response.data else {}
        
        # Get intern details
        intern_response = supabase_client.table('interns').select('*').eq('user_id', user_id).execute()
        intern = intern_response.data[0] if intern_response.data else None
        
        # Get department name
        dep_id = employee.get('dep_id')
        dep_name = None
        if dep_id:
            dep_response = supabase_client.table('departments').select('name').eq('dep_id', dep_id).execute()
            if dep_response.data:
                dep_name = dep_response.data[0].get('name')
        
        # Determine employment type
        employment_type = "Intern" if intern else "Regular"
        
        # Build combined response
        combined_user = {}
        
        if intern:
            combined_user['user_id'] = user_id
            combined_user['university_name'] = intern.get('university_name')
            combined_user['university_advisor_name'] = intern.get('university_advisor_name')
            combined_user['university_advisor_contact_number'] = intern.get('university_advisor_contact_number')
            combined_user['university_address'] = intern.get('university_address')
            combined_user['university_contact_number'] = intern.get('university_contact_number')
            combined_user['university_email'] = intern.get('university_email')
            combined_user['internship_start_date'] = intern.get('internship_start_date')
            combined_user['internship_end_date'] = intern.get('internship_end_date')
            combined_user['hourly_rate'] = intern.get('hourly_rate')
            combined_user['required_hours'] = intern.get('required_hours')
            combined_user['hours_rendered'] = intern.get('hours_rendered')
        else:
            combined_user['created_at'] = user.get('created_at')
            combined_user['first_name'] = user.get('first_name')
            combined_user['last_name'] = user.get('last_name')
            combined_user['user_id'] = user_id
            combined_user['auth0_id'] = user.get('auth0_id')
            combined_user['profile_url'] = user.get('profile_url')
            combined_user['deleted_at'] = user.get('deleted_at')
        
        # Add employee fields
        combined_user['work_status'] = employee.get('work_status')
        combined_user['has_rfid'] = employee.get('has_rfid')
        combined_user['rfid_value'] = employee.get('rfid_value')
        combined_user['email'] = employee.get('email')
        combined_user['contact_number'] = employee.get('contact_number')
        combined_user['birth_date'] = employee.get('birth_date')
        combined_user['emergency_contact_number'] = employee.get('emergency_contact_number')
        combined_user['emergency_contact_person'] = employee.get('emergency_contact_person')
        combined_user['shift_type'] = employee.get('shift_type')
        combined_user['employee_note'] = employee.get('employee_note')
        combined_user['leaves_used'] = employee.get('leaves_used')
        combined_user['date_hired'] = employee.get('date_hired')
        combined_user['address'] = employee.get('address')
        combined_user['remote_days_used'] = employee.get('remote_days_used')
        combined_user['dep_id'] = employee.get('dep_id')
        
        # Add remaining fields
        if intern:
            combined_user['first_name'] = user.get('first_name')
            combined_user['last_name'] = user.get('last_name')
            combined_user['profile_url'] = user.get('profile_url')
            combined_user['dep_name'] = dep_name
            combined_user['employment_type'] = employment_type
            combined_user['auth0_id'] = user.get('auth0_id')
        else:
            combined_user['employment_type'] = employment_type
        
        return combined_user
    except Exception as e:
        raise Exception(f"Error fetching user: {str(e)}")


async def create_user(user_data: UserCreate):
    """
    Create a new user in Auth0 and Supabase with associated employee record.
    
    Flow:
    1. Create user in Auth0 (gets auth0_id and profile_url)
    2. Create user in Supabase users table
    3. Create employee record in Supabase employees table
    """
    try:
        # Step 1: Create user in Auth0
        auth0_user = await auth0_client.create_user(
            email=user_data.email,
            password=user_data.password
        )
        
        auth0_id = auth0_user.get('user_id')  # e.g., "auth0|abc123"
        profile_url = user_data.profile_url or auth0_user.get('picture')
        
        # Step 2: Create user record in Supabase
        user_payload = {
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "auth0_id": auth0_id,
            "profile_url": profile_url,
        }
        user_response = supabase_client.table('users').insert(user_payload).execute()
        
        if not user_response.data:
            # Rollback: Delete Auth0 user if Supabase insert fails
            await auth0_client.hard_delete_user(auth0_id)
            raise Exception("Failed to create user in database")
        
        new_user = user_response.data[0]
        user_id = new_user['user_id']
        
        # Step 3: Create employee record
        employee_payload = {
            "user_id": user_id,
            "email": user_data.email,
            "work_status": user_data.work_status,
            "has_rfid": user_data.has_rfid,
            "rfid_value": user_data.rfid_value,
            "contact_number": user_data.contact_number,
            "birth_date": str(user_data.birth_date) if user_data.birth_date else None,
            "emergency_contact_number": user_data.emergency_contact_number,
            "emergency_contact_person": user_data.emergency_contact_person,
            "shift_type": user_data.shift_type,
            "employee_note": user_data.employee_note,
            "date_hired": str(user_data.date_hired) if user_data.date_hired else None,
            "address": user_data.address,
            "dep_id": user_data.dep_id,
            "leaves_used": user_data.leaves_used,
            "remote_days_used": user_data.remote_days_used,
        }
        employee_response = supabase_client.table('employees').insert(employee_payload).execute()
        
        # Build response
        result = {
            **new_user,
            "auth0_id": auth0_id,
        }
        if employee_response.data:
            result['employee'] = employee_response.data[0]
        
        return result
    except Exception as e:
        raise Exception(f"Error creating user: {str(e)}")


def update_user(user_id: str, user_data: UserUpdate):
    """
    Update an existing user and their employee record.
    """
    try:
        # Build user update payload (only include non-None fields)
        user_payload = {}
        if user_data.first_name is not None:
            user_payload["first_name"] = user_data.first_name
        if user_data.last_name is not None:
            user_payload["last_name"] = user_data.last_name
        if user_data.profile_url is not None:
            user_payload["profile_url"] = user_data.profile_url
        
        # Update user if there are fields to update
        if user_payload:
            user_response = supabase_client.table('users').update(user_payload).eq('user_id', user_id).execute()
            if not user_response.data:
                return None
        
        # Build employee update payload
        employee_payload = {}
        if user_data.email is not None:
            employee_payload["email"] = user_data.email
        if user_data.work_status is not None:
            employee_payload["work_status"] = user_data.work_status
        if user_data.has_rfid is not None:
            employee_payload["has_rfid"] = user_data.has_rfid
        if user_data.rfid_value is not None:
            employee_payload["rfid_value"] = user_data.rfid_value
        if user_data.contact_number is not None:
            employee_payload["contact_number"] = user_data.contact_number
        if user_data.birth_date is not None:
            employee_payload["birth_date"] = str(user_data.birth_date)
        if user_data.emergency_contact_number is not None:
            employee_payload["emergency_contact_number"] = user_data.emergency_contact_number
        if user_data.emergency_contact_person is not None:
            employee_payload["emergency_contact_person"] = user_data.emergency_contact_person
        if user_data.shift_type is not None:
            employee_payload["shift_type"] = user_data.shift_type
        if user_data.employee_note is not None:
            employee_payload["employee_note"] = user_data.employee_note
        if user_data.date_hired is not None:
            employee_payload["date_hired"] = str(user_data.date_hired)
        if user_data.address is not None:
            employee_payload["address"] = user_data.address
        if user_data.dep_id is not None:
            employee_payload["dep_id"] = user_data.dep_id
        if user_data.leaves_used is not None:
            employee_payload["leaves_used"] = user_data.leaves_used
        if user_data.remote_days_used is not None:
            employee_payload["remote_days_used"] = user_data.remote_days_used
        
        # Update employee if there are fields to update
        if employee_payload:
            supabase_client.table('employees').update(employee_payload).eq('user_id', user_id).execute()
        
        # Return updated user with all details
        return get_user_by_id(user_id)
    except Exception as e:
        raise Exception(f"Error updating user: {str(e)}")


async def soft_delete_user(user_id: str):
    """
    Soft delete a user:
    1. Set deleted_at in Supabase users table
    2. Set canLogin: false in Auth0
    
    This does NOT permanently delete the user.
    """
    try:
        # Get the user to find auth0_id
        user_response = supabase_client.table('users').select('auth0_id').eq('user_id', user_id).execute()
        if not user_response.data:
            return None
        
        auth0_id = user_response.data[0].get('auth0_id')
        
        # Step 1: Set deleted_at in Supabase
        today = str(date.today())
        update_response = supabase_client.table('users').update({
            "deleted_at": today
        }).eq('user_id', user_id).execute()
        
        if not update_response.data:
            return None
        
        # Step 2: Set canLogin: false in Auth0
        if auth0_id:
            await auth0_client.soft_delete_user(auth0_id)
        
        return update_response.data[0]
    except Exception as e:
        raise Exception(f"Error soft deleting user: {str(e)}")


async def restore_user(user_id: str):
    """
    Restore a soft-deleted user:
    1. Clear deleted_at in Supabase
    2. Set canLogin: true in Auth0
    """
    try:
        # Get the user to find auth0_id
        user_response = supabase_client.table('users').select('auth0_id').eq('user_id', user_id).execute()
        if not user_response.data:
            return None
        
        auth0_id = user_response.data[0].get('auth0_id')
        
        # Step 1: Clear deleted_at in Supabase
        update_response = supabase_client.table('users').update({
            "deleted_at": None
        }).eq('user_id', user_id).execute()
        
        if not update_response.data:
            return None
        
        # Step 2: Set canLogin: true in Auth0
        if auth0_id:
            await auth0_client.restore_user(auth0_id)
        
        return get_user_by_id(user_id, include_deleted=True)
    except Exception as e:
        raise Exception(f"Error restoring user: {str(e)}")


def delete_user(user_id: str):
    """
    DEPRECATED: Use soft_delete_user instead.
    This function performs a hard delete for backwards compatibility.
    """
    try:
        # Delete intern record first if exists
        supabase_client.table('interns').delete().eq('user_id', user_id).execute()
        
        # Delete employee record (due to foreign key)
        supabase_client.table('employees').delete().eq('user_id', user_id).execute()
        
        # Delete user record
        response = supabase_client.table('users').delete().eq('user_id', user_id).execute()
        
        return response.data[0] if response.data else None
    except Exception as e:
        raise Exception(f"Error deleting user: {str(e)}")
