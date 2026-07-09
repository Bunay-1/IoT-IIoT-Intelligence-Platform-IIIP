"""
Decentralized Identity for IoT Devices Module

This module provides decentralized identity management for IoT devices using DID (Decentralized Identifiers).
It enables self-sovereign identity for devices, allowing them to own and control their own identity without central authorities.

Features:
- DID creation and management for IoT devices
- Verifiable credentials for device attributes
- Decentralized identity resolution
- Integration with blockchain for identity anchoring
"""

import hashlib
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

class DecentralizedIdentityManager:
    """
    Manager for decentralized identities of IoT devices.
    """

    def __init__(self, blockchain_connector=None):
        """
        Initialize the DID manager.

        Args:
            blockchain_connector: Optional blockchain connector for anchoring DIDs
        """
        self.devices: Dict[str, Dict] = {}
        self.blockchain = blockchain_connector

    def create_device_did(self, device_id: str, device_info: Dict[str, Any]) -> str:
        """
        Create a decentralized identifier for an IoT device.

        Args:
            device_id: Unique device identifier
            device_info: Device information (type, manufacturer, capabilities, etc.)

        Returns:
            str: The created DID
        """
        # Generate DID using did:web method for simplicity
        # In production, this could use did:key, did:ethr, etc.
        did = f"did:web:iot-platform:{device_id}"

        # Create DID document
        did_document = {
            "@context": "https://www.w3.org/ns/did/v1",
            "id": did,
            "created": datetime.utcnow().isoformat() + "Z",
            "verificationMethod": [{
                "id": f"{did}#key-1",
                "type": "Ed25519VerificationKey2020",
                "controller": did,
                "publicKeyMultibase": self._generate_public_key(device_id)
            }],
            "service": [{
                "id": f"{did}#service-1",
                "type": "IoTDeviceService",
                "serviceEndpoint": f"https://iot-platform.com/devices/{device_id}"
            }]
        }

        # Store device information
        self.devices[device_id] = {
            "did": did,
            "did_document": did_document,
            "device_info": device_info,
            "credentials": [],
            "created_at": datetime.utcnow()
        }

        # Anchor to blockchain if available
        if self.blockchain:
            self._anchor_to_blockchain(did, did_document)

        return did

    def issue_credential(self, device_id: str, credential_type: str, claims: Dict[str, Any], issuer_did: str) -> Dict:
        """
        Issue a verifiable credential for a device.

        Args:
            device_id: Device identifier
            credential_type: Type of credential (e.g., "DeviceCertification", "ComplianceCredential")
            claims: Credential claims
            issuer_did: DID of the issuer

        Returns:
            Dict: The issued verifiable credential
        """
        if device_id not in self.devices:
            raise ValueError(f"Device {device_id} not found")

        device_did = self.devices[device_id]["did"]

        credential = {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://iot-platform.com/contexts/v1"
            ],
            "id": f"urn:uuid:{uuid.uuid4()}",
            "type": ["VerifiableCredential", credential_type],
            "issuer": issuer_did,
            "issuanceDate": datetime.utcnow().isoformat() + "Z",
            "credentialSubject": {
                "id": device_did,
                **claims
            },
            "proof": self._generate_proof(credential, issuer_did)
        }

        # Store credential
        self.devices[device_id]["credentials"].append(credential)

        return credential

    def verify_credential(self, credential: Dict) -> bool:
        """
        Verify a verifiable credential.

        Args:
            credential: The credential to verify

        Returns:
            bool: True if valid, False otherwise
        """
        # Basic verification - check proof
        # In production, this would involve cryptographic verification
        proof = credential.get("proof", {})
        if not proof:
            return False

        # Verify issuer
        issuer = credential.get("issuer")
        if not issuer:
            return False

        # Check expiration if present
        if "expirationDate" in credential:
            expiration = datetime.fromisoformat(credential["expirationDate"].replace("Z", ""))
            if datetime.utcnow() > expiration:
                return False

        return True

    def resolve_did(self, did: str) -> Optional[Dict]:
        """
        Resolve a DID to its document.

        Args:
            did: The DID to resolve

        Returns:
            Optional[Dict]: The DID document if found
        """
        for device in self.devices.values():
            if device["did"] == did:
                return device["did_document"]
        return None

    def get_device_credentials(self, device_id: str) -> List[Dict]:
        """
        Get all credentials for a device.

        Args:
            device_id: Device identifier

        Returns:
            List[Dict]: List of credentials
        """
        if device_id not in self.devices:
            return []
        return self.devices[device_id]["credentials"]

    def _generate_public_key(self, device_id: str) -> str:
        """
        Generate a mock public key for the device.
        In production, this would use proper cryptographic key generation.
        """
        # Mock implementation - in reality, use Ed25519 or similar
        hash_obj = hashlib.sha256(device_id.encode())
        return "z" + hash_obj.hexdigest()[:43]  # Multibase encoded

    def _generate_proof(self, credential: Dict, issuer_did: str) -> Dict:
        """
        Generate a proof for the credential.
        Mock implementation for demonstration.
        """
        # In production, this would create a proper cryptographic proof
        proof_data = json.dumps(credential, sort_keys=True, default=str)
        proof_hash = hashlib.sha256(proof_data.encode()).hexdigest()

        return {
            "type": "Ed25519Signature2020",
            "created": datetime.utcnow().isoformat() + "Z",
            "verificationMethod": f"{issuer_did}#key-1",
            "proofPurpose": "assertionMethod",
            "proofValue": "z" + proof_hash[:86]  # Mock signature
        }

    def _anchor_to_blockchain(self, did: str, did_document: Dict):
        """
        Anchor the DID document to blockchain.
        Mock implementation.
        """
        if self.blockchain:
            # In production, this would submit to blockchain
            print(f"Anchoring DID {did} to blockchain")
            # self.blockchain.anchor_did(did, did_document)

# Example usage
if __name__ == "__main__":
    did_manager = DecentralizedIdentityManager()

    # Create DID for a device
    device_info = {
        "type": "temperature_sensor",
        "manufacturer": "IoT Corp",
        "capabilities": ["temperature_reading", "humidity_reading"]
    }

    did = did_manager.create_device_did("temp_sensor_001", device_info)
    print(f"Created DID: {did}")

    # Issue a credential
    credential = did_manager.issue_credential(
        "temp_sensor_001",
        "DeviceCertification",
        {"certified": True, "calibration_date": "2024-01-01"},
        "did:web:iot-platform:certification-authority"
    )

    print("Issued credential:", json.dumps(credential, indent=2, default=str))

    # Verify credential
    is_valid = did_manager.verify_credential(credential)
    print(f"Credential valid: {is_valid}")

    # Get device credentials
    credentials = did_manager.get_device_credentials("temp_sensor_001")
    print(f"Device has {len(credentials)} credentials")