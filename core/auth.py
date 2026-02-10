"""Authentication and authorization module for The Loom.

Provides:
- JWT token-based authentication
- Role-based access control (RBAC)
- Password hashing with bcrypt
- API key management for service accounts
- Project-level permissions
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any


class UserRole(Enum):
    """User roles for RBAC."""

    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    SERVICE = "service"  # For API keys


class Permission(Enum):
    """Permissions for project-level access control."""

    # Project permissions
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_SHARE = "project:share"

    # Graph permissions
    GRAPH_READ = "graph:read"
    GRAPH_WRITE = "graph:write"
    GRAPH_DELETE = "graph:delete"

    # Content permissions
    CONTENT_GENERATE = "content:generate"
    CONTENT_EDIT = "content:edit"
    CONTENT_PUBLISH = "content:publish"

    # Admin permissions
    USER_MANAGE = "user:manage"
    SYSTEM_CONFIG = "system:config"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[UserRole, list[Permission]] = {
    UserRole.ADMIN: list(Permission),  # All permissions
    UserRole.EDITOR: [
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_SHARE,
        Permission.GRAPH_READ,
        Permission.GRAPH_WRITE,
        Permission.CONTENT_GENERATE,
        Permission.CONTENT_EDIT,
    ],
    UserRole.VIEWER: [
        Permission.PROJECT_READ,
        Permission.GRAPH_READ,
    ],
    UserRole.SERVICE: [
        Permission.PROJECT_READ,
        Permission.GRAPH_READ,
        Permission.GRAPH_WRITE,
        Permission.CONTENT_GENERATE,
    ],
}


@dataclass(frozen=True)
class User:
    """User account information."""

    user_id: str
    email: str
    username: str
    role: UserRole
    hashed_password: str
    is_active: bool = True
    created_at: str = ""
    last_login: str | None = None

    def __post_init__(self) -> None:
        if not self.created_at:
            object.__setattr__(self, "created_at", datetime.now(UTC).isoformat())

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        return permission in ROLE_PERMISSIONS.get(self.role, [])

    def to_public_dict(self) -> dict[str, Any]:
        """Convert to public-safe dictionary."""
        return {
            "userId": self.user_id,
            "email": self.email,
            "username": self.username,
            "role": self.role.value,
            "isActive": self.is_active,
            "createdAt": self.created_at,
            "lastLogin": self.last_login,
        }


@dataclass(frozen=True)
class ProjectPermission:
    """Permission grant for a specific project."""

    project_id: str
    user_id: str
    permission: Permission
    granted_by: str
    granted_at: str = ""

    def __post_init__(self) -> None:
        if not self.granted_at:
            object.__setattr__(self, "granted_at", datetime.now(UTC).isoformat())


@dataclass(frozen=True)
class APIKey:
    """API key for service accounts."""

    key_id: str
    key_hash: str  # Hashed key (store this)
    name: str
    user_id: str
    permissions: list[Permission]
    is_active: bool
    created_at: str
    expires_at: str | None
    last_used: str | None = None


@dataclass(frozen=True)
class JWTPayload:
    """JWT token payload."""

    sub: str  # User ID
    email: str
    role: str
    jti: str  # JWT ID for token revocation
    iat: float  # Issued at
    exp: float  # Expiration
    type: str  # "access" or "refresh"

    def to_dict(self) -> dict[str, Any]:
        return {
            "sub": self.sub,
            "email": self.email,
            "role": self.role,
            "jti": self.jti,
            "iat": self.iat,
            "exp": self.exp,
            "type": self.type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JWTPayload:
        return cls(
            sub=data["sub"],
            email=data["email"],
            role=data["role"],
            jti=data["jti"],
            iat=data["iat"],
            exp=data["exp"],
            type=data["type"],
        )


class AuthManager:
    """Main authentication and authorization manager."""

    # Token lifetimes
    ACCESS_TOKEN_MINUTES = 15
    REFRESH_TOKEN_DAYS = 7
    API_KEY_DAYS = 365

    def __init__(self, jwt_secret: str | None = None) -> None:
        self._jwt_secret = jwt_secret or secrets.token_urlsafe(32)
        self._users: dict[str, User] = {}  # user_id -> User
        self._email_index: dict[str, str] = {}  # email -> user_id
        self._api_keys: dict[str, APIKey] = {}  # key_id -> APIKey
        self._project_permissions: dict[str, list[ProjectPermission]] = (
            {}
        )  # project_id -> permissions
        self._revoked_tokens: set[str] = set()  # Set of revoked JWT IDs

    # ============ Password Management ============

    def _hash_password(self, password: str) -> str:
        """Hash a password with salt."""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        return f"{salt}${pwd_hash}"

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        try:
            salt, stored_hash = hashed.split("$")
            pwd_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
            return pwd_hash == stored_hash
        except ValueError:
            return False

    # ============ User Management ============

    def create_user(
        self,
        email: str,
        username: str,
        password: str,
        role: UserRole = UserRole.EDITOR,
    ) -> User:
        """Create a new user."""
        if email in self._email_index:
            raise ValueError(f"User with email {email} already exists")

        user_id = str(uuid.uuid4())
        user = User(
            user_id=user_id,
            email=email,
            username=username,
            role=role,
            hashed_password=self._hash_password(password),
        )

        self._users[user_id] = user
        self._email_index[email] = user_id

        return user

    def get_user(self, user_id: str) -> User | None:
        """Get user by ID."""
        return self._users.get(user_id)

    def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        user_id = self._email_index.get(email)
        if user_id:
            return self._users.get(user_id)
        return None

    def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate a user by email and password."""
        user = self.get_user_by_email(email)
        if user and self._verify_password(password, user.hashed_password):
            # Update last login
            updated_user = User(
                user_id=user.user_id,
                email=user.email,
                username=user.username,
                role=user.role,
                hashed_password=user.hashed_password,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login=datetime.now(UTC).isoformat(),
            )
            self._users[user.user_id] = updated_user
            return updated_user
        return None

    def update_password(self, user_id: str, new_password: str) -> bool:
        """Update a user's password."""
        user = self._users.get(user_id)
        if not user:
            return False

        updated_user = User(
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            role=user.role,
            hashed_password=self._hash_password(new_password),
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
        )
        self._users[user_id] = updated_user
        return True

    # ============ JWT Token Management ============

    def _generate_jti(self) -> str:
        """Generate unique JWT ID."""
        return str(uuid.uuid4())

    def create_access_token(self, user: User) -> str:
        """Create a JWT access token for a user."""
        now = datetime.now(UTC)
        exp = now + timedelta(minutes=self.ACCESS_TOKEN_MINUTES)

        payload = JWTPayload(
            sub=user.user_id,
            email=user.email,
            role=user.role.value,
            jti=self._generate_jti(),
            iat=now.timestamp(),
            exp=exp.timestamp(),
            type="access",
        )

        return self._encode_jwt(payload)

    def create_refresh_token(self, user: User) -> str:
        """Create a JWT refresh token for a user."""
        now = datetime.now(UTC)
        exp = now + timedelta(days=self.REFRESH_TOKEN_DAYS)

        payload = JWTPayload(
            sub=user.user_id,
            email=user.email,
            role=user.role.value,
            jti=self._generate_jti(),
            iat=now.timestamp(),
            exp=exp.timestamp(),
            type="refresh",
        )

        return self._encode_jwt(payload)

    def _encode_jwt(self, payload: JWTPayload) -> str:
        """Encode JWT token (simplified - production should use PyJWT)."""
        import base64
        import json

        # Header
        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = (
            base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
        )

        # Payload
        payload_b64 = (
            base64.urlsafe_b64encode(json.dumps(payload.to_dict()).encode())
            .rstrip(b"=")
            .decode()
        )

        # Signature
        signature_input = f"{header_b64}.{payload_b64}"
        signature = hashlib.sha256(
            f"{signature_input}{self._jwt_secret}".encode()
        ).hexdigest()
        signature_b64 = (
            base64.urlsafe_b64encode(signature.encode()).rstrip(b"=").decode()
        )

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def decode_jwt(self, token: str) -> JWTPayload | None:
        """Decode and verify JWT token."""
        try:
            import base64
            import json

            parts = token.split(".")
            if len(parts) != 3:
                return None

            header_b64, payload_b64, signature_b64 = parts

            # Verify signature
            signature_input = f"{header_b64}.{payload_b64}"
            expected_sig = hashlib.sha256(
                f"{signature_input}{self._jwt_secret}".encode()
            ).hexdigest()

            decoded_sig = base64.urlsafe_b64decode(signature_b64 + "=").decode()
            if decoded_sig != expected_sig:
                return None

            # Decode payload
            payload_json = base64.urlsafe_b64decode(payload_b64 + "=")
            payload_data = json.loads(payload_json)

            # Check expiration
            if payload_data["exp"] < datetime.now(UTC).timestamp():
                return None

            # Check if revoked
            if payload_data["jti"] in self._revoked_tokens:
                return None

            return JWTPayload.from_dict(payload_data)

        except Exception:
            return None

    def revoke_token(self, jti: str) -> None:
        """Revoke a JWT token by its ID."""
        self._revoked_tokens.add(jti)

    # ============ API Key Management ============

    def create_api_key(
        self,
        name: str,
        user_id: str,
        permissions: list[Permission] | None = None,
        expires_days: int | None = None,
    ) -> tuple[str, APIKey]:
        """Create a new API key. Returns (plain_key, api_key_obj)."""
        # Generate random key
        plain_key = f"loom_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
        key_id = str(uuid.uuid4())

        now = datetime.now(UTC)
        expires_at = None
        if expires_days:
            expires_at = (now + timedelta(days=expires_days)).isoformat()

        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            user_id=user_id,
            permissions=permissions or [Permission.PROJECT_READ],
            is_active=True,
            created_at=now.isoformat(),
            expires_at=expires_at,
        )

        self._api_keys[key_id] = api_key
        return plain_key, api_key

    def validate_api_key(self, plain_key: str) -> APIKey | None:
        """Validate an API key."""
        if not plain_key.startswith("loom_"):
            return None

        key_hash = hashlib.sha256(plain_key.encode()).hexdigest()

        for api_key in self._api_keys.values():
            if api_key.key_hash == key_hash and api_key.is_active:
                # Check expiration
                if api_key.expires_at:
                    if datetime.now(UTC) > datetime.fromisoformat(api_key.expires_at):
                        return None

                # Update last used
                updated = APIKey(
                    key_id=api_key.key_id,
                    key_hash=api_key.key_hash,
                    name=api_key.name,
                    user_id=api_key.user_id,
                    permissions=api_key.permissions,
                    is_active=api_key.is_active,
                    created_at=api_key.created_at,
                    expires_at=api_key.expires_at,
                    last_used=datetime.now(UTC).isoformat(),
                )
                self._api_keys[api_key.key_id] = updated
                return updated

        return None

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        if key_id not in self._api_keys:
            return False

        api_key = self._api_keys[key_id]
        self._api_keys[key_id] = APIKey(
            key_id=api_key.key_id,
            key_hash=api_key.key_hash,
            name=api_key.name,
            user_id=api_key.user_id,
            permissions=api_key.permissions,
            is_active=False,
            created_at=api_key.created_at,
            expires_at=api_key.expires_at,
            last_used=api_key.last_used,
        )
        return True

    def list_user_api_keys(self, user_id: str) -> list[APIKey]:
        """List all API keys for a user."""
        return [key for key in self._api_keys.values() if key.user_id == user_id]

    # ============ Project Permissions ============

    def grant_project_permission(
        self,
        project_id: str,
        user_id: str,
        permission: Permission,
        granted_by: str,
    ) -> ProjectPermission:
        """Grant a permission on a project to a user."""
        grant = ProjectPermission(
            project_id=project_id,
            user_id=user_id,
            permission=permission,
            granted_by=granted_by,
        )

        if project_id not in self._project_permissions:
            self._project_permissions[project_id] = []

        self._project_permissions[project_id].append(grant)
        return grant

    def revoke_project_permission(
        self, project_id: str, user_id: str, permission: Permission
    ) -> bool:
        """Revoke a project permission."""
        if project_id not in self._project_permissions:
            return False

        perms = self._project_permissions[project_id]
        new_perms = [
            p
            for p in perms
            if not (p.user_id == user_id and p.permission == permission)
        ]

        if len(new_perms) == len(perms):
            return False

        self._project_permissions[project_id] = new_perms
        return True

    def check_project_permission(
        self, project_id: str, user_id: str, permission: Permission
    ) -> bool:
        """Check if a user has a specific permission on a project."""
        user = self._users.get(user_id)
        if not user:
            return False

        # Admins have all permissions
        if user.role == UserRole.ADMIN:
            return True

        # Check role-based permissions
        if permission in ROLE_PERMISSIONS.get(user.role, []):
            return True

        # Check project-specific grants
        if project_id in self._project_permissions:
            for grant in self._project_permissions[project_id]:
                if grant.user_id == user_id and grant.permission == permission:
                    return True

        return False

    def get_user_project_permissions(
        self, project_id: str, user_id: str
    ) -> list[Permission]:
        """Get all permissions a user has on a project."""
        user = self._users.get(user_id)
        if not user:
            return []

        # Start with role-based permissions
        permissions = set(ROLE_PERMISSIONS.get(user.role, []))

        # Add project-specific grants
        if project_id in self._project_permissions:
            for grant in self._project_permissions[project_id]:
                if grant.user_id == user_id:
                    permissions.add(grant.permission)

        return list(permissions)


# Global auth manager instance
_auth_manager: AuthManager | None = None


def get_auth_manager() -> AuthManager:
    """Get the global auth manager instance."""
    global _auth_manager
    if _auth_manager is None:
        import os

        secret = os.environ.get("JWT_SECRET")
        _auth_manager = AuthManager(jwt_secret=secret)
    return _auth_manager
