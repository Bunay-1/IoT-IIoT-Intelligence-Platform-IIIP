import hashlib
import os
import logging
from cryptography.fernet import Fernet
from typing import Dict, List, Optional, Set

# Configure logger
logger = logging.getLogger(__name__)

# Generate key for encryption
def generate_key():
    return Fernet.generate_key()

def encrypt_data(data, key):
    f = Fernet(key)
    return f.encrypt(data.encode())

def decrypt_data(encrypted_data, key):
    f = Fernet(key)
    return f.decrypt(encrypted_data).decode()

def sanitize_input(input_data):
    # Basic sanitization to prevent XSS
    if not isinstance(input_data, str):
        return input_data
    return input_data.replace('<', '&lt;').replace('>', '&gt;')

def hash_pii(data):
    # Hash PII for protection
    return hashlib.sha256(data.encode()).hexdigest()

class RBACManager:
    """
    Manager for Role-Based Access Control.
    """
    def __init__(self):
        # Initial roles and permissions mapping
        self.roles_permissions: Dict[str, Set[str]] = {
            "admin": {"read", "write", "delete", "admin_access"},
            "operator": {"read", "write"},
            "viewer": {"read"},
            "security_officer": {"read", "audit"}
        }
        # Mock user-role database
        self.user_roles: Dict[str, str] = {
            "admin_user": "admin",
            "op_user": "operator",
            "view_user": "viewer",
            "sec_user": "security_officer"
        }

    def check_access(self, user: str, permission: str) -> bool:
        """
        Check if a user has a specific permission based on their role.
        """
        role = self.user_roles.get(user)
        if not role:
            logger.warning(f"Access denied: User '{user}' not found.")
            return False

        permissions = self.roles_permissions.get(role, set())
        if permission in permissions:
            logger.info(f"Access granted: User '{user}' (role: {role}) for permission '{permission}'.")
            return True

        logger.warning(f"Access denied: User '{user}' (role: {role}) lacks permission '{permission}'.")
        return False

# Global instance for easy access
rbac = RBACManager()

def check_access(user, resource_permission):
    """
    Global helper function for access control.
    In a zero-trust model, every access request is verified.
    """
    return rbac.check_access(user, resource_permission)

if __name__ == "__main__":
    # Quick test
    print(f"Admin read access: {check_access('admin_user', 'read')}")
    print(f"Viewer write access: {check_access('view_user', 'write')}")
    print(f"Unknown user access: {check_access('guest', 'read')}")
