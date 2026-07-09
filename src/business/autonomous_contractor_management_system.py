import json
import os
import uuid
from datetime import datetime

class AutonomousContractorManagementSystem:
    """
    A sophisticated system for autonomously managing contractors, projects,
    contracts, and payments.
    """
    def __init__(self, data_file="contractor_data.json"):
        self.data_file = data_file
        self.contractors = {}
        self.contracts = {}
        self.projects = {}
        self.payment_history = []
        self._load_data()

    def _load_data(self):
        """Loads data from the JSON file or initializes a default structure."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.contractors = data.get('contractors', {})
                    self.contracts = data.get('contracts', {})
                    self.projects = data.get('projects', {})
                    self.payment_history = data.get('payment_history', [])
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading data: {e}. Starting with a clean slate.")
                self._initialize_default_data()
        else:
            self._initialize_default_data()

    def _save_data(self):
        """Saves the current state to the JSON file."""
        data = {
            'contractors': self.contractors,
            'contracts': self.contracts,
            'projects': self.projects,
            'payment_history': self.payment_history
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)

    def _initialize_default_data(self):
        """Initializes the system with some sample contractors."""
        self.contractors = {
            "c-001": {
                "name": "Alice Johnson",
                "skills": ["python", "machine_learning", "data_analysis"],
                "rating": 4.8,
                "hourly_rate": 75,
                "status": "available",
                "bank_info": {"account": "ALICE-IBAN-123"}
            },
            "c-002": {
                "name": "Bob Williams",
                "skills": ["javascript", "react", "nodejs"],
                "rating": 4.5,
                "hourly_rate": 65,
                "status": "available",
                "bank_info": {"account": "BOB-IBAN-456"}
            },
            "c-003": {
                "name": "Charlie Brown",
                "skills": ["project_management", "agile", "scrum"],
                "rating": 4.9,
                "hourly_rate": 90,
                "status": "busy",
                "bank_info": {"account": "CHARLIE-IBAN-789"}
            }
        }
        self._save_data()

    def find_suitable_contractors(self, required_skills: list, min_rating: float = 4.0):
        """
        Finds available contractors who meet the skill and rating requirements.

        Args:
            required_skills (list): A list of skills required for the task.
            min_rating (float): The minimum acceptable rating for a contractor.

        Returns:
            list: A list of contractor IDs who are suitable for the task,
                  sorted by rating in descending order.
        """
        suitable_contractors = []
        for contractor_id, details in self.contractors.items():
            if details['status'] == 'available':
                if all(skill in details['skills'] for skill in required_skills):
                    if details['rating'] >= min_rating:
                        suitable_contractors.append((contractor_id, details['rating']))

        # Sort by rating (descending)
        suitable_contractors.sort(key=lambda x: x[1], reverse=True)
        return [cid for cid, rating in suitable_contractors]

    def create_contract(self, contractor_id: str, project_id: str, scope: str, total_value: float):
        """
        Creates a new contract for a contractor and a project.

        Args:
            contractor_id (str): The ID of the contractor.
            project_id (str): The ID of the project.
            scope (str): A description of the work to be done.
            total_value (float): The total value of the contract.

        Returns:
            str: The ID of the newly created contract, or None if creation failed.
        """
        if contractor_id not in self.contractors or project_id not in self.projects:
            print("Error: Invalid contractor or project ID.")
            return None

        contract_id = f"contract-{uuid.uuid4().hex[:6]}"
        self.contracts[contract_id] = {
            "contractor_id": contractor_id,
            "project_id": project_id,
            "scope": scope,
            "total_value": total_value,
            "status": "active",
            "start_date": datetime.now().isoformat()
        }

        # Update contractor and project status
        self.contractors[contractor_id]['status'] = 'busy'
        self.projects[project_id]['contractor_id'] = contractor_id

        self._save_data()
        print(f"Contract {contract_id} created for {self.contractors[contractor_id]['name']}.")
        return contract_id

    def terminate_contract(self, contract_id: str):
        """
        Terminates an active contract.

        Args:
            contract_id (str): The ID of the contract to terminate.

        Returns:
            bool: True if termination was successful, False otherwise.
        """
        if contract_id in self.contracts and self.contracts[contract_id]['status'] == 'active':
            contract = self.contracts[contract_id]
            contractor_id = contract['contractor_id']

            contract['status'] = 'terminated'
            contract['end_date'] = datetime.now().isoformat()

            # Make contractor available again
            self.contractors[contractor_id]['status'] = 'available'

            self._save_data()
            print(f"Contract {contract_id} has been terminated.")
            return True
        print(f"Error: Contract {contract_id} cannot be terminated.")
        return False

    def create_project(self, title: str, budget: float):
        """
        Creates a new project.

        Args:
            title (str): The title of the project.
            budget (float): The total budget for the project.

        Returns:
            str: The ID of the newly created project.
        """
        project_id = f"proj-{uuid.uuid4().hex[:6]}"
        self.projects[project_id] = {
            "title": title,
            "budget": budget,
            "tasks": {},
            "status": "pending",
            "contractor_id": None
        }
        self._save_data()
        print(f"Project '{title}' created with ID {project_id}.")
        return project_id

    def assign_task(self, project_id: str, task_description: str, value: float):
        """
        Assigns a new task to a project.

        Args:
            project_id (str): The ID of the project.
            task_description (str): Description of the task.
            value (float): The payment value for completing the task.

        Returns:
            str: The ID of the newly created task, or None if failed.
        """
        if project_id not in self.projects:
            print("Error: Invalid project ID.")
            return None

        task_id = f"task-{uuid.uuid4().hex[:6]}"
        self.projects[project_id]['tasks'][task_id] = {
            "description": task_description,
            "value": value,
            "status": "pending"
        }
        self._save_data()
        print(f"Task '{task_description}' added to project {project_id}.")
        return task_id

    def complete_task(self, project_id: str, task_id: str):
        """
        Marks a task as completed and triggers payment processing.

        Args:
            project_id (str): The ID of the project.
            task_id (str): The ID of the task.

        Returns:
            bool: True if the task was completed successfully, False otherwise.
        """
        if project_id in self.projects and task_id in self.projects[project_id]['tasks']:
            task = self.projects[project_id]['tasks'][task_id]
            if task['status'] == 'pending':
                task['status'] = 'completed'
                print(f"Task {task_id} in project {project_id} marked as completed.")

                # Trigger payment processing for this task
                contractor_id = self.projects[project_id].get('contractor_id')
                if contractor_id:
                    self.process_payment(contractor_id, task['value'], f"Payment for task: {task['description']}")

                self._save_data()
                return True
        print(f"Error: Could not complete task {task_id}.")
        return False

    def process_payment(self, contractor_id: str, amount: float, reason: str):
        """
        Processes a payment to a contractor and records it in the history.

        Args:
            contractor_id (str): The ID of the contractor to be paid.
            amount (float): The amount to be paid.
            reason (str): The reason for the payment.

        Returns:
            bool: True if payment was processed successfully, False otherwise.
        """
        if contractor_id not in self.contractors:
            print(f"Error: Contractor {contractor_id} not found for payment.")
            return False

        contractor = self.contractors[contractor_id]
        bank_info = contractor.get("bank_info", {})

        if not bank_info.get("account"):
            print(f"Error: Missing bank information for {contractor['name']}.")
            return False

        print(f"Processing payment of ${amount:.2f} to {contractor['name']} ({bank_info['account']}) for: {reason}")

        payment_record = {
            "payment_id": f"pay-{uuid.uuid4().hex[:8]}",
            "contractor_id": contractor_id,
            "amount": amount,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }
        self.payment_history.append(payment_record)
        self._save_data()

        print("Payment successfully processed and recorded.")
        return True

if __name__ == '__main__':
    # --- Simulation ---
    print("--- Initializing Autonomous Contractor Management System ---")
    # Using a temporary file for the simulation to avoid overwriting default data
    simulation_data_file = "temp_contractor_data.json"
    if os.path.exists(simulation_data_file):
        os.remove(simulation_data_file)

    acms = AutonomousContractorManagementSystem(data_file=simulation_data_file)

    print("\n--- Step 1: Find a suitable contractor for a new web development project ---")
    required_skills = ["javascript", "react"]
    suitable_contractors = acms.find_suitable_contractors(required_skills, min_rating=4.5)

    if not suitable_contractors:
        print("No suitable contractors found. Simulation cannot proceed.")
    else:
        top_contractor_id = suitable_contractors[0]
        print(f"Found best match: {acms.contractors[top_contractor_id]['name']} (Rating: {acms.contractors[top_contractor_id]['rating']})")

        print("\n--- Step 2: Create a new project and a contract ---")
        project_id = acms.create_project("E-commerce Platform Frontend", budget=5000)
        contract_id = acms.create_contract(
            contractor_id=top_contractor_id,
            project_id=project_id,
            scope="Develop and deploy the main user interface for the new e-commerce platform.",
            total_value=4500
        )

        if contract_id:
            print("\n--- Step 3: Assign and complete tasks ---")
            task1_id = acms.assign_task(project_id, "Develop login and registration pages", 500)
            task2_id = acms.assign_task(project_id, "Create product display components", 1000)
            task3_id = acms.assign_task(project_id, "Implement shopping cart functionality", 1500)

            print("\nSimulating task completion...")
            acms.complete_task(project_id, task1_id)
            acms.complete_task(project_id, task2_id)

            print("\n--- Step 4: Review Payment History ---")
            print("Current payment history:")
            for payment in acms.payment_history:
                print(f"- {payment['timestamp']}: Paid ${payment['amount']:.2f} to {acms.contractors[payment['contractor_id']]['name']} for '{payment['reason']}'")

            print("\n--- Step 5: Terminate the contract (example) ---")
            acms.terminate_contract(contract_id)
            print(f"Status of contractor {acms.contractors[top_contractor_id]['name']}: {acms.contractors[top_contractor_id]['status']}")

    print("\n--- Simulation Finished ---")
    # Clean up the temporary file
    if os.path.exists(simulation_data_file):
        os.remove(simulation_data_file)
