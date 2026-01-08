"""
NFT for Industrial Assets Module

This module enables tokenization of industrial assets as NFTs (Non-Fungible Tokens).
It allows ownership, trading, and tracking of industrial equipment, machinery, and facilities
using blockchain technology.

Features:
- NFT creation for industrial assets
- Asset metadata management
- Ownership transfer and trading
- Asset lifecycle tracking
- Integration with supply chain
"""

import hashlib
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

class IndustrialAssetNFT:
    """
    NFT representation of an industrial asset.
    """

    def __init__(self, asset_id: str, name: str, asset_type: str, metadata: Dict[str, Any]):
        """
        Initialize an industrial asset NFT.

        Args:
            asset_id: Unique asset identifier
            name: Asset name
            asset_type: Type of asset (machine, facility, equipment, etc.)
            metadata: Asset metadata (specifications, maintenance history, etc.)
        """
        self.asset_id = asset_id
        self.name = name
        self.asset_type = asset_type
        self.metadata = metadata
        self.token_id = self._generate_token_id()
        self.owner = None
        self.created_at = datetime.utcnow()
        self.transactions: List[Dict] = []

        # NFT metadata following ERC-721 standard
        self.nft_metadata = {
            "name": name,
            "description": f"Industrial Asset: {name} - {asset_type}",
            "image": self._generate_asset_image(),
            "attributes": self._generate_attributes(),
            "external_url": f"https://iot-platform.com/assets/{asset_id}"
        }

    def _generate_token_id(self) -> str:
        """
        Generate a unique token ID for the NFT.
        """
        data = f"{self.asset_id}{self.name}{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _generate_asset_image(self) -> str:
        """
        Generate or reference an image for the asset.
        In production, this would be a real image URL or IPFS hash.
        """
        # Mock implementation - in reality, generate or upload image
        return f"https://iot-platform.com/images/assets/{self.asset_type}.png"

    def _generate_attributes(self) -> List[Dict]:
        """
        Generate NFT attributes from asset metadata.
        """
        attributes = [
            {
                "trait_type": "Asset Type",
                "value": self.asset_type
            },
            {
                "trait_type": "Created Date",
                "value": self.created_at.strftime("%Y-%m-%d")
            }
        ]

        # Add custom attributes from metadata
        for key, value in self.metadata.items():
            if isinstance(value, (str, int, float)):
                attributes.append({
                    "trait_type": key.replace("_", " ").title(),
                    "value": str(value)
                })

        return attributes

    def mint(self, owner_address: str) -> Dict:
        """
        Mint the NFT and assign initial owner.

        Args:
            owner_address: Blockchain address of the owner

        Returns:
            Dict: Mint transaction details
        """
        self.owner = owner_address

        transaction = {
            "type": "mint",
            "token_id": self.token_id,
            "from": "0x0000000000000000000000000000000000000000",  # Zero address for minting
            "to": owner_address,
            "timestamp": datetime.utcnow().isoformat(),
            "block_number": self._get_current_block(),
            "transaction_hash": self._generate_transaction_hash()
        }

        self.transactions.append(transaction)

        return {
            "success": True,
            "token_id": self.token_id,
            "owner": owner_address,
            "transaction": transaction,
            "nft_metadata": self.nft_metadata
        }

    def transfer(self, from_address: str, to_address: str, price: Optional[float] = None) -> Dict:
        """
        Transfer ownership of the NFT.

        Args:
            from_address: Current owner address
            to_address: New owner address
            price: Optional transfer price

        Returns:
            Dict: Transfer transaction details
        """
        if self.owner != from_address:
            raise ValueError("Unauthorized transfer - not the current owner")

        self.owner = to_address

        transaction = {
            "type": "transfer",
            "token_id": self.token_id,
            "from": from_address,
            "to": to_address,
            "price": price,
            "timestamp": datetime.utcnow().isoformat(),
            "block_number": self._get_current_block(),
            "transaction_hash": self._generate_transaction_hash()
        }

        self.transactions.append(transaction)

        return {
            "success": True,
            "token_id": self.token_id,
            "new_owner": to_address,
            "transaction": transaction
        }

    def update_metadata(self, new_metadata: Dict[str, Any]) -> bool:
        """
        Update asset metadata.

        Args:
            new_metadata: New metadata to add/update

        Returns:
            bool: Success status
        """
        self.metadata.update(new_metadata)
        self.nft_metadata["attributes"] = self._generate_attributes()

        # Record update transaction
        transaction = {
            "type": "metadata_update",
            "token_id": self.token_id,
            "timestamp": datetime.utcnow().isoformat(),
            "updated_fields": list(new_metadata.keys())
        }

        self.transactions.append(transaction)

        return True

    def get_ownership_history(self) -> List[Dict]:
        """
        Get the complete ownership history of the asset.

        Returns:
            List[Dict]: List of ownership transactions
        """
        return self.transactions

    def get_current_value(self) -> Optional[float]:
        """
        Get the current market value of the asset.
        Mock implementation - in reality, this would query market data.
        """
        # Mock valuation based on asset type and age
        base_values = {
            "machine": 50000,
            "facility": 1000000,
            "equipment": 10000,
            "vehicle": 30000
        }

        base_value = base_values.get(self.asset_type, 10000)
        age_years = (datetime.utcnow() - self.created_at).days / 365

        # Simple depreciation model
        depreciation_rate = 0.05  # 5% per year
        current_value = base_value * (1 - depreciation_rate) ** age_years

        return max(current_value, 1000)  # Minimum value

    def _get_current_block(self) -> int:
        """
        Get current blockchain block number.
        Mock implementation.
        """
        # In production, query actual blockchain
        return 12345678

    def _generate_transaction_hash(self) -> str:
        """
        Generate a mock transaction hash.
        """
        data = f"{self.token_id}{datetime.utcnow().isoformat()}{uuid.uuid4()}"
        return "0x" + hashlib.sha256(data.encode()).hexdigest()

