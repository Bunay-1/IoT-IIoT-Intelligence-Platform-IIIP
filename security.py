import hashlib
import os
from cryptography.fernet import Fernet

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
    return input_data.replace('<', '<').replace('>', '>')

def hash_pii(data):
    # Hash PII for protection
    return hashlib.sha256(data.encode()).hexdigest()

def check_access(user, resource):
    # Placeholder for zero-trust access control
    # In real implementation, check user permissions
    return True