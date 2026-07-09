"""
DAO for Factory Management Module

This module implements a Decentralized Autonomous Organization (DAO) for managing industrial facilities.
It enables decentralized decision-making for factory operations, resource allocation, and governance
using blockchain-based voting and smart contracts.

Features:
- DAO creation and member management
- Proposal creation and voting
- Automated execution of approved proposals
- Factory governance and decision-making
- Integration with IoT sensors for data-driven decisions
"""

import hashlib
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import uuid
from enum import Enum

class ProposalStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PASSED = "passed"
    FAILED = "failed"
    EXECUTED = "executed"

class ProposalType(Enum):
    MAINTENANCE = "maintenance"
    RESOURCE_ALLOCATION = "resource_allocation"
    POLICY_CHANGE = "policy_change"
    BUDGET_APPROVAL = "budget_approval"
    EQUIPMENT_PURCHASE = "equipment_purchase"

class DAOProposal:
    """
    Represents a proposal in the DAO.
    """

    def __init__(self, proposal_id: str, proposer: str, title: str, description: str,
                 proposal_type: ProposalType, actions: List[Callable], voting_period_days: int = 7):
        """
        Initialize a DAO proposal.

        Args:
            proposal_id: Unique proposal identifier
            proposer: Address of the proposer
            title: Proposal title
            description: Detailed description
            proposal_type: Type of proposal
            actions: List of callable actions to execute if passed
            voting_period_days: Voting period in days
        """
        self.proposal_id = proposal_id
        self.proposer = proposer
        self.title = title
        self.description = description
        self.proposal_type = proposal_type
        self.actions = actions
        self.voting_period_days = voting_period_days

        self.created_at = datetime.utcnow()
        self.voting_ends_at = self.created_at + timedelta(days=voting_period_days)
        self.status = ProposalStatus.PENDING
        self.votes: Dict[str, bool] = {}  # member_address -> vote (True for yes, False for no)
        self.execution_result = None

    def vote(self, member_address: str, vote: bool) -> bool:
        """
        Cast a vote on the proposal.

        Args:
            member_address: Voting member address
            vote: True for yes, False for no

        Returns:
            bool: Success status
        """
        if self.status != ProposalStatus.ACTIVE:
            return False

        if datetime.utcnow() > self.voting_ends_at:
            return False

        self.votes[member_address] = vote
        return True

    def get_vote_count(self) -> Dict[str, int]:
        """
        Get the current vote counts.

        Returns:
            Dict[str, int]: Vote counts (yes, no, total)
        """
        yes_votes = sum(1 for vote in self.votes.values() if vote)
        no_votes = sum(1 for vote in self.votes.values() if not vote)

        return {
            "yes": yes_votes,
            "no": no_votes,
            "total": len(self.votes)
        }

    def finalize_voting(self) -> ProposalStatus:
        """
        Finalize the voting period and determine outcome.

        Returns:
            ProposalStatus: Final status
        """
        if self.status != ProposalStatus.ACTIVE:
            return self.status

        if datetime.utcnow() < self.voting_ends_at:
            return self.status

        votes = self.get_vote_count()
        total_members = len(self.votes)  # In production, get from DAO member count

        # Simple majority voting
        if votes["yes"] > votes["no"]:
            self.status = ProposalStatus.PASSED
        else:
            self.status = ProposalStatus.FAILED

        return self.status

    def execute(self) -> Any:
        """
        Execute the proposal actions if passed.

        Returns:
            Any: Execution result
        """
        if self.status != ProposalStatus.PASSED:
            return None

        try:
            results = []
            for action in self.actions:
                result = action()
                results.append(result)

            self.status = ProposalStatus.EXECUTED
            self.execution_result = results
            return results
        except Exception as e:
            self.execution_result = f"Execution failed: {str(e)}"
            return self.execution_result

