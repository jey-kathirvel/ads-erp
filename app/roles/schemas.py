from pydantic import BaseModel

# ----------------------------------------------------
# Create Role
# ----------------------------------------------------


class RoleCreate(BaseModel):

    role_code: str

    role_name: str

    description: str | None = None

    is_active: bool = True


# ----------------------------------------------------
# Update Role
# ----------------------------------------------------


class RoleUpdate(BaseModel):

    role_code: str

    role_name: str

    description: str | None = None

    is_active: bool = True


# ----------------------------------------------------
# Permission
# ----------------------------------------------------


class PermissionUpdate(BaseModel):

    role_id: int

    module_name: str

    can_view: bool = True

    can_add: bool = False

    can_edit: bool = False

    can_delete: bool = False
