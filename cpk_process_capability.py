"""
CPK Process Capability Module

This module implements process capability analysis using CPK and other
statistical process control metrics for manufacturing quality management.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats

from utils.logging_config import LoggerMixin
from utils.performance_monitor import monitor_operation
from utils.security import SecurityError, input_validator, validate_input


class ProcessCapabilityError(Exception):
    """Base exception for process capability errors."""
    pass


class InsufficientDataError(ProcessCapabilityError):
    """Raised when insufficient data for analysis."""
    pass


class CPKProcessCapability(LoggerMixin):
    """
    Process Capability Analysis using CPK and statistical methods.

    This class provides comprehensive process capability analysis including:
    - CPK calculation and interpretation
    - Process performance metrics
    - Capability indices (Cp, Cpk, Pp, Ppk)
    - Distribution analysis
    - Out-of-control detection
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Process Capability analyzer.

        Args:
            config: Configuration dictionary with analysis parameters
        """
        self.config = config or self._get_default_config()

        # Analysis history and metrics
        self.capability_history: List[Dict[str, Any]] = []
        self.process_metrics: Dict[str, Any] = {}

        self.logger.info("CPK Process Capability analyzer initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "min_samples": 30,  # Minimum samples for reliable analysis
            "confidence_level": 0.95,  # Confidence level for intervals
            "capability_target": 1.33,  # Target CPK value
            "subgroup_size": 5,  # For control charts
            "distribution_test_alpha": 0.05,  # Significance level for normality test
            "auto_update_interval": 3600,  # 1 hour
            "alert_thresholds": {
                "cpk_low": 1.0,
                "cpk_critical": 0.8
            }
        }

    @validate_input({
        "process_data": {
            "type": "object",
            "required": True
        },
        "specifications": {
            "type": "object",
            "required": True
        }
    })
    @monitor_operation("cpk_process_capability.analyze_capability")
    async def analyze_capability(
        self,
        process_data: Union[pd.DataFrame, List[float], np.ndarray],
        specifications: Dict[str, Any],
        process_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze process capability using CPK and related metrics.

        Args:
            process_data: Process measurement data
            specifications: Process specifications (LSL, USL, target)
            process_name: Optional name for the process

        Returns:
            Comprehensive capability analysis results

        Raises:
            InsufficientDataError: If data is insufficient for analysis
            ProcessCapabilityError: If analysis fails
        """
        try:
            self.logger.info(f"Analyzing process capability for {process_name or 'unnamed process'}")

            # Convert data to numpy array
            data = self._prepare_data(process_data)

            # Validate data sufficiency
            await self._validate_data_sufficiency(data, specifications)

            # Extract specifications
            lsl = specifications.get("lsl")
            usl = specifications.get("usl")
            target = specifications.get("target")

            # Calculate basic statistics
            basic_stats = self._calculate_basic_statistics(data)

            # Test for normality
            normality_test = self._test_normality(data)

            # Calculate capability indices
            capability_indices = self._calculate_capability_indices(
                data, lsl, usl, target, basic_stats
            )

            # Calculate process performance
            performance_metrics = self._calculate_performance_metrics(
                data, lsl, usl, basic_stats
            )

            # Generate recommendations
            recommendations = self._generate_capability_recommendations(
                capability_indices, normality_test, basic_stats
            )

            # Check for alerts
            alerts = self._check_capability_alerts(capability_indices)

            # Update history
            self._update_capability_history(
                process_name or "unnamed",
                capability_indices,
                basic_stats,
                alerts
            )

            result = {
                "process_name": process_name,
                "timestamp": datetime.now().isoformat(),
                "specifications": {
                    "lsl": lsl,
                    "usl": usl,
                    "target": target,
                    "nominal_tolerance": usl - lsl if lsl is not None and usl is not None else None
                },
                "basic_statistics": basic_stats,
                "normality_test": normality_test,
                "capability_indices": capability_indices,
                "performance_metrics": performance_metrics,
                "recommendations": recommendations,
                "alerts": alerts,
                "data_summary": {
                    "sample_size": len(data),
                    "data_range": [float(np.min(data)), float(np.max(data))],
                    "outliers_detected": self._detect_outliers(data)
                }
            }

            self.logger.info(
                f"Capability analysis completed for {process_name or 'unnamed'}. "
                f"CPK: {capability_indices.get('cpk', 'N/A'):.3f}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Capability analysis failed: {e}")
            raise ProcessCapabilityError(f"Failed to analyze capability: {e}") from e

    def _prepare_data(self, data: Union[pd.DataFrame, List[float], np.ndarray]) -> np.ndarray:
        """Prepare data for analysis."""
        try:
            if isinstance(data, pd.DataFrame):
                # Assume first column or 'value' column
                if 'value' in data.columns:
                    data_array = data['value'].values
                else:
                    data_array = data.iloc[:, 0].values
            elif isinstance(data, list):
                data_array = np.array(data)
            elif isinstance(data, np.ndarray):
                data_array = data
            else:
                raise ValueError("Unsupported data format")

            # Remove NaN values
            data_array = data_array[~np.isnan(data_array)]

            return data_array

        except Exception as e:
            raise ProcessCapabilityError(f"Data preparation failed: {e}") from e

    async def _validate_data_sufficiency(
        self,
        data: np.ndarray,
        specifications: Dict[str, Any]
    ) -> None:
        """Validate that data is sufficient for capability analysis."""
        min_samples = self.config["min_samples"]

        if len(data) < min_samples:
            raise InsufficientDataError(
                f"Insufficient data: {len(data)} samples, minimum required: {min_samples}"
            )

        # Check for specifications
        has_lsl = specifications.get("lsl") is not None
        has_usl = specifications.get("usl") is not None

        if not (has_lsl or has_usl):
            raise ProcessCapabilityError("At least one specification limit (LSL or USL) must be provided")

        # Check for constant data
        if np.std(data) == 0:
            raise ProcessCapabilityError("Data has no variation (constant values)")

    def _calculate_basic_statistics(self, data: np.ndarray) -> Dict[str, Any]:
        """Calculate basic statistical measures."""
        try:
            return {
                "mean": float(np.mean(data)),
                "median": float(np.median(data)),
                "std_dev": float(np.std(data, ddof=1)),  # Sample standard deviation
                "variance": float(np.var(data, ddof=1)),
                "skewness": float(stats.skew(data)),
                "kurtosis": float(stats.kurtosis(data)),
                "min": float(np.min(data)),
                "max": float(np.max(data)),
                "range": float(np.max(data) - np.min(data)),
                "quartiles": {
                    "q1": float(np.percentile(data, 25)),
                    "q3": float(np.percentile(data, 75))
                },
                "iqr": float(np.percentile(data, 75) - np.percentile(data, 25))
            }

        except Exception as e:
            self.logger.warning(f"Basic statistics calculation failed: {e}")
            return {}

    def _test_normality(self, data: np.ndarray) -> Dict[str, Any]:
        """Test if data follows normal distribution."""
        try:
            # Shapiro-Wilk test for normality
            if len(data) <= 5000:  # Shapiro test limit
                statistic, p_value = stats.shapiro(data)
                test_name = "shapiro"
            else:
                # Use Kolmogorov-Smirnov test for larger samples
                statistic, p_value = stats.kstest(data, 'norm',
                    args=(np.mean(data), np.std(data, ddof=1)))
                test_name = "kolmogorov-smirnov"

            alpha = self.config["distribution_test_alpha"]
            is_normal = p_value > alpha

            return {
                "test_name": test_name,
                "statistic": float(statistic),
                "p_value": float(p_value),
                "is_normal": is_normal,
                "alpha": alpha,
                "interpretation": "Data appears normally distributed" if is_normal
                               else "Data does not appear normally distributed"
            }

        except Exception as e:
            self.logger.warning(f"Normality test failed: {e}")
            return {"test_name": "failed", "error": str(e)}

    def _calculate_capability_indices(
        self,
        data: np.ndarray,
        lsl: Optional[float],
        usl: Optional[float],
        target: Optional[float],
        basic_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate process capability indices."""
        try:
            mean = basic_stats["mean"]
            sigma = basic_stats["std_dev"]

            indices = {}

            # Calculate Cp (Process Capability)
            if lsl is not None and usl is not None:
                tolerance = usl - lsl
                indices["cp"] = tolerance / (6 * sigma) if sigma > 0 else float('inf')

            # Calculate Cpk (Process Capability Index)
            if lsl is not None and usl is not None:
                cpu = (usl - mean) / (3 * sigma) if sigma > 0 else float('inf')
                cpl = (mean - lsl) / (3 * sigma) if sigma > 0 else float('inf')
                indices["cpk"] = min(cpu, cpl)
                indices["cpu"] = cpu
                indices["cpl"] = cpl

            # Calculate Pp (Process Performance)
            if lsl is not None and usl is not None:
                tolerance = usl - lsl
                sigma_overall = np.std(data, ddof=1)  # Overall standard deviation
                indices["pp"] = tolerance / (6 * sigma_overall) if sigma_overall > 0 else float('inf')

            # Calculate Ppk (Process Performance Index)
            if lsl is not None and usl is not None:
                sigma_overall = np.std(data, ddof=1)
                ppu = (usl - mean) / (3 * sigma_overall) if sigma_overall > 0 else float('inf')
                ppl = (mean - lsl) / (3 * sigma_overall) if sigma_overall > 0 else float('inf')
                indices["ppk"] = min(ppu, ppl)
                indices["ppu"] = ppu
                indices["ppl"] = ppl

            # Calculate Cpm (Taguchi capability index) if target is provided
            if target is not None and lsl is not None and usl is not None:
                tolerance = usl - lsl
                cpm = tolerance / (6 * np.sqrt(sigma**2 + (mean - target)**2)) if sigma > 0 else float('inf')
                indices["cpm"] = cpm

            # Convert to float and handle inf
            for key, value in indices.items():
                if isinstance(value, (np.floating, float)):
                    indices[key] = float(value) if not np.isinf(value) else None

            return indices

        except Exception as e:
            self.logger.warning(f"Capability indices calculation failed: {e}")
            return {}

    def _calculate_performance_metrics(
        self,
        data: np.ndarray,
        lsl: Optional[float],
        usl: Optional[float],
        basic_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate process performance metrics."""
        try:
            metrics = {}

            # Percentage of data within specifications
            if lsl is not None and usl is not None:
                within_specs = np.sum((data >= lsl) & (data <= usl))
                metrics["yield"] = float(within_specs / len(data))
                metrics["defect_rate"] = 1.0 - metrics["yield"]

            # PPM (Parts Per Million) defective
            if "defect_rate" in metrics:
                metrics["ppm_defective"] = metrics["defect_rate"] * 1000000

            # Process centering
            if lsl is not None and usl is not None:
                target = (lsl + usl) / 2
                metrics["centering"] = abs(basic_stats["mean"] - target) / ((usl - lsl) / 2)

            # Process spread
            if lsl is not None and usl is not None:
                tolerance = usl - lsl
                process_spread = 6 * basic_stats["std_dev"]
                metrics["spread_ratio"] = process_spread / tolerance if tolerance > 0 else float('inf')

            return metrics

        except Exception as e:
            self.logger.warning(f"Performance metrics calculation failed: {e}")
            return {}

    def _generate_capability_recommendations(
        self,
        capability_indices: Dict[str, Any],
        normality_test: Dict[str, Any],
        basic_stats: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on capability analysis."""
        recommendations = []

        try:
            cpk = capability_indices.get("cpk")

            if cpk is None:
                recommendations.append("Unable to calculate CPK - check specifications and data")
                return recommendations

            # CPK-based recommendations
            if cpk < 0.8:
                recommendations.append("CRITICAL: Process is not capable - immediate action required")
                recommendations.append("Review process controls and reduce variation")
            elif cpk < 1.0:
                recommendations.append("Process capability is marginal - improvement needed")
                recommendations.append("Consider process optimization and control implementation")
            elif cpk < 1.33:
                recommendations.append("Process is capable but can be improved")
                recommendations.append("Monitor process and implement continuous improvement")
            else:
                recommendations.append("Process is well-capable - maintain current controls")

            # Normality recommendations
            if not normality_test.get("is_normal", True):
                recommendations.append("Data does not follow normal distribution - consider transformation or alternative methods")

            # Centering recommendations
            centering = basic_stats.get("centering", 0)
            if centering > 0.1:
                recommendations.append("Process may be off-center - check for systematic errors")

            # Variation recommendations
            spread_ratio = capability_indices.get("spread_ratio", 1)
            if spread_ratio > 1.5:
                recommendations.append("High process variation detected - focus on reducing variability")

        except Exception as e:
            self.logger.warning(f"Recommendation generation failed: {e}")
            recommendations = ["Review process capability analysis results"]

        return recommendations

    def _check_capability_alerts(self, capability_indices: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for capability-related alerts."""
        alerts = []

        try:
            cpk = capability_indices.get("cpk")
            if cpk is not None:
                thresholds = self.config["alert_thresholds"]

                if cpk <= thresholds["cpk_critical"]:
                    alerts.append({
                        "level": "critical",
                        "message": f"Critical CPK value: {cpk:.3f} - process out of control",
                        "action_required": True
                    })
                elif cpk <= thresholds["cpk_low"]:
                    alerts.append({
                        "level": "warning",
                        "message": f"Low CPK value: {cpk:.3f} - process needs attention",
                        "action_required": False
                    })

        except Exception as e:
            self.logger.warning(f"Alert checking failed: {e}")

        return alerts

    def _detect_outliers(self, data: np.ndarray, method: str = "iqr") -> int:
        """Detect outliers in the data."""
        try:
            if method == "iqr":
                q1, q3 = np.percentile(data, [25, 75])
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outliers = np.sum((data < lower_bound) | (data > upper_bound))
                return int(outliers)
            else:
                # Z-score method
                z_scores = np.abs(stats.zscore(data))
                return int(np.sum(z_scores > 3))

        except Exception as e:
            self.logger.warning(f"Outlier detection failed: {e}")
            return 0

    def _update_capability_history(
        self,
        process_name: str,
        capability_indices: Dict[str, Any],
        basic_stats: Dict[str, Any],
        alerts: List[Dict[str, Any]]
    ) -> None:
        """Update capability analysis history."""
        try:
            history_entry = {
                "process_name": process_name,
                "timestamp": datetime.now().isoformat(),
                "cpk": capability_indices.get("cpk"),
                "mean": basic_stats.get("mean"),
                "std_dev": basic_stats.get("std_dev"),
                "alerts_count": len(alerts),
                "alerts": alerts
            }

            self.capability_history.append(history_entry)

            # Keep only recent history (last 100 entries)
            if len(self.capability_history) > 100:
                self.capability_history = self.capability_history[-100:]

        except Exception as e:
            self.logger.warning(f"History update failed: {e}")

    @monitor_operation("cpk_process_capability.get_capability_report")
    def get_capability_report(
        self,
        process_name: Optional[str] = None,
        time_range_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get comprehensive capability report."""
        try:
            # Filter history if needed
            history = self.capability_history
            if process_name:
                history = [h for h in history if h["process_name"] == process_name]

            if time_range_hours:
                cutoff_time = datetime.now().timestamp() - (time_range_hours * 3600)
                history = [h for h in history if datetime.fromisoformat(h["timestamp"]).timestamp() > cutoff_time]

            # Calculate trends
            trends = self._calculate_capability_trends(history)

            return {
                "summary": {
                    "total_analyses": len(history),
                    "processes_analyzed": len(set(h["process_name"] for h in history)),
                    "alerts_generated": sum(h["alerts_count"] for h in history)
                },
                "trends": trends,
                "recent_history": history[-10:],  # Last 10 analyses
                "config": self.config,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            return {"error": str(e)}

    def _calculate_capability_trends(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate capability trends from history."""
        try:
            if not history:
                return {}

            cpk_values = [h["cpk"] for h in history if h["cpk"] is not None]

            if not cpk_values:
                return {}

            return {
                "cpk_trend": {
                    "current": cpk_values[-1] if cpk_values else None,
                    "average": float(np.mean(cpk_values)),
                    "min": float(np.min(cpk_values)),
                    "max": float(np.max(cpk_values)),
                    "trend_direction": "improving" if len(cpk_values) > 1 and cpk_values[-1] > cpk_values[0] else "declining"
                },
                "analysis_count": len(history),
                "time_span": self._calculate_time_span(history)
            }

        except Exception as e:
            self.logger.warning(f"Trend calculation failed: {e}")
            return {}

    def _calculate_time_span(self, history: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate time span of history in hours."""
        try:
            if len(history) < 2:
                return None

            timestamps = [datetime.fromisoformat(h["timestamp"]).timestamp() for h in history]
            return (max(timestamps) - min(timestamps)) / 3600

        except Exception:
            return None