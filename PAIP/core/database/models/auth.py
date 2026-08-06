"""
PAIP Core Database — Auth, RBAC & Organization Models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.base import Base, BaseModelMixin, _utcnow


class DepartmentModel(Base, BaseModelMixin):
    """
    Department / Unit hierarchy model within PTSC.
    Mapping table: departments
    """

    __tablename__ = "departments"

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        doc="Department code (e.g. 'P.ATCL', 'P.KTTB', 'P.TM')",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Full department name",
    )

    parent_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        doc="Parent department ID for tree structure",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    users: Mapped[list["UserModel"]] = relationship(
        "UserModel",
        back_populates="department",
    )


class UserModel(Base, BaseModelMixin):
    """
    User account model synchronized from LDAP / Microsoft Entra ID.
    Mapping table: users
    """

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        doc="LDAP sAMAccountName / Username",
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="Company email address (@ptsc.com.vn)",
    )

    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Full user name",
    )

    title: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Job title (Trưởng phòng, Chuyên viên...)",
    )

    department_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Platform super administrator",
    )

    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    department: Mapped[Optional["DepartmentModel"]] = relationship(
        "DepartmentModel",
        back_populates="users",
    )


class RoleModel(Base, BaseModelMixin):
    """
    RBAC Role model.
    Mapping table: roles
    """

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        doc="Role name: ADMIN, DEPT_LEAD, SPECIALIST, VIEWER",
    )

    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="System protected roles that cannot be deleted",
    )


class PermissionModel(Base, BaseModelMixin):
    """
    RBAC Permission model.
    Mapping table: permissions
    """

    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        doc="Permission code (e.g. 'glossary:edit', 'proofread:run')",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    module: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Module area: glossary, proofreader, admin, telemetry",
    )


class UserRoleModel(Base):
    """
    User to Role association table.
    Mapping table: user_roles
    """

    __tablename__ = "user_roles"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )

    assigned_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
    )


class RolePermissionModel(Base):
    """
    Role to Permission association table.
    Mapping table: role_permissions
    """

    __tablename__ = "role_permissions"

    role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )

    permission_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )


class UserSessionModel(Base, BaseModelMixin):
    """
    User active session / refresh token model.
    Mapping table: user_sessions
    """

    __tablename__ = "user_sessions"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    refresh_token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    ip_address: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
