"""
Blockchain Integration Module (with Simulated Ledger)

This module implements an enhanced blockchain integration system, featuring a
fully simulated blockchain ledger. It's designed for securely recording IoT
data and automating actions via smart contracts without external dependencies.

Key Features:
- Simulated Blockchain Ledger: Manages a local chain of blocks, including a
  genesis block, pending transactions, and a mining process.
- Immutable IoT Data Recording: Allows recording sensor data as transactions
  that are then mined into immutable blocks on the simulated chain.
- Chain Integrity Verification: Includes a method to validate the entire
  blockchain, ensuring data has not been tampered with.
- Automated Smart Contracts: A simple rule-based smart contract system that
  triggers actions (e.g., alerts) based on IoT data recorded on the chain.
"""

import asyncio
import json
import logging
import hashlib
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from utils.logging_config import get_logger

logger = get_logger(__name__)


# --- Data Structures ---
@dataclass
class Transaction:
    """Represents a transaction in a block."""
    tx_id: str
    sender: str
    recipient: str
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

@dataclass
class Block:
    """Represents a block in the blockchain."""
    index: int
    timestamp: float
    transactions: List[Transaction]
    nonce: int
    previous_hash: str
    hash: str = ""

# --- Main Blockchain Class ---
class BlockchainConnector:
    """
    Manages a simulated blockchain for IoT data integrity and automation.
    """
    def __init__(self):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.smart_contract_rules: Dict[str, Any] = {}
        self._create_genesis_block()
        self.wallets = {} # Using a simple dict to simulate wallets
        logger.info("BlockchainConnector initialized with a genesis block.")

    def _create_genesis_block(self):
        """Creates the very first block in the chain."""
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            transactions=[],
            nonce=0,
            previous_hash="0"
        )
        genesis_block.hash = self._calculate_hash(genesis_block)
        self.chain.append(genesis_block)

    def _calculate_hash(self, block: Block) -> str:
        """Calculates the SHA-256 hash of a block."""
        block_string = json.dumps({
            "index": block.index,
            "timestamp": block.timestamp,
            "transactions": [tx.__dict__ for tx in block.transactions],
            "nonce": block.nonce,
            "previous_hash": block.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self) -> Block:
        """Returns the most recent block in the chain."""
        return self.chain[-1]

    def create_wallet(self, wallet_id: str) -> str:
        """Creates a new simulated wallet (address)."""
        if wallet_id in self.wallets:
            raise ValueError(f"Wallet with ID '{wallet_id}' already exists.")
        address = f"addr_{wallet_id}_{hashlib.sha256(wallet_id.encode()).hexdigest()[:10]}"
        self.wallets[wallet_id] = address
        logger.info(f"Created wallet '{wallet_id}' with address '{address}'.")
        return address

    def record_iot_data(self, device_id: str, sensor_data: Dict[str, Any], wallet_id: str) -> str:
        """
        Creates a transaction for IoT sensor data and adds it to the pending pool.
        """
        if wallet_id not in self.wallets:
            raise ValueError(f"Sender wallet '{wallet_id}' not found.")

        tx_id = hashlib.sha256(json.dumps(sensor_data, sort_keys=True).encode() + str(time.time()).encode()).hexdigest()
        transaction = Transaction(
            tx_id=tx_id,
            sender=self.wallets[wallet_id],
            recipient="data_ledger", # A conceptual address for data records
            data={"device_id": device_id, "sensor_data": sensor_data}
        )
        self.pending_transactions.append(transaction)
        logger.debug(f"Queued IoT data transaction {tx_id} from device '{device_id}'.")
        return tx_id

    def mine_block(self) -> Block:
        """
        Mines a new block, adds it to the chain, and processes smart contracts.
        """
        if not self.pending_transactions:
            logger.warning("Mining attempted with no pending transactions.")
            # In a real scenario might create an empty block, but for simulation we'll just return
            return self.last_block

        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            transactions=self.pending_transactions,
            nonce=0, # In a real PoW, this would be iterated
            previous_hash=self.last_block.hash
        )
        new_block.hash = self._calculate_hash(new_block)
        
        self.chain.append(new_block)
        logger.info(f"Mined new block #{new_block.index} with {len(new_block.transactions)} transactions.")
        
        self.pending_transactions = []

        # Process smart contracts after mining
        self._process_smart_contracts(new_block)

        return new_block

    def register_iot_smart_contract(self, contract_id: str, device_id: str, condition: str, action: callable):
        """
        Registers a simple rule-based smart contract for IoT data.
        Example condition: "sensor_data['temperature'] > 50"
        """
        self.smart_contract_rules[contract_id] = {
            "device_id": device_id,
            "condition": condition,
            "action": action
        }
        logger.info(f"Registered smart contract '{contract_id}' for device '{device_id}'.")

    def _process_smart_contracts(self, block: Block):
        """Checks transactions in a new block against registered smart contract rules."""
        for tx in block.transactions:
            device_id = tx.data.get("device_id")
            if not device_id:
                continue

            for contract_id, rule in self.smart_contract_rules.items():
                if rule["device_id"] == device_id:
                    try:
                        # WARNING: eval is used for simplicity. In production, a safe parsing engine is a must.
                        if eval(rule["condition"], {"__builtins__": {}}, tx.data):
                            logger.info(f"Smart contract '{contract_id}' triggered for device '{device_id}'.")
                            rule["action"](tx.data)
                    except Exception as e:
                        logger.error(f"Error executing smart contract '{contract_id}': {e}")

    def verify_chain_integrity(self) -> bool:
        """
        Verifies the integrity of the entire blockchain by checking hashes.
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            # Recalculate hash and check if it's correct
            if current_block.hash != self._calculate_hash(current_block):
                logger.error(f"Data tampering detected: Hash of Block #{current_block.index} is invalid.")
                return False

            # Check if it links to the previous block correctly
            if current_block.previous_hash != previous_block.hash:
                logger.error(f"Chain broken: Block #{current_block.index} previous_hash does not match hash of Block #{previous_block.index}.")
                return False

        logger.info("Blockchain integrity verified successfully.")
        return True

    def get_device_history(self, device_id: str) -> List[Dict]:
        """Retrieves all data recorded for a specific device from the chain."""
        history = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.data.get("device_id") == device_id:
                    history.append({
                        "block_index": block.index,
                        "timestamp": block.timestamp,
                        "data": tx.data['sensor_data']
                    })
        return history

# --- Demonstration ---
if __name__ == "__main__":

    # --- Action for Smart Contract ---
    def trigger_alert(data: Dict):
        print(f"\n[!!!] SMART CONTRACT ALERT [!!!]")
        print(f"High temperature detected on device {data['device_id']}: {data['sensor_data']['temperature']}°C")
        print(f"[!!!] ACTION: Schedule immediate inspection.\n")

    async def simulate():
        print("--- Initializing Blockchain Simulation for IoT Data ---")
        bc = BlockchainConnector()

        # 1. Create wallets for devices
        bc.create_wallet("factory_A_main")
        bc.create_wallet("device_temp_sensor_001")
        bc.create_wallet("device_pressure_sensor_002")

        # 2. Register a smart contract
        bc.register_iot_smart_contract(
            contract_id="high_temp_alert",
            device_id="temp_sensor_001",
            condition="sensor_data['temperature'] > 45.0",
            action=trigger_alert
        )

        # 3. Simulate recording data over time
        print("\n--- Simulating data recording (5 data points) ---")
        bc.record_iot_data("temp_sensor_001", {"temperature": 25.5, "humidity": 60}, "device_temp_sensor_001")
        bc.record_iot_data("pressure_sensor_002", {"pressure": 1013, "unit": "hPa"}, "device_pressure_sensor_002")
        await asyncio.sleep(0.1)
        bc.record_iot_data("temp_sensor_001", {"temperature": 35.2, "humidity": 58}, "device_temp_sensor_001")
        await asyncio.sleep(0.1)
        bc.record_iot_data("temp_sensor_001", {"temperature": 48.9, "humidity": 55}, "device_temp_sensor_001") # This should trigger the contract
        bc.record_iot_data("pressure_sensor_002", {"pressure": 1015, "unit": "hPa"}, "device_pressure_sensor_002")

        print(f"Total pending transactions: {len(bc.pending_transactions)}")

        # 4. Mine a new block to confirm transactions
        print("\n--- Mining a new block ---")
        mined_block = bc.mine_block()
        print(f"Block #{mined_block.index} mined with hash: {mined_block.hash[:20]}...")

        # 5. Verify chain integrity
        print("\n--- Verifying blockchain integrity ---")
        is_valid = bc.verify_chain_integrity()
        print(f"Chain integrity valid: {is_valid}")

        # 6. Tamper with the data (for demonstration)
        print("\n--- Simulating data tampering ---")
        try:
            # Directly modifying a transaction in a past block
            bc.chain[1].transactions[0].data['sensor_data']['temperature'] = 999.9
            print("Modified temperature in Block #1.")
        except IndexError:
            print("Not enough blocks to tamper with. Skipping.")

        # 7. Verify integrity again
        print("\n--- Verifying integrity after tampering ---")
        is_valid_after_tamper = bc.verify_chain_integrity()
        print(f"Chain integrity valid after tampering: {is_valid_after_tamper}")

        # 8. Retrieve history for a device
        print("\n--- Retrieving history for 'temp_sensor_001' ---")
        # Note: the history will show the tampered data because we modified it in-memory
        history = bc.get_device_history("temp_sensor_001")
        for record in history:
            print(f"  - Block {record['block_index']}: {record['data']}")

    asyncio.run(simulate())
