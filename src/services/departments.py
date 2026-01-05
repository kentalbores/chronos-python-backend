from src.services.supabase import supabase_client
from src.models.departments import DepartmentCreate, DepartmentUpdate


def get_all_departments():
    """
    Fetch all departments from the database.
    """
    try:
        response = supabase_client.table('departments').select('*').execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error fetching departments: {str(e)}")


def get_department_by_id(dep_id: int):
    """
    Fetch a specific department by ID.
    """
    try:
        response = supabase_client.table('departments').select('*').eq('dep_id', dep_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        raise Exception(f"Error fetching department: {str(e)}")


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
