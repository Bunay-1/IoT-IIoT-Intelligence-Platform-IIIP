"""
Advanced Encryption Module with Secure Enclave Simulation.

This module provides a robust cryptographic service simulating a hardware
secure enclave for key management and implementing a hybrid encryption scheme
(similar to ECIES) for secure data exchange.
"""

import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

from utils.logging_config import get_logger

class SecureEnclaveSimulator:
    """
    Simulates a hardware secure enclave for key management.

    In a real system, this would be a hardware security module (HSM) or a
    secure element in a CPU (e.g., Intel SGX, Apple Secure Enclave).
    This simulation stores keys in memory and never exposes private keys.
    """
    def __init__(self, logger):
        self.logger = logger
        self._key_pairs: Dict[str, Dict] = {} # {key_id: {'private': RsaKey, 'public': RsaKey, 'created_at': datetime}}
        self._active_key_id: Optional[str] = None
        self.logger.info("Secure Enclave Simulator initialized.")

    def generate_key_pair(self, key_id: str, bits: int = 2048) -> str:
        """Generates and stores a new RSA key pair inside the enclave."""
        private_key = RSA.generate(bits)
        public_key = private_key.publickey()
        self._key_pairs[key_id] = {
            "private": private_key,
            "public": public_key,
            "created_at": datetime.now(timezone.utc)
        }
        if not self._active_key_id:
            self._active_key_id = key_id
        self.logger.info(f"Generated and stored new {bits}-bit key pair with ID: {key_id}")
        return public_key.export_key().decode('utf-8')

    def get_public_key(self, key_id: Optional[str] = None) -> Optional[str]:
        """Retrieves the public key for a given key ID (or the active one)."""
        target_key_id = key_id or self._active_key_id
        if target_key_id in self._key_pairs:
            return self._key_pairs[target_key_id]["public"].export_key().decode('utf-8')
        self.logger.warning(f"Public key for ID '{target_key_id}' not found.")
        return None

    def rotate_keys(self, new_key_id: str):
        """Generates a new key pair and sets it as the active one."""
        self.generate_key_pair(new_key_id)
        self._active_key_id = new_key_id
        self.logger.info(f"Key rotation complete. New active key ID is '{new_key_id}'.")

    def _decrypt_with_private_key(self, key_id: str, ciphertext: bytes) -> bytes:
        """Internal method to decrypt using a stored private key."""
        if key_id not in self._key_pairs:
            raise ValueError(f"Key ID '{key_id}' not found in enclave.")

        private_key = self._key_pairs[key_id]["private"]
        cipher_rsa = PKCS1_OAEP.new(private_key)
        return cipher_rsa.decrypt(ciphertext)

class HybridEncryptionService:
    """
    Provides hybrid encryption using RSA and AES-GCM.

    This service encrypts data using a fresh symmetric key (AES) for each message,
    and then encrypts that symmetric key with the recipient's public RSA key.
    """
    def __init__(self, enclave: SecureEnclaveSimulator):
        self.enclave = enclave
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def encrypt(self, data: bytes, recipient_public_key_pem: str, recipient_key_id: str) -> str:
        """
        Encrypts data using a hybrid encryption scheme.

        Args:
            data: The raw bytes to encrypt.
            recipient_public_key_pem: The PEM-encoded public key of the recipient.
            recipient_key_id: The identifier for the recipient's key pair.

        Returns:
            A JSON string containing all necessary components for decryption.
        """
        # 1. Import recipient's public key
        recipient_public_key = RSA.import_key(recipient_public_key_pem)

        # 2. Generate a one-time AES session key
        session_key = get_random_bytes(16)

        # 3. Encrypt the session key with the recipient's public RSA key
        cipher_rsa = PKCS1_OAEP.new(recipient_public_key)
        encrypted_session_key = cipher_rsa.encrypt(session_key)

        # 4. Encrypt the data with the AES session key using GCM mode
        cipher_aes = AES.new(session_key, AES.MODE_GCM)
        ciphertext, tag = cipher_aes.encrypt_and_digest(data)

        # 5. Pack everything into a JSON object for transport
        encrypted_payload = {
            "key_id": recipient_key_id,  # CRITICAL: Use the recipient's key ID
            "encrypted_session_key": encrypted_session_key.hex(),
            "nonce": cipher_aes.nonce.hex(),
            "tag": tag.hex(),
            "ciphertext": ciphertext.hex()
        }
        self.logger.info(f"Data encrypted for recipient key ID '{recipient_key_id}'.")
        return json.dumps(encrypted_payload)

    def decrypt(self, encrypted_payload_json: str) -> bytes:
        """
        Decrypts a hybrid encrypted payload using a private key from the enclave.
        """
        try:
            payload = json.loads(encrypted_payload_json)
            key_id = payload["key_id"]

            # 1. Decrypt the session key using the enclave's private key
            encrypted_session_key = bytes.fromhex(payload["encrypted_session_key"])
            session_key = self.enclave._decrypt_with_private_key(key_id, encrypted_session_key)

            # 2. Decrypt the data using the AES session key
            nonce = bytes.fromhex(payload["nonce"])
            tag = bytes.fromhex(payload["tag"])
            ciphertext = bytes.fromhex(payload["ciphertext"])

            cipher_aes = AES.new(session_key, AES.MODE_GCM, nonce=nonce)
            decrypted_data = cipher_aes.decrypt_and_verify(ciphertext, tag)

            self.logger.info("Data decrypted successfully.")
            return decrypted_data
        except (ValueError, KeyError, TypeError) as e:
            self.logger.error(f"Decryption failed due to malformed payload or key error: {e}")
            raise ValueError("Decryption failed. The payload may be corrupt or the key invalid.")

