from typing import Optional, List, Dict, Any
from datetime import datetime
from src.services.supabase import supabase_client
from src.models.leaves import LeaveRequestCreate, LeaveRequestUpdate, LeaveRequestFilter


def _enrich_leave_requests(leaves: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrich leave requests with user and department details.
    """
    if not leaves:
        return []
        
    user_ids = list(set(leave['user_id'] for leave in leaves if leave.get('user_id')))
    
    if not user_ids:
        return leaves

    # Fetch users associated with these leaves
    users_response = supabase_client.table('users').select('user_id, first_name, last_name, profile_url').in_('user_id', user_ids).execute()
    users_map = {u['user_id']: u for u in users_response.data}
    
    # Fetch employees to get department IDs
    employees_response = supabase_client.table('employees').select('user_id, dep_id').in_('user_id', user_ids).execute()
    employees_map = {e['user_id']: e for e in employees_response.data}
    
    # Collect department IDs
    dep_ids = list(set(e['dep_id'] for e in employees_map.values() if e.get('dep_id')))
    
    # Fetch departments
    departments_map = {}
    if dep_ids:
        departments_response = supabase_client.table('departments').select('dep_id, name').in_('dep_id', dep_ids).execute()
        departments_map = {d['dep_id']: d['name'] for d in departments_response.data}
        
    # Merge data
    enriched_leaves = []
    for leave in leaves:
        user_id = leave.get('user_id')
        user = users_map.get(user_id, {})
        employee = employees_map.get(user_id, {})
        dep_id = employee.get('dep_id')
        dep_name = departments_map.get(dep_id)
        
        enriched_leave = {
            **leave,
            "first_name": user.get('first_name'),
            "last_name": user.get('last_name'),
            "profile_url": user.get('profile_url'),
            "dep_name": dep_name
        }
        enriched_leaves.append(enriched_leave)
        
    return enriched_leaves


def create_leave_request(leave_data: LeaveRequestCreate) -> Dict[str, Any]:
    """
    Create a new leave request.
    """
    try:
        payload = {
            "user_id": leave_data.user_id,
            "type": leave_data.type,
            "start_date": str(leave_data.start_date),
            "end_date": str(leave_data.end_date),
            "comment": leave_data.comment,
            "attachment_url": leave_data.attachment_url,
            "status": "Pending",
            "approved_by": None
        }
        
        response = supabase_client.table('leaves').insert(payload).execute()
        if not response.data:
            raise Exception("Failed to insert leave request")
            
        new_leave = response.data[0]
        enriched = _enrich_leave_requests([new_leave])
        return enriched[0] if enriched else new_leave
        
    except Exception as e:
        raise Exception(f"Error creating leave request: {str(e)}")


def get_all_leaves(filters: Optional[LeaveRequestFilter] = None) -> List[Dict[str, Any]]:
    """
    Get all leave requests with optional filtering.
    Filters out soft-deleted records by default.
    """
    try:
        query = supabase_client.table('leaves').select('*').is_('deleted_at', 'null').order('created_at', desc=True)
        
        if filters:
            if filters.user_id:
                query = query.eq('user_id', filters.user_id)
            if filters.status:
                query = query.eq('status', filters.status)
            if filters.type:
                query = query.eq('type', filters.type)
            if filters.date_from:
                query = query.gte('start_date', str(filters.date_from))
            if filters.date_to:
                query = query.lte('end_date', str(filters.date_to))
                
            # Pagination
            offset = filters.offset or 0
            limit = filters.limit or 100
            query = query.range(offset, offset + limit - 1)
            
        response = query.execute()
        return _enrich_leave_requests(response.data)
        
    except Exception as e:
        raise Exception(f"Error fetching leave requests: {str(e)}")


def get_leave_by_id(leave_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific leave request by ID.
    Only returns non-deleted leaves.
    """
    try:
        response = supabase_client.table('leaves').select('*').eq('leave_id', leave_id).is_('deleted_at', 'null').execute()
        if not response.data:
            return None
            
        enriched = _enrich_leave_requests(response.data)
        return enriched[0] if enriched else None
        
    except Exception as e:
        raise Exception(f"Error fetching leave request: {str(e)}")


def update_leave_request(leave_id: str, update_data: LeaveRequestUpdate) -> Optional[Dict[str, Any]]:
    """
    Update a leave request (e.g., approve/reject).
    """
    try:
        payload = {}
        if update_data.status:
            payload['status'] = update_data.status
        if update_data.approved_by:
            payload['approved_by'] = update_data.approved_by
            
        payload['updated_at'] = datetime.now().isoformat()
        
        if not payload:
            return get_leave_by_id(leave_id)
            
        response = supabase_client.table('leaves').update(payload).eq('leave_id', leave_id).execute()
        
        if not response.data:
            return None
            
        enriched = _enrich_leave_requests(response.data)
        return enriched[0] if enriched else None
        
    except Exception as e:
        raise Exception(f"Error updating leave request: {str(e)}")


def delete_leave_request(leave_id: str) -> bool:
    """
    Soft delete a leave request.
    """
    try:
        response = supabase_client.table('leaves').update({
            "deleted_at": datetime.now().date().isoformat()
        }).eq('leave_id', leave_id).execute()
        return len(response.data) > 0
    except Exception as e:
        raise Exception(f"Error deleting leave request: {str(e)}")