class IndustrialNFTManager:
    """
    Manager for industrial asset NFTs.
    """

    def __init__(self):
        self.assets: Dict[str, IndustrialAssetNFT] = {}

    def create_asset_nft(self, asset_id: str, name: str, asset_type: str, metadata: Dict[str, Any]) -> IndustrialAssetNFT:
        """
        Create a new industrial asset NFT.

        Args:
            asset_id: Unique asset identifier
            name: Asset name
            asset_type: Type of asset
            metadata: Asset metadata

        Returns:
            IndustrialAssetNFT: The created NFT
        """
        if asset_id in self.assets:
            raise ValueError(f"Asset {asset_id} already exists")

        nft = IndustrialAssetNFT(asset_id, name, asset_type, metadata)
        self.assets[asset_id] = nft

        return nft

    def get_asset_nft(self, asset_id: str) -> Optional[IndustrialAssetNFT]:
        """
        Get an asset NFT by ID.

        Args:
            asset_id: Asset identifier

        Returns:
            Optional[IndustrialAssetNFT]: The NFT if found
        """
        return self.assets.get(asset_id)

    def list_assets_by_owner(self, owner_address: str) -> List[IndustrialAssetNFT]:
        """
        List all assets owned by an address.

        Args:
            owner_address: Owner address

        Returns:
            List[IndustrialAssetNFT]: List of owned assets
        """
        return [asset for asset in self.assets.values() if asset.owner == owner_address]

    def list_assets_by_type(self, asset_type: str) -> List[IndustrialAssetNFT]:
        """
        List all assets of a specific type.

        Args:
            asset_type: Asset type

        Returns:
            List[IndustrialAssetNFT]: List of assets of the type
        """
        return [asset for asset in self.assets.values() if asset.asset_type == asset_type]

# Example usage
if __name__ == "__main__":
    manager = IndustrialNFTManager()

    # Create an industrial asset NFT
    metadata = {
        "manufacturer": "Siemens",
        "model": "S7-1500",
        "serial_number": "SN123456",
        "installation_date": "2020-01-15",
        "maintenance_schedule": "quarterly",
        "efficiency_rating": 95.5
    }

    asset_nft = manager.create_asset_nft(
        "machine_001",
        "Production Line Machine",
        "machine",
        metadata
    )

    print(f"Created NFT with token ID: {asset_nft.token_id}")

    # Mint the NFT
    mint_result = asset_nft.mint("0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
    print(f"Minted to: {mint_result['owner']}")

    # Update metadata
    asset_nft.update_metadata({"last_maintenance": "2024-12-01", "efficiency_rating": 97.2})
    print("Metadata updated")

    # Get current value
    value = asset_nft.get_current_value()
    print(f"Current estimated value: ${value:,.2f}")

    # Transfer ownership
    transfer_result = asset_nft.transfer(
        "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "0x8ba1f109551bD432803012645261ad5D634606b",
        45000.0
    )
    print(f"Transferred to: {transfer_result['new_owner']} for ${transfer_result['transaction']['price']}")

    # Get ownership history
    history = asset_nft.get_ownership_history()
    print(f"Asset has {len(history)} transactions in history")