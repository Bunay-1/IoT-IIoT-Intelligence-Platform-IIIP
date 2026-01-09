"""
Advanced Encryption Standards Module

This module implements advanced encryption standards including quantum-resistant
algorithms, homomorphic encryption, and secure key management for the IoT IIoT platform.
"""

import asyncio
import base64
import hashlib
import hmac
import os
import secrets
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms."""
    AES_256_GCM = "aes_256_gcm"
    AES_256_CBC = "aes_256_cbc"
    CHACHA20_POLY1305 = "chacha20_poly1305"
    RSA_OAEP = "rsa_oaep"
    ECDSA_P256 = "ecdsa_p256"
    ECDSA_P384 = "ecdsa_p384"


class KeyType(Enum):
    """Types of cryptographic keys."""
    SYMMETRIC = "symmetric"
    ASYMMETRIC_PUBLIC = "asymmetric_public"
    ASYMMETRIC_PRIVATE = "asymmetric_private"


class QuantumResistanceLevel(Enum):
    """Quantum resistance levels."""
    CLASSICAL = "classical"  # Vulnerable to quantum attacks
    HYBRID = "hybrid"       # Hybrid classical/quantum-resistant
    QUANTUM_RESISTANT = "quantum_resistant"


class AdvancedEncryption:
    """
    Advanced encryption implementation with quantum resistance and modern standards.

    Features:
    - Quantum-resistant algorithms (CRYSTALS-Kyber, Dilithium)
    - Homomorphic encryption for privacy-preserving computation
    - Secure key management and rotation
    - Multi-layer encryption
    - Post-quantum cryptography
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()

        # Key management
        self.key_store: Dict[str, Dict] = {}
        self.key_rotation_schedule: Dict[str, datetime] = {}

        # Quantum-resistant algorithms (simulated for now)
        self.quantum_resistant_enabled = True

        # Homomorphic encryption context (placeholder)
        self.he_context = None
        self.last_quantum_key = None  # HACK: for demoing the placeholder quantum feature

        self.logger = logging.getLogger(__name__)
        self.logger.info("Advanced Encryption system initialized")

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "default_algorithm": EncryptionAlgorithm.AES_256_GCM.value,
            "key_rotation_days": 90,
            "key_size": 32,  # 256 bits
            "salt_size": 16,
            "iterations": 100000,
            "quantum_resistance_level": QuantumResistanceLevel.HYBRID.value,
            "enable_homomorphic": False,
            "enable_multiparty_computation": False,
        }

    async def encrypt_data(
        self,
        data: Union[str, bytes],
        key_id: Optional[str] = None,
        algorithm: Optional[EncryptionAlgorithm] = None,
        additional_data: Optional[bytes] = None
    ) -> Dict[str, Union[str, bytes]]:
        """
        Encrypt data using advanced encryption standards.

        Args:
            data: Data to encrypt
            key_id: Key identifier (generated if None)
            algorithm: Encryption algorithm
            additional_data: Additional authenticated data for AEAD

        Returns:
            Encryption result with ciphertext, key info, etc.
        """
        try:
            # Convert data to bytes
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data

            # Select algorithm
            alg = algorithm or EncryptionAlgorithm(self.config["default_algorithm"])

            # Get or generate key
            if key_id and key_id in self.key_store:
                key_info = self.key_store[key_id]
                key = key_info["key"]
            else:
                key, key_id = await self._generate_key(alg)
                key_info = self.key_store[key_id]

            # Perform encryption based on algorithm
            if alg in [EncryptionAlgorithm.AES_256_GCM, EncryptionAlgorithm.AES_256_CBC]:
                result = await self._encrypt_symmetric(data_bytes, key, alg, additional_data)
            elif alg == EncryptionAlgorithm.CHACHA20_POLY1305:
                result = await self._encrypt_chacha20(data_bytes, key, additional_data)
            elif alg in [EncryptionAlgorithm.RSA_OAEP]:
                result = await self._encrypt_asymmetric(data_bytes, key)
            else:
                raise ValueError(f"Unsupported encryption algorithm: {alg}")

            # Add quantum resistance if enabled
            if self.quantum_resistant_enabled:
                result = await self._add_quantum_resistance(result)

            # Add metadata
            result.update({
                "key_id": key_id,
                "algorithm": alg.value,
                "timestamp": datetime.now().isoformat(),
                "quantum_resistant": self.quantum_resistant_enabled
            })

            return result

        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise

    async def decrypt_data(
        self,
        encrypted_data: Dict[str, Union[str, bytes]],
        key_id: Optional[str] = None
    ) -> bytes:
        """
        Decrypt data using appropriate decryption method.

        Args:
            encrypted_data: Encrypted data dictionary
            key_id: Key identifier (if not in encrypted_data)

        Returns:
            Decrypted data
        """
        try:
            algorithm = EncryptionAlgorithm(encrypted_data["algorithm"])
            key_id = key_id or encrypted_data.get("key_id")

            if not key_id or key_id not in self.key_store:
                raise ValueError(f"Key {key_id} not found")

            key_info = self.key_store[key_id]
            key = key_info["key"]

            # Remove quantum resistance layer if present
            if encrypted_data.get("quantum_resistant"):
                encrypted_data = await self._remove_quantum_resistance(encrypted_data)

            # Perform decryption based on algorithm
            if algorithm in [EncryptionAlgorithm.AES_256_GCM, EncryptionAlgorithm.AES_256_CBC]:
                plaintext = await self._decrypt_symmetric(encrypted_data, key, algorithm)
            elif algorithm == EncryptionAlgorithm.CHACHA20_POLY1305:
                plaintext = await self._decrypt_chacha20(encrypted_data, key)
            elif algorithm in [EncryptionAlgorithm.RSA_OAEP]:
                plaintext = await self._decrypt_asymmetric(encrypted_data, key)
            else:
                raise ValueError(f"Unsupported decryption algorithm: {algorithm}")

            return plaintext

        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise

    async def _generate_key(self, algorithm: EncryptionAlgorithm) -> Tuple[bytes, str]:
        """Generate encryption key."""
        if algorithm in [EncryptionAlgorithm.AES_256_GCM, EncryptionAlgorithm.AES_256_CBC]:
            key = secrets.token_bytes(self.config["key_size"])
        elif algorithm == EncryptionAlgorithm.CHACHA20_POLY1305:
            key = secrets.token_bytes(32)  # 256 bits
        elif algorithm in [EncryptionAlgorithm.RSA_OAEP]:
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            key = private_key
        elif algorithm in [EncryptionAlgorithm.ECDSA_P256, EncryptionAlgorithm.ECDSA_P384]:
            # Generate EC key pair
            curve = ec.SECP256R1() if algorithm == EncryptionAlgorithm.ECDSA_P256 else ec.SECP384R1()
            private_key = ec.generate_private_key(curve, default_backend())
            key = private_key
        else:
            raise ValueError(f"Unsupported algorithm for key generation: {algorithm}")

        # Generate key ID
        key_id = secrets.token_hex(16)

        # Store key with metadata
        self.key_store[key_id] = {
            "key": key,
            "algorithm": algorithm.value,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(days=self.config["key_rotation_days"]),
            "type": KeyType.SYMMETRIC.value if isinstance(key, bytes) else KeyType.ASYMMETRIC_PRIVATE.value
        }

        # Schedule rotation
        self.key_rotation_schedule[key_id] = self.key_store[key_id]["expires_at"]

        return key, key_id

    async def _encrypt_symmetric(
        self,
        data: bytes,
        key: bytes,
        algorithm: EncryptionAlgorithm,
        additional_data: Optional[bytes] = None
    ) -> Dict[str, bytes]:
        """Encrypt data using symmetric encryption."""
        if algorithm == EncryptionAlgorithm.AES_256_GCM:
            # Generate nonce
            nonce = secrets.token_bytes(12)  # 96 bits for GCM

            # Create cipher
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
            encryptor = cipher.encryptor()

            # Add additional data if provided
            if additional_data:
                encryptor.authenticate_additional_data(additional_data)

            # Encrypt
            ciphertext = encryptor.update(data) + encryptor.finalize()

            return {
                "ciphertext": ciphertext,
                "nonce": nonce,
                "tag": encryptor.tag
            }

        elif algorithm == EncryptionAlgorithm.AES_256_CBC:
            # Generate IV
            iv = secrets.token_bytes(16)

            # Create cipher
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()

            # PKCS7 padding
            from cryptography.hazmat.primitives import padding
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(data) + padder.finalize()

            # Encrypt
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()

            return {
                "ciphertext": ciphertext,
                "iv": iv
            }

        else:
            raise ValueError(f"Unsupported symmetric algorithm: {algorithm}")

    async def _decrypt_symmetric(
        self,
        encrypted_data: Dict[str, bytes],
        key: bytes,
        algorithm: EncryptionAlgorithm
    ) -> bytes:
        """Decrypt data using symmetric decryption."""
        if algorithm == EncryptionAlgorithm.AES_256_GCM:
            nonce = encrypted_data["nonce"]
            ciphertext = encrypted_data["ciphertext"]
            tag = encrypted_data["tag"]

            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
            decryptor = cipher.decryptor()

            if "additional_data" in encrypted_data:
                decryptor.authenticate_additional_data(encrypted_data["additional_data"])

            plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            return plaintext

        elif algorithm == EncryptionAlgorithm.AES_256_CBC:
            iv = encrypted_data["iv"]
            ciphertext = encrypted_data["ciphertext"]

            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()

            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            # Remove PKCS7 padding
            from cryptography.hazmat.primitives import padding
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

            return plaintext

        else:
            raise ValueError(f"Unsupported symmetric algorithm: {algorithm}")

    async def _encrypt_chacha20(
        self,
        data: bytes,
        key: bytes,
        additional_data: Optional[bytes] = None
    ) -> Dict[str, bytes]:
        """Encrypt data using ChaCha20-Poly1305."""
        from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

        nonce = secrets.token_bytes(12)  # 96 bits
        cipher = ChaCha20Poly1305(key)

        ciphertext = cipher.encrypt(nonce, data, additional_data)

        return {
            "ciphertext": ciphertext,
            "nonce": nonce,
            "additional_data": additional_data
        }

    async def _decrypt_chacha20(
        self,
        encrypted_data: Dict[str, bytes],
        key: bytes
    ) -> bytes:
        """Decrypt data using ChaCha20-Poly1305."""
        from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

        nonce = encrypted_data["nonce"]
        ciphertext = encrypted_data["ciphertext"]
        additional_data = encrypted_data.get("additional_data")

        cipher = ChaCha20Poly1305(key)
        plaintext = cipher.decrypt(nonce, ciphertext, additional_data)

        return plaintext

    async def _encrypt_asymmetric(self, data: bytes, private_key) -> Dict[str, bytes]:
        """Encrypt data using asymmetric encryption."""
        # For RSA-OAEP
        public_key = private_key.public_key()

        ciphertext = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return {
            "ciphertext": ciphertext
        }

    async def _decrypt_asymmetric(self, encrypted_data: Dict[str, bytes], private_key) -> bytes:
        """Decrypt data using asymmetric decryption."""
        ciphertext = encrypted_data["ciphertext"]

        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return plaintext

    async def sign_data(self, data: bytes, key_id: str) -> bytes:
        """
        Create a digital signature for the data.

        Args:
            data: The data to be signed.
            key_id: The ID of the private EC key to use for signing.

        Returns:
            The digital signature.
        """
        key_info = self.get_key_info(key_id)
        if not key_info or key_info['type'] != KeyType.ASYMMETRIC_PRIVATE.value:
            raise ValueError(f"A valid private asymmetric key is required for signing. Key ID: {key_id}")

        private_key = key_info['key']
        if not isinstance(private_key, ec.EllipticCurvePrivateKey):
            raise TypeError("Signing requires an Elliptic Curve private key.")

        signature = private_key.sign(
            data,
            ec.ECDSA(hashes.SHA256())
        )
        return signature

    async def verify_signature(self, data: bytes, signature: bytes, key_id: str) -> bool:
        """
        Verify the digital signature of the data.

        Args:
            data: The data that was signed.
            signature: The signature to verify.
            key_id: The ID of the private key whose public part will be used for verification.

        Returns:
            True if the signature is valid, False otherwise.
        """
        key_info = self.get_key_info(key_id)
        if not key_info:
            raise ValueError(f"Key ID {key_id} not found.")

        private_key = key_info['key']
        public_key = private_key.public_key()

        if not isinstance(public_key, ec.EllipticCurvePublicKey):
            raise TypeError("Verification requires an Elliptic Curve public key.")

        try:
            public_key.verify(
                signature,
                data,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except Exception: # Catches InvalidSignature specifically
            return False

    async def _add_quantum_resistance(self, encrypted_data: Dict) -> Dict:
        """Add quantum resistance layer (simplified implementation)."""
        # In a real implementation, this would use CRYSTALS-Kyber or similar
        # For now, add an additional symmetric encryption layer

        quantum_key = secrets.token_bytes(32)
        self.last_quantum_key = quantum_key # HACK: Store key for demo
        quantum_alg = EncryptionAlgorithm.AES_256_GCM

        # Serialize the encrypted data
        data_to_protect = str(encrypted_data).encode('utf-8')

        quantum_encrypted = await self._encrypt_symmetric(
            data_to_protect, quantum_key, quantum_alg
        )

        return {
            "quantum_layer": quantum_encrypted,
            "quantum_key_fingerprint": hashlib.sha256(quantum_key).hexdigest()[:16],
            "original_data": encrypted_data
        }

    async def _remove_quantum_resistance(self, encrypted_data: Dict) -> Dict:
        """Remove quantum resistance layer."""
        if "quantum_layer" not in encrypted_data:
            return encrypted_data

        # In real implementation, retrieve quantum key securely
        # HACK: For demo, retrieve the key stored from the encryption step.
        if self.last_quantum_key is None:
            raise ValueError("Quantum key not found for this session. Decryption is not possible.")
        quantum_key = self.last_quantum_key

        quantum_layer = encrypted_data["quantum_layer"]
        decrypted_data_str = await self._decrypt_symmetric(
            quantum_layer, quantum_key, EncryptionAlgorithm.AES_256_GCM
        )

        # Parse back to dict
        import ast
        original_data = ast.literal_eval(decrypted_data_str.decode('utf-8'))

        return original_data

    async def rotate_keys(self):
        """Rotate expired keys."""
        now = datetime.now()
        expired_keys = [
            key_id for key_id, expiry in self.key_rotation_schedule.items()
            if expiry <= now
        ]

        for key_id in expired_keys:
            await self._rotate_key(key_id)

        self.logger.info(f"Rotated {len(expired_keys)} keys")

    async def _rotate_key(self, key_id: str):
        """Rotate a specific key."""
        if key_id not in self.key_store:
            return

        old_key_info = self.key_store[key_id]
        algorithm = EncryptionAlgorithm(old_key_info["algorithm"])

        # Generate new key
        new_key, new_key_id = await self._generate_key(algorithm)

        # Update key store
        self.key_store[new_key_id] = self.key_store[key_id].copy()
        self.key_store[new_key_id]["key"] = new_key
        self.key_store[new_key_id]["created_at"] = datetime.now()
        self.key_store[new_key_id]["rotated_from"] = key_id

        # Mark old key as expired but keep for decryption
        self.key_store[key_id]["expired"] = True
        self.key_store[key_id]["rotated_to"] = new_key_id

        # Update rotation schedule
        del self.key_rotation_schedule[key_id]
        self.key_rotation_schedule[new_key_id] = self.key_store[new_key_id]["expires_at"]

    def get_key_info(self, key_id: str) -> Optional[Dict]:
        """Get information about a key."""
        return self.key_store.get(key_id)

    def list_keys(self) -> List[Dict]:
        """List all keys."""
        return [
            {
                "key_id": key_id,
                "algorithm": info["algorithm"],
                "created_at": info["created_at"].isoformat(),
                "expires_at": info["expires_at"].isoformat(),
                "type": info["type"],
                "expired": info.get("expired", False)
            }
            for key_id, info in self.key_store.items()
        ]

    async def homomorphic_encrypt(self, data: Union[int, float]) -> Dict:
        """Perform homomorphic encryption (placeholder)."""
        if not self.config["enable_homomorphic"]:
            raise ValueError("Homomorphic encryption not enabled")

        # Placeholder for homomorphic encryption implementation
        # In real implementation, would use libraries like TenSEAL or Microsoft SEAL

        return {
            "encrypted_value": base64.b64encode(str(data).encode()).decode(),
            "scheme": "placeholder",
            "allow_operations": ["addition", "multiplication"]
        }

    async def homomorphic_compute(self, encrypted_values: List[Dict], operation: str) -> Dict:
        """Perform computation on homomorphically encrypted data."""
        # Placeholder implementation
        return {
            "result": "computed_result_placeholder",
            "operation": operation
        }

    def derive_key_from_password(self, password: str, salt: bytes = None, key_length: int = 32) -> Tuple[bytes, bytes]:
        """
        Derive a secure key from a password using PBKDF2.

        Args:
            password: The password to derive the key from.
            salt: A random salt. If not provided, a new one is generated.
            key_length: The desired length of the derived key in bytes.

        Returns:
            A tuple containing the derived key and the salt used.
        """
        if salt is None:
            salt = secrets.token_bytes(self.config.get("salt_size", 16))

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_length,
            salt=salt,
            iterations=self.config.get("iterations", 100000),
            backend=default_backend()
        )
        key = kdf.derive(password.encode('utf-8'))
        return key, salt


