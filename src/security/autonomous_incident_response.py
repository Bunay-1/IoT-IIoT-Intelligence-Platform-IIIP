import json
import os
import uuid
from datetime import datetime
from collections import defaultdict
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

class AutonomousIncidentResponse:
    def __init__(self, data_file="incident_response_data.json"):
        self.data_file = data_file
        self.incidents = {}
        self.knowledge_base = {}
        self.remediation_rules = {}
        self.model = None
        self.label_encoders = {}
        self._load_data()

    def _load_data(self):
        """Loads data from the JSON file or initializes a default structure."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.incidents = data.get('incidents', {})
                    self.knowledge_base = data.get('knowledge_base', {})
                    self.remediation_rules = data.get('remediation_rules', {})
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading data: {e}. Initializing with default data.")
                self._initialize_default_data()
        else:
            self._initialize_default_data()

    def _save_data(self):
        """Saves the current state to the JSON file."""
        data = {
            'incidents': self.incidents,
            'knowledge_base': self.knowledge_base,
            'remediation_rules': self.remediation_rules
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)

    def _initialize_default_data(self):
        """Initializes the system with some sample data."""
        self.remediation_rules = {
            "High CPU Usage": "restart_service",
            "Database Connection Error": "check_db_credentials",
            "Unauthorized Access Attempt": "block_ip"
        }
        # Sample incidents for initial training
        self.incidents = {
            "inc-001": {"type": "performance", "source": "server-01", "details": "CPU usage > 95%", "severity": "high", "category": "High CPU Usage", "resolved": True},
            "inc-002": {"type": "security", "source": "firewall", "details": "Multiple failed login attempts from 192.168.1.100", "severity": "critical", "category": "Unauthorized Access Attempt", "resolved": True},
            "inc-003": {"type": "database", "source": "db-main", "details": "Cannot connect to database", "severity": "high", "category": "Database Connection Error", "resolved": True},
        }
        self._save_data()

    def log_incident(self, incident_type: str, source: str, details: str):
        """Logs a new incident in the system."""
        incident_id = f"inc-{uuid.uuid4().hex[:6]}"
        self.incidents[incident_id] = {
            "type": incident_type,
            "source": source,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "status": "open",
            "severity": "unknown",
            "category": "uncategorized",
            "resolved": False
        }
        print(f"New incident logged: {incident_id} - {details}")
        self._save_data()
        return incident_id

    def learn_from_incident(self, incident_id: str, root_cause: str, resolution_steps: list):
        """
        Updates the knowledge base with learnings from a resolved incident.
        """
        if incident_id not in self.incidents:
            print("Error: Cannot learn from an unknown incident.")
            return

        incident = self.incidents[incident_id]
        category = incident.get('category', 'uncategorized')

        if category not in self.knowledge_base:
            self.knowledge_base[category] = {
                "count": 0,
                "root_causes": defaultdict(int),
                "effective_resolutions": defaultdict(int)
            }

        kb_entry = self.knowledge_base[category]
        kb_entry["count"] += 1
        kb_entry["root_causes"][root_cause] += 1
        for step in resolution_steps:
            kb_entry["effective_resolutions"][step] += 1

        print(f"Knowledge base updated based on incident {incident_id}.")
        self._save_data()

    def train_prediction_model(self):
        """
        Trains a classification model to predict incident category and severity.
        """
        historical_incidents = [inc for inc in self.incidents.values() if inc.get('resolved')]

        if len(historical_incidents) < 2:
            print("Not enough historical data to train a model.")
            return

        # Prepare data for training
        features = [f"{inc['type']} {inc['source']}" for inc in historical_incidents]

        # Encode categorical features and target variables
        self.label_encoders['features'] = LabelEncoder().fit(features)
        X = self.label_encoders['features'].transform(features)

        targets_cat = [inc['category'] for inc in historical_incidents]
        self.label_encoders['category'] = LabelEncoder().fit(targets_cat)
        y_cat = self.label_encoders['category'].transform(targets_cat)

        targets_sev = [inc['severity'] for inc in historical_incidents]
        self.label_encoders['severity'] = LabelEncoder().fit(targets_sev)
        y_sev = self.label_encoders['severity'].transform(targets_sev)

        # Combine targets for a multi-output model
        y = np.array([y_cat, y_sev]).T

        # Simple train-test split
        X_train, _, y_train, _ = train_test_split(X.reshape(-1, 1), y, test_size=0.1, random_state=42)

        if X_train.shape[0] == 0:
            print("Not enough training data after split.")
            return

        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        print("Incident prediction model trained successfully.")

    def analyze_incident(self, incident_id: str):
        """
        Analyzes an incident using the ML model and knowledge base.
        """
        if incident_id not in self.incidents:
            return {"error": "Incident not found."}

        incident = self.incidents[incident_id]

        if self.model:
            # Predict category and severity
            feature_str = f"{incident['type']} {incident['source']}"

            # Handle unseen labels by adding them to the encoder
            if feature_str not in self.label_encoders['features'].classes_:
                 self.label_encoders['features'].classes_ = np.append(self.label_encoders['features'].classes_, feature_str)

            X_pred = self.label_encoders['features'].transform([feature_str]).reshape(1, -1)

            prediction = self.model.predict(X_pred)[0]

            predicted_category = self.label_encoders['category'].inverse_transform([prediction[0]])[0]
            predicted_severity = self.label_encoders['severity'].inverse_transform([prediction[1]])[0]

            incident['category'] = predicted_category
            incident['severity'] = predicted_severity
            print(f"ML Model Prediction for {incident_id}: Category='{predicted_category}', Severity='{predicted_severity}'")
        else:
            print("Model not trained. Using default analysis.")

        # Suggest remediation from knowledge base or rules
        suggested_plan = "No suggestion available."
        if incident['category'] in self.knowledge_base:
            resolutions = self.knowledge_base[incident['category']]['effective_resolutions']
            if resolutions:
                suggested_plan = max(resolutions, key=resolutions.get)
        elif incident['category'] in self.remediation_rules:
            suggested_plan = self.remediation_rules[incident['category']]

        incident['suggested_plan'] = suggested_plan
        self._save_data()

        return incident

    def determine_escalation(self, incident_id: str):
        """
        Determines if an incident needs to be escalated to a human operator.

        Args:
            incident_id (str): The ID of the incident to check.

        Returns:
            bool: True if escalation is needed, False otherwise.
        """
        if incident_id not in self.incidents:
            return True # Escalate if incident is not found

        incident = self.incidents[incident_id]

        # Escalate if severity is critical
        if incident.get('severity') == 'critical':
            print(f"Escalation required for {incident_id}: Critical severity.")
            incident['status'] = 'escalated'
            self._save_data()
            return True

        # Escalate if no remediation plan is suggested
        if incident.get('suggested_plan') == "No suggestion available.":
            print(f"Escalation required for {incident_id}: No suggested remediation plan.")
            incident['status'] = 'escalated'
            self._save_data()
            return True

        print(f"No escalation required for {incident_id}.")
        return False

    def execute_remediation_plan(self, incident_id: str):
        """
        Executes the suggested remediation plan for an incident.
        """
        if incident_id not in self.incidents:
            print(f"Cannot execute plan for unknown incident {incident_id}.")
            return False

        incident = self.incidents[incident_id]
        plan = incident.get('suggested_plan')

        if not plan or plan == "No suggestion available.":
            print(f"No actionable plan for {incident_id}.")
            return False

        print(f"Executing remediation plan '{plan}' for incident {incident_id}...")

        # --- Simulation of remediation actions ---
        success = False
        if plan == "restart_service":
            print(f"  -> Restarting service on {incident['source']}...")
            success = True
        elif plan == "block_ip":
            ip_address = incident['details'].split(" ")[-1]
            print(f"  -> Blocking IP address {ip_address} on firewall...")
            success = True
        elif plan == "check_db_credentials":
            print(f"  -> Verifying database credentials on {incident['source']}...")
            success = True
        else:
            print(f"  -> Unknown plan: '{plan}'. Cannot execute.")

        if success:
            incident['status'] = 'resolved'
            incident['resolved'] = True
            incident['resolution_timestamp'] = datetime.now().isoformat()
            print(f"Incident {incident_id} resolved successfully.")

            # This is a good place to trigger learning
            self.learn_from_incident(
                incident_id=incident_id,
                root_cause="Inferred from category", # Simplified for simulation
                resolution_steps=[plan]
            )
        else:
            incident['status'] = 'resolution_failed'
            print(f"Remediation plan failed for {incident_id}. Escalation might be needed.")

        self._save_data()
        return success

if __name__ == '__main__':
    print("--- Autonomous Incident Response System Simulation ---")

    # Use a temporary file for the simulation
    sim_data_file = "temp_incident_data.json"
    if os.path.exists(sim_data_file):
        os.remove(sim_data_file)

    airs = AutonomousIncidentResponse(data_file=sim_data_file)

    print("\n--- Step 1: Initial Model Training ---")
    airs.train_prediction_model()

    print("\n--- Step 2: New Incidents Occur ---")
    inc1 = airs.log_incident("performance", "server-02", "CPU usage > 98%")
    inc2 = airs.log_incident("security", "firewall", "Unauthorized access from 10.0.0.5")
    inc3 = airs.log_incident("application", "api-gateway", "503 Service Unavailable errors")

    print("\n--- Step 3: Autonomous Analysis and Response ---")
    incidents_to_process = [inc1, inc2, inc3]
    for inc_id in incidents_to_process:
        print(f"\n--- Processing Incident: {inc_id} ---")

        # 1. Analyze the incident
        analysis = airs.analyze_incident(inc_id)
        if "error" in analysis:
            print(analysis['error'])
            continue

        # 2. Determine if escalation is needed
        if not airs.determine_escalation(inc_id):
            # 3. If not escalated, execute remediation
            airs.execute_remediation_plan(inc_id)
        else:
            print(f"Incident {inc_id} has been escalated for manual review.")

    print("\n--- Step 4: System State After Initial Response ---")
    for inc_id, details in airs.incidents.items():
        if not details.get("resolved", False):
            print(f" - {inc_id}: Status='{details['status']}', Severity='{details['severity']}', Category='{details['category']}'")

    print("\n--- Step 5: Manual Resolution and Learning ---")
    # Simulate a manual resolution for the escalated incident
    escalated_incident_id = inc3
    airs.incidents[escalated_incident_id]['category'] = "Application Error" # Manually categorized
    airs.incidents[escalated_incident_id]['resolved'] = True
    print(f"Simulating manual resolution for {escalated_incident_id}...")
    airs.learn_from_incident(
        incident_id=escalated_incident_id,
        root_cause="Upstream service failure",
        resolution_steps=["restart_api_gateway", "check_upstream_services"]
    )

    print("\n--- Step 6: Retraining the Model with New Data ---")
    airs.train_prediction_model()

    print("\n--- Final Knowledge Base State ---")
    print(json.dumps(airs.knowledge_base, indent=2))

    print("\n--- Simulation Finished ---")
    # Clean up the temporary file
    if os.path.exists(sim_data_file):
        os.remove(sim_data_file)
