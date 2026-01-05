from src.services.supabase import supabase_client


def get_all_roles():
    """
    Fetch all roles except admin.
    
    Returns:
        List of role dictionaries excluding the admin role.
    """
    try:
        response = supabase_client.table('roles').select('*').neq('role_name', 'Admin').execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error fetching roles: {str(e)}")

