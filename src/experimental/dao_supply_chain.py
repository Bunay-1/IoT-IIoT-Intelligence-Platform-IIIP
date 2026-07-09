"""
DAO for Supply Chain Module

This module implements a Decentralized Autonomous Organization (DAO) specifically for supply chain management.
It enables collaborative decision-making across supply chain partners, automated contract execution,
and transparent tracking of goods and services using blockchain technology.

Features:
- Multi-party supply chain governance
- Smart contract-based agreements
- Automated compliance and quality checks
- Transparent inventory and shipment tracking
- Decentralized dispute resolution
"""

import hashlib
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import uuid
from enum import Enum

class SupplyChainRole(Enum):
    MANUFACTURER = "manufacturer"
    SUPPLIER = "supplier"
    DISTRIBUTOR = "distributor"
    RETAILER = "retailer"
    LOGISTICS = "logistics"
    REGULATOR = "regulator"

class ContractStatus(Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    ACTIVE = "active"
    COMPLETED = "completed"
    BREACHED = "breached"
    TERMINATED = "terminated"

class SupplyChainContract:
    """
    Smart contract for supply chain agreements.
    """

    def __init__(self, contract_id: str, parties: List[str], terms: Dict[str, Any],
                 auto_execute_conditions: List[Callable] = None):
        """
        Initialize a supply chain contract.

        Args:
            contract_id: Unique contract identifier
            parties: List of party addresses involved
            terms: Contract terms and conditions
            auto_execute_conditions: Conditions for automatic execution
        """
        self.contract_id = contract_id
        self.parties = parties
        self.terms = terms
        self.auto_execute_conditions = auto_execute_conditions or []

        self.status = ContractStatus.DRAFT
        self.created_at = datetime.utcnow()
        self.activated_at = None
        self.completed_at = None

        self.performance_metrics: Dict[str, Any] = {}
        self.disputes: List[Dict] = []
        self.amendments: List[Dict] = []

    def propose(self) -> bool:
        """
        Propose the contract to all parties.

        Returns:
            bool: Success status
        """
        if self.status != ContractStatus.DRAFT:
            return False

        self.status = ContractStatus.PROPOSED
        return True

    def activate(self) -> bool:
        """
        Activate the contract once all parties agree.

        Returns:
            bool: Success status
        """
        if self.status != ContractStatus.PROPOSED:
            return False

        self.status = ContractStatus.ACTIVE
        self.activated_at = datetime.utcnow()
        return True

    def check_auto_execute(self) -> List[Any]:
        """
        Check and execute automatic conditions.

        Returns:
            List[Any]: Results of executed conditions
        """
        if self.status != ContractStatus.ACTIVE:
            return []

        results = []
        for condition in self.auto_execute_conditions:
            try:
                if condition():
                    result = condition()
                    results.append(result)
            except Exception as e:
                results.append(f"Condition failed: {str(e)}")

        return results

    def complete(self) -> bool:
        """
        Mark contract as completed.

        Returns:
            bool: Success status
        """
        if self.status != ContractStatus.ACTIVE:
            return False

        self.status = ContractStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        return True

    def breach(self, breached_by: str, reason: str) -> bool:
        """
        Report a contract breach.

        Args:
            breached_by: Party that breached
            reason: Reason for breach

        Returns:
            bool: Success status
        """
        if self.status not in [ContractStatus.ACTIVE, ContractStatus.PROPOSED]:
            return False

        self.status = ContractStatus.BREACHED
        self.disputes.append({
            "type": "breach",
            "breached_by": breached_by,
            "reason": reason,
            "reported_at": datetime.utcnow(),
            "resolved": False
        })

        return True

    def amend(self, amendment: Dict[str, Any], proposed_by: str) -> bool:
        """
        Propose an amendment to the contract.

        Args:
            amendment: Amendment details
            proposed_by: Party proposing the amendment

        Returns:
            bool: Success status
        """
        if proposed_by not in self.parties:
            return False

        self.amendments.append({
            **amendment,
            "proposed_by": proposed_by,
            "proposed_at": datetime.utcnow(),
            "approved": False
        })

        return True

    def update_performance(self, metrics: Dict[str, Any]) -> bool:
        """
        Update contract performance metrics.

        Args:
            metrics: Performance metrics

        Returns:
            bool: Success status
        """
        self.performance_metrics.update(metrics)
        self.performance_metrics["last_updated"] = datetime.utcnow()
        return True

class SupplyChainDAO:
    """
    DAO for supply chain governance and management.
    """

    def __init__(self, dao_name: str, supply_chain_id: str):
        """
        Initialize the Supply Chain DAO.

        Args:
            dao_name: Name of the DAO
            supply_chain_id: Supply chain identifier
        """
        self.dao_name = dao_name
        self.supply_chain_id = supply_chain_id

        self.members: Dict[str, Dict] = {}  # address -> member_info
        self.contracts: Dict[str, SupplyChainContract] = {}
        self.inventory: Dict[str, Dict] = {}  # item_id -> inventory_info
        self.shipments: Dict[str, Dict] = {}  # shipment_id -> shipment_info

        # Governance parameters
        self.voting_quorum = 0.6  # 60% participation required
        self.voting_threshold = 0.7  # 70% approval required

    def add_member(self, address: str, role: SupplyChainRole, member_info: Dict[str, Any]) -> bool:
        """
        Add a member to the supply chain DAO.

        Args:
            address: Member address
            role: Member role in supply chain
            member_info: Additional member information

        Returns:
            bool: Success status
        """
        if address in self.members:
            return False

        self.members[address] = {
            "role": role.value,
            **member_info,
            "joined_at": datetime.utcnow(),
            "reputation_score": 100,  # Starting reputation
            "contracts_participated": 0
        }

        return True

    def create_contract(self, contract_id: str, parties: List[str], terms: Dict[str, Any],
                       auto_execute_conditions: List[Callable] = None) -> Optional[SupplyChainContract]:
        """
        Create a new supply chain contract.

        Args:
            contract_id: Contract identifier
            parties: Contract parties
            terms: Contract terms
            auto_execute_conditions: Automatic execution conditions

        Returns:
            Optional[SupplyChainContract]: Created contract
        """
        # Validate all parties are members
        for party in parties:
            if party not in self.members:
                return None

        contract = SupplyChainContract(contract_id, parties, terms, auto_execute_conditions)
        self.contracts[contract_id] = contract

        # Update member statistics
        for party in parties:
            self.members[party]["contracts_participated"] += 1

        return contract

    def track_shipment(self, shipment_id: str, origin: str, destination: str,
                      items: List[Dict], logistics_provider: str) -> bool:
        """
        Track a shipment in the supply chain.

        Args:
            shipment_id: Shipment identifier
            origin: Origin location
            destination: Destination location
            items: Items in shipment
            logistics_provider: Logistics provider address

        Returns:
            bool: Success status
        """
        if shipment_id in self.shipments:
            return False

        if logistics_provider not in self.members:
            return False

        self.shipments[shipment_id] = {
            "origin": origin,
            "destination": destination,
            "items": items,
            "logistics_provider": logistics_provider,
            "status": "in_transit",
            "created_at": datetime.utcnow(),
            "events": [{
                "event": "created",
                "timestamp": datetime.utcnow(),
                "location": origin
            }]
        }

        return True

    def update_shipment_status(self, shipment_id: str, status: str, location: str,
                              notes: str = "") -> bool:
        """
        Update shipment status.

        Args:
            shipment_id: Shipment identifier
            status: New status
            location: Current location
            notes: Additional notes

        Returns:
            bool: Success status
        """
        if shipment_id not in self.shipments:
            return False

        self.shipments[shipment_id]["status"] = status
        self.shipments[shipment_id]["events"].append({
            "event": status,
            "timestamp": datetime.utcnow(),
            "location": location,
            "notes": notes
        })

        return True

    def quality_check(self, item_id: str, check_results: Dict[str, Any]) -> bool:
        """
        Perform quality check on an item.

        Args:
            item_id: Item identifier
            check_results: Quality check results

        Returns:
            bool: Success status
        """
        if item_id not in self.inventory:
            self.inventory[item_id] = {}

        self.inventory[item_id]["quality_checks"] = self.inventory[item_id].get("quality_checks", [])
        self.inventory[item_id]["quality_checks"].append({
            **check_results,
            "checked_at": datetime.utcnow()
        })

        return True

    def resolve_dispute(self, contract_id: str, dispute_id: int, resolution: Dict[str, Any]) -> bool:
        """
        Resolve a contract dispute.

        Args:
            contract_id: Contract identifier
            dispute_id: Dispute index
            resolution: Resolution details

        Returns:
            bool: Success status
        """
        if contract_id not in self.contracts:
            return False

        contract = self.contracts[contract_id]
        if dispute_id >= len(contract.disputes):
            return False

        contract.disputes[dispute_id]["resolution"] = resolution
        contract.disputes[dispute_id]["resolved"] = True
        contract.disputes[dispute_id]["resolved_at"] = datetime.utcnow()

        return True

    def get_supply_chain_metrics(self) -> Dict[str, Any]:
        """
        Get overall supply chain performance metrics.

        Returns:
            Dict[str, Any]: Supply chain metrics
        """
        total_contracts = len(self.contracts)
        active_contracts = sum(1 for c in self.contracts.values() if c.status == ContractStatus.ACTIVE)
        completed_contracts = sum(1 for c in self.contracts.values() if c.status == ContractStatus.COMPLETED)
        breached_contracts = sum(1 for c in self.contracts.values() if c.status == ContractStatus.BREACHED)

        total_shipments = len(self.shipments)
        delivered_shipments = sum(1 for s in self.shipments.values() if s["status"] == "delivered")

        return {
            "contracts": {
                "total": total_contracts,
                "active": active_contracts,
                "completed": completed_contracts,
                "breached": breached_contracts,
                "success_rate": completed_contracts / total_contracts if total_contracts > 0 else 0
            },
            "shipments": {
                "total": total_shipments,
                "delivered": delivered_shipments,
                "on_time_delivery": delivered_shipments / total_shipments if total_shipments > 0 else 0
            },
            "members": len(self.members),
            "inventory_items": len(self.inventory)
        }

# Example usage
if __name__ == "__main__":
    # Create supply chain DAO
    dao = SupplyChainDAO("Global Supply Chain DAO", "supply_chain_001")

    # Add members
    dao.add_member("0x1234", SupplyChainRole.MANUFACTURER, {"company": "AutoCorp"})
    dao.add_member("0x5678", SupplyChainRole.SUPPLIER, {"company": "PartsInc"})
    dao.add_member("0x9abc", SupplyChainRole.LOGISTICS, {"company": "FastShip"})

    print(f"Created DAO: {dao.dao_name} with {len(dao.members)} members")

    # Create a supply chain contract
    terms = {
        "delivery_deadline": "2024-12-31",
        "payment_terms": "30 days",
        "quality_standards": "ISO 9001",
        "penalty_for_delay": 1000
    }

    contract = dao.create_contract(
        "contract_001",
        ["0x1234", "0x5678"],
        terms
    )

    if contract:
        contract.propose()
        contract.activate()
        print(f"Created and activated contract: {contract.contract_id}")

    # Track a shipment
    items = [
        {"item_id": "engine_001", "quantity": 10, "value": 50000},
        {"item_id": "transmission_001", "quantity": 10, "value": 30000}
    ]

    dao.track_shipment("shipment_001", "PartsInc Warehouse", "AutoCorp Factory", items, "0x9abc")
    print("Tracked shipment: shipment_001")

    # Update shipment status
    dao.update_shipment_status("shipment_001", "delivered", "AutoCorp Factory", "On time delivery")
    print("Updated shipment status to delivered")

    # Perform quality check
    dao.quality_check("engine_001", {
        "inspector": "0x1234",
        "result": "passed",
        "defects_found": 0,
        "compliance_score": 98
    })
    print("Performed quality check on engine_001")

    # Get metrics
    metrics = dao.get_supply_chain_metrics()
    print("Supply chain metrics:", json.dumps(metrics, indent=2, default=str))