if __name__ == "__main__":
    async def main():
        print("--- Advanced Encryption with Secure Enclave and Hybrid Scheme Demo ---")
        logger = get_logger("EncryptionDemo")

        # 1. Initialize the Secure Enclave and Encryption Service
        print("\n--- 1. Initializing Secure Enclave and Services ---")
        enclave = SecureEnclaveSimulator(logger)
        hybrid_service = HybridEncryptionService(enclave)

        # 2. Generate key pairs for two parties: Alice and Bob
        print("\n--- 2. Generating Key Pairs for Alice and Bob ---")
        alice_public_key_pem = enclave.generate_key_pair("alice_key_v1")
        bob_public_key_pem = enclave.generate_key_pair("bob_key_v1")
        print("Alice's and Bob's keys are generated and stored in the enclave.")
        # Note: We only get their public keys back. Private keys never leave the enclave.

        # 3. Alice encrypts a message for Bob
        print("\n--- 3. Alice encrypts a secret message for Bob ---")
        secret_message = b"Meet at the usual place at midnight. The eagle has landed."
        # Alice uses Bob's public key to encrypt the message
        encrypted_message_for_bob = hybrid_service.encrypt(secret_message, bob_public_key_pem, "bob_key_v1")
        print("Message encrypted. Transmitting the following payload:")
        print(encrypted_message_for_bob)

        # 4. Bob decrypts the message using the service (which uses his private key from the enclave)
        print("\n--- 4. Bob receives and decrypts the message ---")
        # Bob's side of the application calls the decrypt service.
        # The service automatically finds the correct private key ('bob_key_v1') in the enclave.
        decrypted_message = hybrid_service.decrypt(encrypted_message_for_bob)

        print(f"Decrypted message: {decrypted_message.decode('utf-8')}")
        assert secret_message == decrypted_message
        print("SUCCESS: Decrypted message matches original secret.")

        # 5. Demonstrate Key Rotation
        print("\n--- 5. Bob rotates his encryption key ---")
        enclave.rotate_keys("bob_key_v2")
        new_bob_public_key_pem = enclave.get_public_key() # Gets the new active key

        print(f"Bob's active key is now '{enclave._active_key_id}'.")
        assert enclave._active_key_id == "bob_key_v2"

        # Alice encrypts a new message with Bob's NEW public key
        new_secret = b"The plan has changed. Await new instructions."
        encrypted_new_secret = hybrid_service.encrypt(new_secret, new_bob_public_key_pem, "bob_key_v2")

        # Bob decrypts the new message
        decrypted_new_secret = hybrid_service.decrypt(encrypted_new_secret)
        assert new_secret == decrypted_new_secret
        print("SUCCESS: Message encrypted with rotated key was decrypted successfully.")

        # Try to decrypt the OLD message (should still work if old key is retained)
        print("\n--- 6. Bob tries to decrypt the old message with the old key ---")
        old_message_decrypted = hybrid_service.decrypt(encrypted_message_for_bob)
        assert secret_message == old_message_decrypted
        print("SUCCESS: Old message can still be decrypted with the previous key.")

    import asyncio
    asyncio.run(main())