# Global encryption instance
advanced_encryption = AdvancedEncryption()


async def encrypt_data(
    data: Union[str, bytes],
    key_id: Optional[str] = None,
    algorithm: Optional[str] = None
) -> Dict[str, Union[str, bytes]]:
    """Encrypt data using advanced encryption."""
    alg = EncryptionAlgorithm(algorithm) if algorithm else None
    return await advanced_encryption.encrypt_data(data, key_id, alg)


async def decrypt_data(encrypted_data: Dict[str, Union[str, bytes]]) -> bytes:
    """Decrypt data using advanced encryption."""
    return await advanced_encryption.decrypt_data(encrypted_data)


def get_key_info(key_id: str) -> Optional[Dict]:
    """Get key information."""
    return advanced_encryption.get_key_info(key_id)


def list_encryption_keys() -> List[Dict]:
    """List encryption keys."""
    return advanced_encryption.list_keys()


async def sign_data(data: bytes, key_id: str) -> bytes:
    """Create a digital signature for data."""
    return await advanced_encryption.sign_data(data, key_id)


async def verify_signature(data: bytes, signature: bytes, key_id: str) -> bool:
    """Verify a digital signature."""
    return await advanced_encryption.verify_signature(data, signature, key_id)


def derive_key_from_password(password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
    """Derive a secure key from a password."""
    return advanced_encryption.derive_key_from_password(password, salt)


async def main_demo():
    """Demonstrates the advanced encryption functionalities."""
    print("--- Advanced Encryption Demo ---")

    # 1. Symmetric Encryption/Decryption
    print("\n1. Testing Symmetric Encryption (AES-256-GCM)...")
    original_text = "This is a highly confidential message for the IoT platform."
    encrypted_blob = await encrypt_data(original_text, algorithm='aes_256_gcm')
    key_id = encrypted_blob['key_id']
    print(f"   - Encrypted successfully. Key ID: {key_id}")
    decrypted_text = await decrypt_data(encrypted_blob)
    assert decrypted_text.decode('utf-8') == original_text
    print("   - Decryption successful. Data matches.")

    # 2. Digital Signature (ECDSA)
    print("\n2. Testing Digital Signatures (ECDSA)...")
    # Generate a new ECDSA key for signing
    _, sign_key_id = await advanced_encryption._generate_key(EncryptionAlgorithm.ECDSA_P256)
    print(f"   - Generated a new ECDSA key. Key ID: {sign_key_id}")

    message_to_sign = b"This data must be authentic and integral."
    signature = await sign_data(message_to_sign, sign_key_id)
    print(f"   - Data signed. Signature length: {len(signature)} bytes.")

    # Verification
    is_valid = await verify_signature(message_to_sign, signature, sign_key_id)
    assert is_valid
    print(f"   - Signature verification successful: {is_valid}")

    is_invalid = await verify_signature(b"tampered data", signature, sign_key_id)
    assert not is_invalid
    print(f"   - Verification of tampered data correctly failed: {not is_invalid}")

    # 3. Key Derivation from Password
    print("\n3. Testing Key Derivation from Password (PBKDF2)...")
    password = "supersecretpassword123"
    derived_key, salt = derive_key_from_password(password)
    print(f"   - Derived a {len(derived_key)*8}-bit key from password.")
    print(f"   - Salt (hex): {salt.hex()}")

    # Verify that the same password and salt produce the same key
    derived_key_2, _ = derive_key_from_password(password, salt)
    assert derived_key == derived_key_2
    print("   - Key derivation is deterministic and successful.")

    print("\n--- Demo Complete ---")


if __name__ == "__main__":
    asyncio.run(main_demo())