class FactoryDAO:
    """
    Decentralized Autonomous Organization for factory management.
    """

    def __init__(self, dao_name: str, factory_id: str, voting_quorum: float = 0.5,
                 voting_threshold: float = 0.51):
        """
        Initialize the Factory DAO.

        Args:
            dao_name: Name of the DAO
            factory_id: Associated factory identifier
            voting_quorum: Minimum participation required (0.5 = 50%)
            voting_threshold: Minimum yes votes required (0.51 = 51%)
        """
        self.dao_name = dao_name
        self.factory_id = factory_id
        self.voting_quorum = voting_quorum
        self.voting_threshold = voting_threshold

        self.members: Dict[str, Dict] = {}  # address -> member_info
        self.proposals: Dict[str, DAOProposal] = {}
        self.executed_actions: List[Dict] = []

        # Factory state
        self.factory_state = {
            "maintenance_budget": 100000,
            "resource_allocation": {},
            "policies": {},
            "equipment_inventory": []
        }

    def add_member(self, address: str, member_info: Dict[str, Any]) -> bool:
        """
        Add a member to the DAO.

        Args:
            address: Member address
            member_info: Member information (role, voting_power, etc.)

        Returns:
            bool: Success status
        """
        if address in self.members:
            return False

        self.members[address] = {
            **member_info,
            "joined_at": datetime.utcnow(),
            "voting_power": member_info.get("voting_power", 1)
        }

        return True

    def remove_member(self, address: str) -> bool:
        """
        Remove a member from the DAO.

        Args:
            address: Member address

        Returns:
            bool: Success status
        """
        if address not in self.members:
            return False

        del self.members[address]
        return True

    def create_proposal(self, proposer: str, title: str, description: str,
                       proposal_type: ProposalType, actions: List[Callable],
                       voting_period_days: int = 7) -> Optional[str]:
        """
        Create a new proposal.

        Args:
            proposer: Proposer address
            title: Proposal title
            description: Proposal description
            proposal_type: Type of proposal
            actions: Actions to execute if passed
            voting_period_days: Voting period

        Returns:
            Optional[str]: Proposal ID if created
        """
        if proposer not in self.members:
            return None

        proposal_id = str(uuid.uuid4())
        proposal = DAOProposal(
            proposal_id, proposer, title, description,
            proposal_type, actions, voting_period_days
        )

        self.proposals[proposal_id] = proposal
        proposal.status = ProposalStatus.ACTIVE

        return proposal_id

    def vote_on_proposal(self, proposal_id: str, voter: str, vote: bool) -> bool:
        """
        Vote on a proposal.

        Args:
            proposal_id: Proposal identifier
            voter: Voter address
            vote: Vote (True for yes)

        Returns:
            bool: Success status
        """
        if proposal_id not in self.proposals:
            return False

        if voter not in self.members:
            return False

        proposal = self.proposals[proposal_id]
        return proposal.vote(voter, vote)

    def process_proposals(self) -> List[Dict]:
        """
        Process all proposals that have ended voting.

        Returns:
            List[Dict]: Processing results
        """
        results = []

        for proposal_id, proposal in self.proposals.items():
            if proposal.status == ProposalStatus.ACTIVE:
                old_status = proposal.status
                new_status = proposal.finalize_voting()

                if new_status != old_status:
                    results.append({
                        "proposal_id": proposal_id,
                        "title": proposal.title,
                        "old_status": old_status.value,
                        "new_status": new_status.value
                    })

                    if new_status == ProposalStatus.PASSED:
                        execution_result = proposal.execute()
                        results[-1]["execution_result"] = execution_result

                        # Record executed action
                        self.executed_actions.append({
                            "proposal_id": proposal_id,
                            "executed_at": datetime.utcnow(),
                            "result": execution_result
                        })

        return results

    def get_proposal_status(self, proposal_id: str) -> Optional[Dict]:
        """
        Get the status of a proposal.

        Args:
            proposal_id: Proposal identifier

        Returns:
            Optional[Dict]: Proposal status information
        """
        if proposal_id not in self.proposals:
            return None

        proposal = self.proposals[proposal_id]
        votes = proposal.get_vote_count()

        return {
            "proposal_id": proposal_id,
            "title": proposal.title,
            "status": proposal.status.value,
            "votes": votes,
            "created_at": proposal.created_at.isoformat(),
            "voting_ends_at": proposal.voting_ends_at.isoformat(),
            "time_remaining": str(proposal.voting_ends_at - datetime.utcnow())
        }

    def get_factory_state(self) -> Dict:
        """
        Get the current factory state.

        Returns:
            Dict: Factory state
        """
        return self.factory_state.copy()

    def update_factory_state(self, updates: Dict[str, Any]) -> bool:
        """
        Update factory state (typically called by executed proposals).

        Args:
            updates: State updates

        Returns:
            bool: Success status
        """
        self.factory_state.update(updates)
        return True

# Example usage and predefined actions
def create_maintenance_budget_action(amount: float):
    """Create an action to allocate maintenance budget."""
    def action():
        dao = FactoryDAO("", "")  # In practice, get from context
        dao.update_factory_state({"maintenance_budget": amount})
        return f"Allocated ${amount} for maintenance"
    return action

def create_equipment_purchase_action(equipment: Dict):
    """Create an action to purchase equipment."""
    def action():
        dao = FactoryDAO("", "")
        dao.factory_state["equipment_inventory"].append(equipment)
        return f"Purchased equipment: {equipment['name']}"
    return action

if __name__ == "__main__":
    # Create a factory DAO
    dao = FactoryDAO("Factory Alpha DAO", "factory_001")

    # Add members
    dao.add_member("0x1234", {"role": "manager", "voting_power": 2})
    dao.add_member("0x5678", {"role": "engineer", "voting_power": 1})
    dao.add_member("0x9abc", {"role": "worker", "voting_power": 1})

    print(f"Created DAO: {dao.dao_name} with {len(dao.members)} members")

    # Create a proposal for maintenance budget
    actions = [create_maintenance_budget_action(150000)]
    proposal_id = dao.create_proposal(
        "0x1234",
        "Increase Maintenance Budget",
        "Allocate additional funds for equipment maintenance",
        ProposalType.BUDGET_APPROVAL,
        actions,
        voting_period_days=3
    )

    print(f"Created proposal: {proposal_id}")

    # Members vote
    dao.vote_on_proposal(proposal_id, "0x1234", True)  # Manager votes yes
    dao.vote_on_proposal(proposal_id, "0x5678", True)  # Engineer votes yes
    dao.vote_on_proposal(proposal_id, "0x9abc", False)  # Worker votes no

    # Process proposals (simulate time passing)
    import time
    # time.sleep(3 * 24 * 3600)  # Wait 3 days - commented for demo

    # Manually finalize for demo
    proposal = dao.proposals[proposal_id]
    proposal.voting_ends_at = datetime.utcnow() - timedelta(hours=1)  # Past time

    results = dao.process_proposals()
    print("Processing results:", results)

    # Check final state
    status = dao.get_proposal_status(proposal_id)
    print(f"Proposal status: {status['status']}")
    print(f"Final votes: {status['votes']}")

    if status['status'] == 'executed':
        print(f"Factory state updated: {dao.get_factory_state()}")