import random
from typing import Dict, List, Any
from datetime import datetime, timedelta
import pandas as pd

from fastapi import FastAPI

app = FastAPI()

# Mock data for multi-tenant KPIs
tenants = ["tenant1", "tenant2", "tenant3"]
kpis = {
    "tenant1": {"uptime": 99.5, "latency": 20, "error_rate": 0.1},
    "tenant2": {"uptime": 98.8, "latency": 25, "error_rate": 0.2},
    "tenant3": {"uptime": 99.2, "latency": 15, "error_rate": 0.15},
}


class MultiTenantKPISegregation:
    """Multi-tenant KPI segregation and management system."""

    def __init__(self):
        self.tenants = tenants
        self.kpis = kpis
        self.kpi_history = self._generate_kpi_history()

    def _generate_kpi_history(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate historical KPI data for each tenant."""
        history = {}
        for tenant in self.tenants:
            history[tenant] = []
            for i in range(30):  # Last 30 days
                timestamp = (datetime.now() - timedelta(days=i)).isoformat()
                base_kpis = self.kpis[tenant]
                # Add some variation
                history[tenant].append({
                    "timestamp": timestamp,
                    "uptime": base_kpis["uptime"] + random.uniform(-1, 1),
                    "latency": base_kpis["latency"] + random.uniform(-5, 5),
                    "error_rate": max(0, base_kpis["error_rate"] + random.uniform(-0.05, 0.05))
                })
        return history

    def get_tenant_kpis(self, tenant_id: str) -> Dict[str, Any]:
        """Get current KPIs for a specific tenant."""
        if tenant_id not in self.kpis:
            raise ValueError(f"Tenant {tenant_id} not found")

        return {
            "tenant_id": tenant_id,
            "current_kpis": self.kpis[tenant_id],
            "kpi_history": self.kpi_history[tenant_id][-7:],  # Last 7 days
            "performance_score": self._calculate_performance_score(tenant_id)
        }

    def _calculate_performance_score(self, tenant_id: str) -> float:
        """Calculate overall performance score for a tenant."""
        kpis = self.kpis[tenant_id]
        # Simple weighted score
        uptime_score = kpis["uptime"] / 100
        latency_score = max(0, 1 - (kpis["latency"] / 100))  # Lower latency is better
        error_score = max(0, 1 - kpis["error_rate"])

        return (uptime_score * 0.5 + latency_score * 0.3 + error_score * 0.2) * 100

    def get_all_tenants_summary(self) -> Dict[str, Any]:
        """Get summary of all tenants' KPIs."""
        summary = {
            "total_tenants": len(self.tenants),
            "tenant_summaries": [],
            "overall_stats": {
                "avg_uptime": 0,
                "avg_latency": 0,
                "avg_error_rate": 0
            }
        }

        total_uptime = 0
        total_latency = 0
        total_error_rate = 0

        for tenant in self.tenants:
            tenant_summary = self.get_tenant_kpis(tenant)
            summary["tenant_summaries"].append(tenant_summary)

            kpis = tenant_summary["current_kpis"]
            total_uptime += kpis["uptime"]
            total_latency += kpis["latency"]
            total_error_rate += kpis["error_rate"]

        summary["overall_stats"]["avg_uptime"] = total_uptime / len(self.tenants)
        summary["overall_stats"]["avg_latency"] = total_latency / len(self.tenants)
        summary["overall_stats"]["avg_error_rate"] = total_error_rate / len(self.tenants)

        return summary

    def compare_tenants(self, tenant_ids: List[str]) -> Dict[str, Any]:
        """Compare KPIs between multiple tenants."""
        if not tenant_ids:
            raise ValueError("At least one tenant must be specified")

        comparison = {
            "compared_tenants": tenant_ids,
            "kpi_comparison": {},
            "rankings": {}
        }

        # Compare each KPI
        kpi_types = ["uptime", "latency", "error_rate"]
        for kpi_type in kpi_types:
            comparison["kpi_comparison"][kpi_type] = {}
            values = []

            for tenant_id in tenant_ids:
                if tenant_id in self.kpis:
                    value = self.kpis[tenant_id][kpi_type]
                    comparison["kpi_comparison"][kpi_type][tenant_id] = value
                    values.append((tenant_id, value))

            # Rank tenants for this KPI
            if kpi_type in ["uptime"]:  # Higher is better
                values.sort(key=lambda x: x[1], reverse=True)
            else:  # Lower is better
                values.sort(key=lambda x: x[1])

            comparison["rankings"][kpi_type] = [tenant for tenant, _ in values]

        return comparison

    def get_tenant_alerts(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get alerts for a specific tenant based on KPI thresholds."""
        if tenant_id not in self.kpis:
            raise ValueError(f"Tenant {tenant_id} not found")

        alerts = []
        kpis = self.kpis[tenant_id]

        # Check uptime
        if kpis["uptime"] < 99.0:
            alerts.append({
                "type": "warning",
                "metric": "uptime",
                "value": kpis["uptime"],
                "threshold": 99.0,
                "message": f"Uptime below threshold: {kpis['uptime']}%"
            })

        # Check latency
        if kpis["latency"] > 50:
            alerts.append({
                "type": "warning",
                "metric": "latency",
                "value": kpis["latency"],
                "threshold": 50,
                "message": f"Latency above threshold: {kpis['latency']}ms"
            })

        # Check error rate
        if kpis["error_rate"] > 0.5:
            alerts.append({
                "type": "critical",
                "metric": "error_rate",
                "value": kpis["error_rate"],
                "threshold": 0.5,
                "message": f"Error rate above threshold: {kpis['error_rate']}%"
            })

        return alerts


@app.get("/kpis/{tenant_id}")
async def get_kpis(tenant_id: str):
    if tenant_id in kpis:
        return {"tenant": tenant_id, "kpis": kpis[tenant_id]}
    else:
        return {"error": "Tenant not found"}


# Example endpoint
@app.get("/")
async def root():
    return {"message": "Multi-Tenant KPI Segregation"}
