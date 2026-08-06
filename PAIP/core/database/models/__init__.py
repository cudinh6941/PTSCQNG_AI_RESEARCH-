"""
PAIP Core Database — Models Registration.
"""

from core.database.models.agent_history import Agent0ProofreadHistoryModel
from core.database.models.auth import (
    DepartmentModel,
    PermissionModel,
    RoleModel,
    RolePermissionModel,
    UserModel,
    UserRoleModel,
    UserSessionModel,
)
from core.database.models.glossary import GlossaryTermModel
from core.database.models.rules import SystemRuleModel, SystemSettingModel
from core.database.models.telemetry import (
    AuditLogModel,
    DepartmentQuotaModel,
    LLMRequestModel,
)

__all__ = [
    # Glossary
    "GlossaryTermModel",
    # Rules
    "SystemRuleModel",
    "SystemSettingModel",
    # Auth & RBAC
    "DepartmentModel",
    "UserModel",
    "RoleModel",
    "PermissionModel",
    "UserRoleModel",
    "RolePermissionModel",
    "UserSessionModel",
    # Telemetry
    "AuditLogModel",
    "LLMRequestModel",
    "DepartmentQuotaModel",
    # Agent History
    "Agent0ProofreadHistoryModel",
]
