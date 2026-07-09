class ChangeManagementWorkflow:
    def __init__(self, change_data):
        self.change_data = change_data
        self.history = []

    def manage_change(self, change):
        print(f"Managing change: {change}")
        workflow = self.create_workflow(change)
        print(f"Change management workflow: {workflow}")
        self.history.append(
            {
                "change": change,
                "workflow": workflow,
                "timestamp": datetime.datetime.now().isoformat(),
            }
        )
        return workflow

    def create_workflow(self, change):
        print("Creating change management workflow")
        # Simulate workflow creation
        return f"Workflow created for change {change}"

    def approve_change(self, change):
        print(f"Approving change: {change}")
        # Simulate change approval
        self.notify_stakeholders(change)
        return "Change approved"

    def notify_stakeholders(self, change):
        # Simulate notification to stakeholders
        print(f"Notifying stakeholders about change: {change}")
        # Example: Send email, message, or integrate with a ticketing system
        print("Stakeholders notified")

    def get_change_history(self):
        return self.history


class StaleNotificationSystem:
    def __init__(self, contact, project):
        self.contact = contact
        self.project = project
        self.update_timestamp = ""

    def check_for_status(self):
        # dummy method to check for status
        self.update_timestamp = datetime.datetime.now().isoformat()
        return "status has been updated"

    def notify(self):
        # dummy method to issue notification based on status
        return f"New Status Update on project: {self.project}, contact: {self.contact}. Status updated at: {self.update_timestamp}"
