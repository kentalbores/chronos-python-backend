from datetime import date
from typing import Optional, Dict, Any

from src.services.supabase import supabase_client
from src.models.departments import DepartmentCreate, DepartmentUpdate


def get_all_departments():
    """
    Fetch all departments from the database with employee count.
    """
    try:
        # Get all departments
        response = supabase_client.table('departments').select('*').execute()
        departments = response.data
        
        if not departments:
            return []
        
        # Get employee counts per department
        employees_response = supabase_client.table('employees').select('dep_id', 'can_login').execute()

        # Count employees per department
        employee_counts = {}
        for emp in employees_response.data:
            if emp.get('can_login') is False:
                continue

            dep_id = emp.get('dep_id')
            
            if dep_id:
                employee_counts[dep_id] = employee_counts.get(dep_id, 0) + 1
        
        # Add employee_count to each department
        for dept in departments:
            dept['employee_count'] = employee_counts.get(dept['dep_id'], 0)
        
        return departments
    except Exception as e:
        raise Exception(f"Error fetching departments: {str(e)}")




def get_department_by_id(dep_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch a specific department by ID with employee statistics and employee list.
    
    Returns department info with:
    - stats: employee_count, work_from_home_count, on_leave_count
    - employees: list of employees with user_id, name, type (intern/regular), phone_num, date_hired
    """
    try:
        # Get department basic info
        department_response = supabase_client.table('departments').select('*').eq('dep_id', dep_id).execute()
        if not department_response.data:
            return None
        department = department_response.data[0]
        
        # Get all employees in this department
        employees_response = supabase_client.table('employees').select('*').eq('dep_id', dep_id).execute()
        department_employees = employees_response.data or []
        
        if not department_employees:
            # No employees in this department
            return {
                "dep_id": department['dep_id'],
                "name": department['name'],
                "dep_color": department.get('dep_color'),
                "stats": {
                    "employee_count": 0,
                    "work_from_home_count": 0,
                    "on_leave_count": 0,
                },
                "employees": [],
            }
        
        # Get user IDs for this department's employees
        user_ids = [emp['user_id'] for emp in department_employees]
        
        # Get user details (names) - filter for active users only
        users_response = supabase_client.table('users').select('user_id, first_name, last_name').in_('user_id', user_ids).is_('deleted_at', 'null').execute()
        users_map = {user['user_id']: user for user in users_response.data}
        
        # Get all interns first for optimization (check which employees are interns)
        interns_response = supabase_client.table('interns').select('user_id').execute()
        intern_ids = {intern['user_id'] for intern in interns_response.data} if interns_response.data else set()
        
        # Get current leaves for employees in this department
        today = date.today().isoformat()
        leaves_response = supabase_client.table('leaves').select('user_id, status, start_date, end_date').in_('user_id', user_ids).eq('status', 'approved').execute()
        
        # Count employees currently on leave (today falls within their leave period)
        on_leave_user_ids = set()
        for leave in leaves_response.data or []:
            start_date = leave.get('start_date')
            end_date = leave.get('end_date')
            if start_date and end_date:
                if start_date <= today <= end_date:
                    on_leave_user_ids.add(leave['user_id'])
        
        # Count work from home employees based on shift_type
        work_from_home_count = 0
        employee_count = 0
        employees_list = []
        
        for emp in department_employees:
            user_id = emp['user_id']
            user = users_map.get(user_id)
            
            # Skip if user doesn't exist or is deleted
            if not user:
                continue
            
            employee_count += 1
            
            # Check if working from home (based on shift_type field)
            shift_type = emp.get('shift_type', '').lower() if emp.get('shift_type') else ''
            if 'remote' in shift_type or 'wfh' in shift_type or 'work from home' in shift_type:
                work_from_home_count += 1
            
            # Determine employee type (intern or regular)
            employee_type = "intern" if user_id in intern_ids else "regular"
            
            # Build employee info
            first_name = user.get('first_name', '')
            last_name = user.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            
            employees_list.append({
                "user_id": user_id,
                "name": full_name,
                "type": employee_type,
                "phone_num": emp.get('contact_number'),
                "date_hired": emp.get('date_hired'),
            })
        
        return {
            "dep_id": department['dep_id'],
            "name": department['name'],
            "dep_color": department.get('dep_color'),
            "stats": {
                "employee_count": employee_count,
                "work_from_home_count": work_from_home_count,
                "on_leave_count": len(on_leave_user_ids),
            },
            "employees": employees_list,
        }
    
    except Exception as e:
        raise Exception(f"Error fetching department details: {str(e)}")


def create_department(department_data: DepartmentCreate):
    """
    Create a new department.
    Raises an exception if a department with the same name already exists.
    """
    try:
        # Check if department with same name already exists
        existing = supabase_client.table('departments').select('dep_id').eq('name', department_data.name).execute()
        if existing.data:
            raise ValueError(f"Department with name '{department_data.name}' already exists")
        
        payload = {
            "name": department_data.name,
            "dep_color": department_data.dep_color,
        }
        response = supabase_client.table('departments').insert(payload).execute()
        return response.data[0] if response.data else None
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error creating department: {str(e)}")


def update_department(department_data: DepartmentUpdate):
    """
    Update an existing department.
    """
    try:
        payload = {}
        if department_data.name is not None:
            payload["name"] = department_data.name
        if department_data.dep_color is not None:
            payload["dep_color"] = department_data.dep_color
        
        if not payload:
            return get_department_by_id(department_data.dep_id)
        
        response = supabase_client.table('departments').update(payload).eq('dep_id', department_data.dep_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        raise Exception(f"Error updating department: {str(e)}")


def delete_department(dep_id: int):
    """
    Delete a department by ID.
    """
    try:
        response = supabase_client.table('departments').delete().eq('dep_id', dep_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        raise Exception(f"Error deleting department: {str(e)}")
