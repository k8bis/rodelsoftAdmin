from typing import Optional
from pydantic import BaseModel, Field


class InternalAdminClientItem(BaseModel):
    client_id: int
    client_name: str
    status: str | None = None


class InternalAdminUserByClientItem(BaseModel):
    user_id: int
    username: str
    email: str | None = None
    membership_status: str | None = None


class InternalAdminSubscriptionByClientItem(BaseModel):
    subscription_id: int
    app_id: int
    app_name: str
    status: str | None = None
    is_enabled: bool
    start_date: str | None = None
    end_date: str | None = None


class InternalAdminPermissionByClientItem(BaseModel):
    permission_id: int
    user_id: int
    username: str
    app_id: int
    app_name: str
    client_id: int
    client_name: str
    role: str | None = None


class InternalAdminGlobalUserItem(BaseModel):
    user_id: int
    username: str
    email: str | None = None
    is_system_admin: bool
    clients_count: int
    permissions_count: int


class InternalAdminGlobalApplicationItem(BaseModel):
    app_id: int
    app_name: str
    slug: str | None = None
    description: str | None = None
    internal_url: str | None = None
    public_url: str | None = None
    entry_path: str | None = None
    health_path: str | None = None
    launch_mode: str | None = None
    is_enabled: bool = True
    clients_count: int
    permissions_count: int


class InternalAdminGlobalClientItem(BaseModel):
    client_id: int
    client_name: str
    active_memberships: int
    subscriptions_count: int
    active_subscriptions_count: int


class InternalAdminCreateUserRequest(BaseModel):
    username: str
    password: str
    email: str | None = None
    is_system_admin: bool = False


class InternalAdminCreateClientRequest(BaseModel):
    client_name: str


class InternalAdminUpsertSubscriptionRequest(BaseModel):
    client_id: int
    app_id: int
    status: str = "active"
    is_enabled: bool = True
    start_date: str | None = None
    end_date: str | None = None


class AdminUpdateClientPayload(BaseModel):
    client_id: int = Field(..., gt=0)
    client_name: str = Field(..., min_length=1, max_length=255)


class AdminUpdateSubscriptionPayload(BaseModel):
    client_id: int = Field(..., gt=0)
    app_id: int = Field(..., gt=0)
    status: str = Field(..., min_length=1, max_length=50)
    is_enabled: bool = True
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class AdminUpdatePermissionRolePayload(BaseModel):
    permission_id: int = Field(..., gt=0)
    role: str = Field(..., min_length=1, max_length=100)


class AdminUpdateUserPayload(BaseModel):
    user_id: int = Field(..., gt=0)
    username: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = None
    is_system_admin: bool = False


class AdminCreateApplicationPayload(BaseModel):
    app_name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = None
    internal_url: str = Field(..., min_length=1, max_length=500)
    public_url: str = Field(..., min_length=1, max_length=500)
    entry_path: Optional[str] = None
    health_path: Optional[str] = None
    launch_mode: Optional[str] = None
    description: Optional[str] = None
    is_enabled: bool = True


class AdminUpdateApplicationPayload(BaseModel):
    app_id: int = Field(..., gt=0)
    app_name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = None
    internal_url: str = Field(..., min_length=1, max_length=500)
    public_url: str = Field(..., min_length=1, max_length=500)
    entry_path: Optional[str] = None
    health_path: Optional[str] = None
    launch_mode: Optional[str] = None
    description: Optional[str] = None
    is_enabled: bool = True


class AdminCreatePermissionPayload(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    client_id: int = Field(..., gt=0)
    app_id: int = Field(..., gt=0)
    role: str = Field(..., min_length=1, max_length=100)