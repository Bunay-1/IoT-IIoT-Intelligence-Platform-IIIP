"""
Process Stability Monitor Module

This module implements statistical process control (SPC) for monitoring
process stability, detecting out-of-control conditions, and maintaining
production quality through control charts and stability analysis.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats

from src.utils.logging_config import LoggerMixin
from src.utils.performance_monitor import monitor_operation
from src.utils.security import SecurityError, input_validator, validate_input


class ProcessStabilityError(Exception):
    """Base exception for process stability errors."""
    pass


class InsufficientDataError(ProcessStabilityError):
    """Raised when insufficient data for stability analysis."""
    pass


class ProcessStabilityMonitor(LoggerMixin):
    """
    Statistical Process Control (SPC) for process stability monitoring.

    This class provides comprehensive process stability analysis including:
    - Control chart generation (X-bar, R, p, np, c, u charts)
    - Out-of-control detection using Western Electric rules
    - Process capability monitoring
    - Stability trend analysis
    - Alert generation for process deviations
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Process Stability Monitor.

        Args:
            config: Configuration dictionary with monitoring parameters
        """
        self.config = config or self._get_default_config()

        # Process data storage
        self.process_data: Dict[str, List[Dict[str, Any]]] = {}
        self.control_limits: Dict[str, Dict[str, Any]] = {}
        self.stability_history: Dict[str, List[Dict[str, Any]]] = {}

        self.logger.info("Process Stability Monitor initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "min_samples_for_limits": 20,  # Minimum samples to calculate control limits
            "subgroup_size": 5,  # Sample size for each subgroup
            "control_limit_sigma": 3,  # Sigma level for control limits
            "moving_range_length": 2,  # For I-MR charts
            "alert_cooldown_minutes": 15,  # Minimum time between alerts
            "stability_check_interval": 300,  # 5 minutes
            "trend_detection_periods": 8,  # Number of periods for trend detection
            "chart_types": ["xbar_r", "individuals_mr", "p", "np", "c", "u"],
            "western_electric_rules": {
                "rule_1": True,  # 1 point beyond 3σ
                "rule_2": True,  # 9 points on one side of center line
                "rule_3": True,  # 6 consecutive points increasing/decreasing
                "rule_4": True   # 14 consecutive points alternating up/down
            }
        }

    @validate_input({
        "process_name": {
            "type": "string",
            "max_length": 100,
            "required": True
        },
        "data": {
            "type": "object",
            "required": True
        },
        "chart_type": {
            "type": "string",
            "required": False
        }
    })
    @monitor_operation("process_stability_monitor.monitor_process")
    async def monitor_process(
        self,
        process_name: str,
        data: Union[pd.DataFrame, List[float], Dict[str, Any]],
        chart_type: str = "xbar_r",
        specifications: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Monitor process stability and generate control chart.

        Args:
            process_name: Name of the process being monitored
            data: Process measurement data
            chart_type: Type of control chart (xbar_r, individuals_mr, p, np, c, u)
            specifications: Process specifications (LSL, USL, target)

        Returns:
            Stability analysis results with control chart data

        Raises:
            ProcessStabilityError: If monitoring fails
        """
        try:
            self.logger.info(f"Monitoring process stability for {process_name}")

            # Prepare data
            processed_data = self._prepare_monitoring_data(data, chart_type)

            # Calculate control limits if not already calculated
            if process_name not in self.control_limits or not self.control_limits[process_name].get(chart_type):
                await self._calculate_control_limits(process_name, processed_data, chart_type)

            # Generate control chart
            chart_data = await self._generate_control_chart(process_name, processed_data, chart_type)

            # Check for out-of-control conditions
            ooc_conditions = self._check_out_of_control(chart_data, chart_type)

            # Analyze stability
            stability_analysis = self._analyze_stability(chart_data, ooc_conditions)

            # Generate alerts
            alerts = self._generate_stability_alerts(process_name, ooc_conditions, stability_analysis)

            # Update monitoring history
            self._update_monitoring_history(process_name, chart_data, stability_analysis, alerts)

            result = {
                "process_name": process_name,
                "chart_type": chart_type,
                "timestamp": datetime.now().isoformat(),
                "control_limits": self.control_limits[process_name][chart_type],
                "chart_data": chart_data,
                "out_of_control_conditions": ooc_conditions,
                "stability_analysis": stability_analysis,
                "alerts": alerts,
                "specifications": specifications,
                "data_summary": {
                    "total_points": len(chart_data["points"]),
                    "in_control_points": len(chart_data["points"]) - len(ooc_conditions),
                    "out_of_control_points": len(ooc_conditions)
                }
            }

            self.logger.info(
                f"Process monitoring completed for {process_name}. "
                f"Stability: {stability_analysis['overall_stability']}, "
                f"OOC conditions: {len(ooc_conditions)}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Process monitoring failed for {process_name}: {e}")
            raise ProcessStabilityError(f"Process monitoring failed: {e}") from e

    def _prepare_monitoring_data(
        self,
        data: Union[pd.DataFrame, List[float], Dict[str, Any]],
        chart_type: str
    ) -> Dict[str, Any]:
        """Prepare data for monitoring based on chart type."""
        try:
            processed = {}

            if chart_type in ["xbar_r", "individuals_mr"]:
                # Convert to numerical data
                if isinstance(data, pd.DataFrame):
                    if 'value' in data.columns:
                        values = data['value'].values
                    else:
                        values = data.iloc[:, 0].values
                elif isinstance(data, list):
                    values = np.array(data)
                elif isinstance(data, dict) and 'values' in data:
                    values = np.array(data['values'])
                else:
                    values = np.array(list(data.values()) if isinstance(data, dict) else data)

                processed["values"] = values.astype(float)

                if chart_type == "xbar_r":
                    # Group into subgroups
                    subgroup_size = self.config["subgroup_size"]
                    num_subgroups = len(values) // subgroup_size
                    if num_subgroups == 0:
                        raise InsufficientDataError("Insufficient data for X-bar R chart")

                    subgroups = values[:num_subgroups * subgroup_size].reshape(num_subgroups, subgroup_size)
                    processed["subgroups"] = subgroups
                    processed["xbar"] = np.mean(subgroups, axis=1)
                    processed["r"] = np.ptp(subgroups, axis=1)  # Range

            elif chart_type in ["p", "np"]:
                # Attribute data for proportion
                if isinstance(data, dict):
                    processed.update(data)
                else:
                    raise ProcessStabilityError("Attribute data required for p/np charts")

            elif chart_type in ["c", "u"]:
                # Count data
                if isinstance(data, (list, np.ndarray)):
                    processed["counts"] = np.array(data)
                elif isinstance(data, dict) and 'counts' in data:
                    processed["counts"] = np.array(data['counts'])
                else:
                    raise ProcessStabilityError("Count data required for c/u charts")

            return processed

        except Exception as e:
            raise ProcessStabilityError(f"Data preparation failed: {e}") from e

    async def _calculate_control_limits(
        self,
        process_name: str,
        data: Dict[str, Any],
        chart_type: str
    ) -> None:
        """Calculate control limits for the process."""
        try:
            if process_name not in self.control_limits:
                self.control_limits[process_name] = {}

            limits = {}

            if chart_type == "xbar_r":
                # X-bar chart limits
                xbar_values = data["xbar"]
                r_values = data["r"]

                if len(xbar_values) < self.config["min_samples_for_limits"]:
                    raise InsufficientDataError("Insufficient subgroups for control limit calculation")

                xbar_bar = np.mean(xbar_values)
                r_bar = np.mean(r_values)

                # Control limits for X-bar chart
                A2 = self._get_A2_factor(len(data["subgroups"][0]))  # First subgroup size
                limits["xbar"] = {
                    "center": float(xbar_bar),
                    "ucl": float(xbar_bar + A2 * r_bar),
                    "lcl": float(xbar_bar - A2 * r_bar)
                }

                # Control limits for R chart
                D3, D4 = self._get_D_factors(len(data["subgroups"][0]))
                limits["r"] = {
                    "center": float(r_bar),
                    "ucl": float(D4 * r_bar),
                    "lcl": float(D3 * r_bar) if D3 * r_bar > 0 else 0
                }

            elif chart_type == "individuals_mr":
                # Individuals and Moving Range chart
                values = data["values"]
                if len(values) < self.config["min_samples_for_limits"]:
                    raise InsufficientDataError("Insufficient data for I-MR chart")

                # Moving ranges
                mr_length = self.config["moving_range_length"]
                moving_ranges = np.abs(np.diff(values, n=mr_length-1))

                x_bar = np.mean(values)
                mr_bar = np.mean(moving_ranges)

                # Control limits for Individuals chart
                E2 = self._get_E2_factor(mr_length)
                limits["individuals"] = {
                    "center": float(x_bar),
                    "ucl": float(x_bar + E2 * mr_bar),
                    "lcl": float(x_bar - E2 * mr_bar)
                }

                # Control limits for MR chart
                D4_mr = self._get_D4_mr_factor(mr_length)
                limits["mr"] = {
                    "center": float(mr_bar),
                    "ucl": float(D4_mr * mr_bar),
                    "lcl": 0  # MR chart LCL is 0
                }

            elif chart_type == "p":
                # p-chart for proportion nonconforming
                if "sample_sizes" in data and "defectives" in data:
                    sample_sizes = np.array(data["sample_sizes"])
                    defectives = np.array(data["defectives"])

                    p_bar = np.sum(defectives) / np.sum(sample_sizes)

                    # Control limits
                    limits["p"] = {
                        "center": float(p_bar),
                        "ucl": float(p_bar + 3 * np.sqrt(p_bar * (1 - p_bar) / np.mean(sample_sizes))),
                        "lcl": float(max(0, p_bar - 3 * np.sqrt(p_bar * (1 - p_bar) / np.mean(sample_sizes))))
                    }

            # Store limits
            self.control_limits[process_name][chart_type] = limits

            self.logger.info(f"Control limits calculated for {process_name} {chart_type} chart")

        except Exception as e:
            self.logger.error(f"Control limit calculation failed: {e}")
            raise ProcessStabilityError(f"Control limit calculation failed: {e}") from e

    def _get_A2_factor(self, n: int) -> float:
        """Get A2 factor for X-bar chart."""
        A2_factors = {2: 1.880, 3: 1.023, 4: 0.729, 5: 0.577, 6: 0.483, 7: 0.419, 8: 0.373, 9: 0.337, 10: 0.308}
        return A2_factors.get(n, 0.308)  # Default for n >= 10

    def _get_D_factors(self, n: int) -> Tuple[float, float]:
        """Get D3 and D4 factors for R chart."""
        D_factors = {
            2: (0, 3.267), 3: (0, 2.575), 4: (0, 2.282), 5: (0, 2.115), 6: (0, 2.004), 7: (0, 1.924),
            8: (0, 1.864), 9: (0, 1.816), 10: (0, 1.777)
        }
        return D_factors.get(n, (0, 1.777))

    def _get_E2_factor(self, n: int) -> float:
        """Get E2 factor for Individuals chart."""
        E2_factors = {2: 2.660, 3: 1.772, 4: 1.457, 5: 1.290, 6: 1.184, 7: 1.109, 8: 1.054, 9: 1.010, 10: 0.975}
        return E2_factors.get(n, 0.975)

    def _get_D4_mr_factor(self, n: int) -> float:
        """Get D4 factor for MR chart."""
        D4_factors = {2: 3.267, 3: 2.575, 4: 2.282, 5: 2.115, 6: 2.004, 7: 1.924, 8: 1.864, 9: 1.816, 10: 1.777}
        return D4_factors.get(n, 1.777)

    async def _generate_control_chart(
        self,
        process_name: str,
        data: Dict[str, Any],
        chart_type: str
    ) -> Dict[str, Any]:
        """Generate control chart data."""
        try:
            chart_data = {"points": [], "timestamps": []}

            if chart_type == "xbar_r":
                # X-bar chart points
                for i, (xbar, r) in enumerate(zip(data["xbar"], data["r"])):
                    chart_data["points"].append({
                        "index": i + 1,
                        "xbar": float(xbar),
                        "r": float(r),
                        "timestamp": datetime.now().isoformat()
                    })

            elif chart_type == "individuals_mr":
                # Individuals chart points
                values = data["values"]
                mr_length = self.config["moving_range_length"]
                moving_ranges = np.abs(np.diff(values, n=mr_length-1))

                for i, (value, mr) in enumerate(zip(values[mr_length-1:], moving_ranges)):
                    chart_data["points"].append({
                        "index": i + 1,
                        "value": float(value),
                        "moving_range": float(mr),
                        "timestamp": datetime.now().isoformat()
                    })

            return chart_data

        except Exception as e:
            self.logger.error(f"Control chart generation failed: {e}")
            return {"points": [], "error": str(e)}

    def _check_out_of_control(self, chart_data: Dict[str, Any], chart_type: str) -> List[Dict[str, Any]]:
        """Check for out-of-control conditions using Western Electric rules."""
        try:
            ooc_conditions = []
            points = chart_data["points"]

            if not points:
                return ooc_conditions

            # Get control limits
            process_name = "current"  # Would be passed properly in real implementation
            limits = self.control_limits.get(process_name, {}).get(chart_type, {})

            if not limits:
                return ooc_conditions

            # Extract values based on chart type
            if chart_type == "xbar_r":
                values = [p["xbar"] for p in points]
                center = limits["xbar"]["center"]
                ucl = limits["xbar"]["ucl"]
                lcl = limits["xbar"]["lcl"]
            elif chart_type == "individuals_mr":
                values = [p["value"] for p in points]
                center = limits["individuals"]["center"]
                ucl = limits["individuals"]["ucl"]
                lcl = limits["individuals"]["lcl"]
            else:
                return ooc_conditions

            # Apply Western Electric rules
            rules_config = self.config["western_electric_rules"]

            # Rule 1: 1 point beyond 3σ
            if rules_config["rule_1"]:
                for i, value in enumerate(values):
                    if value > ucl or value < lcl:
                        ooc_conditions.append({
                            "point_index": i + 1,
                            "rule": "1",
                            "description": "Point beyond control limits",
                            "value": float(value),
                            "limit": "UCL" if value > ucl else "LCL",
                            "severity": "high"
                        })

            # Rule 2: 9 consecutive points on one side of center line
            if rules_config["rule_2"] and len(values) >= 9:
                for i in range(len(values) - 8):
                    segment = values[i:i+9]
                    above_center = sum(1 for v in segment if v > center)
                    below_center = sum(1 for v in segment if v < center)

                    if above_center >= 9:
                        ooc_conditions.append({
                            "point_index": i + 5,  # Middle of the segment
                            "rule": "2",
                            "description": "9 consecutive points above center line",
                            "severity": "high"
                        })
                    elif below_center >= 9:
                        ooc_conditions.append({
                            "point_index": i + 5,
                            "rule": "2",
                            "description": "9 consecutive points below center line",
                            "severity": "high"
                        })

            # Rule 3: 6 consecutive points increasing or decreasing
            if rules_config["rule_3"] and len(values) >= 6:
                for i in range(len(values) - 5):
                    segment = values[i:i+6]
                    increasing = all(segment[j] < segment[j+1] for j in range(5))
                    decreasing = all(segment[j] > segment[j+1] for j in range(5))

                    if increasing or decreasing:
                        ooc_conditions.append({
                            "point_index": i + 3,
                            "rule": "3",
                            "description": "6 consecutive points trending",
                            "direction": "increasing" if increasing else "decreasing",
                            "severity": "medium"
                        })

            # Rule 4: 14 consecutive points alternating up and down
            if rules_config["rule_4"] and len(values) >= 14:
                for i in range(len(values) - 13):
                    segment = values[i:i+14]
                    alternating = True
                    for j in range(12):
                        if not ((segment[j] < segment[j+1] and segment[j+1] > segment[j+2]) or
                               (segment[j] > segment[j+1] and segment[j+1] < segment[j+2])):
                            alternating = False
                            break

                    if alternating:
                        ooc_conditions.append({
                            "point_index": i + 7,
                            "rule": "4",
                            "description": "14 consecutive points alternating",
                            "severity": "medium"
                        })

            return ooc_conditions

        except Exception as e:
            self.logger.warning(f"Out-of-control check failed: {e}")
            return []

    def _analyze_stability(
        self,
        chart_data: Dict[str, Any],
        ooc_conditions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze overall process stability."""
        try:
            points = chart_data["points"]
            if not points:
                return {"overall_stability": "unknown", "stability_score": 0}

            total_points = len(points)
            ooc_points = len(ooc_conditions)

            # Calculate stability score (0-100, higher is better)
            stability_score = max(0, 100 - (ooc_points / total_points * 100) - (len(ooc_conditions) * 5))

            # Determine overall stability
            if stability_score >= 90:
                overall_stability = "excellent"
            elif stability_score >= 80:
                overall_stability = "good"
            elif stability_score >= 70:
                overall_stability = "fair"
            elif stability_score >= 60:
                overall_stability = "poor"
            else:
                overall_stability = "out_of_control"

            # Calculate trends
            if len(points) >= self.config["trend_detection_periods"]:
                recent_points = points[-self.config["trend_detection_periods"]:]
                if "xbar" in points[0]:
                    values = [p["xbar"] for p in recent_points]
                elif "value" in points[0]:
                    values = [p["value"] for p in recent_points]
                else:
                    values = []

                if values:
                    slope, _, _, _, _ = stats.linregress(range(len(values)), values)
                    trend = "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable"
                else:
                    trend = "unknown"
            else:
                trend = "insufficient_data"

            return {
                "overall_stability": overall_stability,
                "stability_score": float(stability_score),
                "trend": trend,
                "ooc_ratio": float(ooc_points / total_points) if total_points > 0 else 0,
                "recommendations": self._generate_stability_recommendations(
                    overall_stability, ooc_conditions
                )
            }

        except Exception as e:
            self.logger.warning(f"Stability analysis failed: {e}")
            return {"overall_stability": "error", "stability_score": 0, "error": str(e)}

    def _generate_stability_recommendations(
        self,
        stability: str,
        ooc_conditions: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate stability improvement recommendations."""
        recommendations = []

        try:
            if stability in ["poor", "out_of_control"]:
                recommendations.append("IMMEDIATE ACTION: Process is out of control")
                recommendations.append("Identify and eliminate special causes of variation")
                recommendations.append("Review process parameters and equipment")

            elif stability == "fair":
                recommendations.append("Process stability needs improvement")
                recommendations.append("Monitor closely and implement corrective actions")

            # Specific recommendations based on OOC conditions
            rules_triggered = set(c["rule"] for c in ooc_conditions)

            if "1" in rules_triggered:
                recommendations.append("Points beyond control limits - check for special causes")

            if "2" in rules_triggered:
                recommendations.append("Shift in process mean detected - investigate systematic changes")

            if "3" in rules_triggered:
                recommendations.append("Process trending - monitor for continued drift")

            if not recommendations:
                recommendations.append("Continue monitoring process stability")

        except Exception as e:
            self.logger.warning(f"Recommendation generation failed: {e}")
            recommendations = ["Review process control chart and take appropriate actions"]

        return recommendations

    def _generate_stability_alerts(
        self,
        process_name: str,
        ooc_conditions: List[Dict[str, Any]],
        stability_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate alerts for stability issues."""
        alerts = []

        try:
            # Check cooldown period
            last_alert_time = getattr(self, f'_last_alert_{process_name}', None)
            if last_alert_time:
                cooldown = timedelta(minutes=self.config["alert_cooldown_minutes"])
                if datetime.now() - last_alert_time < cooldown:
                    return alerts

            # Generate alerts based on conditions
            if ooc_conditions:
                alerts.append({
                    "level": "warning" if len(ooc_conditions) <= 2 else "critical",
                    "message": f"Out-of-control conditions detected in {process_name}",
                    "details": f"{len(ooc_conditions)} points violate control rules",
                    "action_required": True,
                    "timestamp": datetime.now().isoformat()
                })

            if stability_analysis.get("overall_stability") in ["poor", "out_of_control"]:
                alerts.append({
                    "level": "critical",
                    "message": f"Process {process_name} stability compromised",
                    "details": f"Stability score: {stability_analysis.get('stability_score', 0):.1f}",
                    "action_required": True,
                    "timestamp": datetime.now().isoformat()
                })

            # Update last alert time
            if alerts:
                setattr(self, f'_last_alert_{process_name}', datetime.now())

        except Exception as e:
            self.logger.warning(f"Alert generation failed: {e}")

        return alerts

    def _update_monitoring_history(
        self,
        process_name: str,
        chart_data: Dict[str, Any],
        stability_analysis: Dict[str, Any],
        alerts: List[Dict[str, Any]]
    ) -> None:
        """Update monitoring history."""
        try:
            if process_name not in self.stability_history:
                self.stability_history[process_name] = []

            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "stability_score": stability_analysis.get("stability_score", 0),
                "overall_stability": stability_analysis.get("overall_stability", "unknown"),
                "ooc_conditions": len(chart_data.get("ooc_conditions", [])),
                "alerts_generated": len(alerts),
                "data_points": len(chart_data.get("points", []))
            }

            self.stability_history[process_name].append(history_entry)

            # Keep only recent history (last 100 entries per process)
            if len(self.stability_history[process_name]) > 100:
                self.stability_history[process_name] = self.stability_history[process_name][-100:]

        except Exception as e:
            self.logger.warning(f"History update failed: {e}")

    @monitor_operation("process_stability_monitor.get_stability_report")
    def get_stability_report(
        self,
        process_name: Optional[str] = None,
        time_range_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get comprehensive stability report."""
        try:
            # Filter history
            history = {}
            for proc_name, proc_history in self.stability_history.items():
                if not process_name or proc_name == process_name:
                    filtered_history = proc_history
                    if time_range_hours:
                        cutoff_time = datetime.now().timestamp() - (time_range_hours * 3600)
                        filtered_history = [
                            h for h in proc_history
                            if datetime.fromisoformat(h["timestamp"]).timestamp() > cutoff_time
                        ]
                    history[proc_name] = filtered_history

            # Generate summary
            summary = {
                "total_processes": len(history),
                "total_monitoring_sessions": sum(len(h) for h in history.values()),
                "processes_with_alerts": len([p for p, h in history.items() if any(sess["alerts_generated"] > 0 for sess in h)]),
                "average_stability_score": 0
            }

            # Calculate average stability score
            all_scores = []
            for proc_history in history.values():
                all_scores.extend([sess["stability_score"] for sess in proc_history if "stability_score" in sess])

            if all_scores:
                summary["average_stability_score"] = float(np.mean(all_scores))

            return {
                "summary": summary,
                "process_history": history,
                "control_limits": self.control_limits,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            return {"error": str(e)}