class DataLineageAudit:
    def __init__(self, data_pipeline):
        self.data_pipeline = data_pipeline

    def track_lineage(self, data):
        print("Tracking data lineage")
        lineage = self.data_pipeline.trace(data)
        print(f"Data lineage: {lineage}")
        return lineage

    def audit_pipeline(self):
        print("Auditing data pipeline")
        audit_report = self.data_pipeline.audit()
        print(f"Audit report: {audit_report}")
        return audit_report
