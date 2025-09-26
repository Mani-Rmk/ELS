from fastapi import Depends, HTTPException, status
from core.security import get_current_user
from role_permissions import ROLE_PERMISSIONS

def require_permission(permission: str):
    def dependency(current_user = Depends(get_current_user)):
        role = current_user.role
        allowed_permissions = ROLE_PERMISSIONS.get(role, [])
        if "*" in allowed_permissions or permission in allowed_permissions:
            return True
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{role}' does not have permission '{permission}'"
        )
    return dependency
