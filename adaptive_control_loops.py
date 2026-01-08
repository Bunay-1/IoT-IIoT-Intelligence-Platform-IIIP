"""
Module: Adaptive Control Loops

This module implements adaptive control systems for industrial processes.
It provides PID controller optimization, adaptive tuning algorithms, and
real-time parameter adjustment based on process feedback.
"""

import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from config import settings
from utils.logging_config import LoggerMixin
from utils.performance_monitor import monitor_operation
from utils.security import SecurityError, input_validator, validate_input

# Import core ML engines for integration
try:
    from automl_engine import automl_engine
    from reinforcement_learning import rl_engine

    AUTOML_AVAILABLE = True
    RL_AVAILABLE = True
except ImportError:
    AUTOML_AVAILABLE = False
    RL_AVAILABLE = False
    # Logger will be available after class definition


class ControlMode(Enum):
    """Enumeration of control modes."""

    MANUAL = "manual"
    AUTOMATIC = "automatic"
    CASCADE = "cascade"
    ADAPTIVE = "adaptive"


@dataclass
class PIDParameters:
    """PID controller parameters."""

    kp: float
    ki: float
    kd: float
    setpoint: float = 0.0
    output_limits: Tuple[float, float] = (-100.0, 100.0)
    integral_limits: Tuple[float, float] = (-100.0, 100.0)


@dataclass
class ControlPerformance:
    """Control loop performance metrics."""

    timestamp: datetime
    setpoint: float
    process_variable: float
    control_output: float
    error: float
    integral_error: float
    derivative_error: float
    settling_time: Optional[float] = None
    overshoot: Optional[float] = None
    steady_state_error: Optional[float] = None
    oscillation_frequency: Optional[float] = None


class AdaptiveControlError(Exception):
    """Base exception for AdaptiveControlLoops module."""

    pass


class InvalidPIDParametersError(AdaptiveControlError):
    """Raised when PID parameters are invalid."""

    pass


class ControlInstabilityError(AdaptiveControlError):
    """Raised when control loop becomes unstable."""

    pass


class AdvancedTuningEngine:
    """Advanced PID tuning algorithms."""

    def __init__(self):
        self.tuning_history = []

    def genetic_algorithm_tuning(self, loop_id: str, bounds: Dict[str, Tuple[float, float]],
                                generations: int = 50, population_size: int = 20) -> PIDParameters:
        """Use genetic algorithm for PID tuning."""
        # Simplified GA implementation
        population = []
        for _ in range(population_size):
            individual = {
                'kp': np.random.uniform(bounds['kp'][0], bounds['kp'][1]),
                'ki': np.random.uniform(bounds['ki'][0], bounds['ki'][1]),
                'kd': np.random.uniform(bounds['kd'][0], bounds['kd'][1])
            }
            population.append(individual)

        # Mock fitness evaluation
        for individual in population:
            individual['fitness'] = np.random.random()  # Replace with actual evaluation

        best = max(population, key=lambda x: x['fitness'])
        return PIDParameters(**best)

    def particle_swarm_tuning(self, loop_id: str, bounds: Dict[str, Tuple[float, float]],
                             iterations: int = 100, swarm_size: int = 30) -> PIDParameters:
        """Use particle swarm optimization for PID tuning."""
        # Simplified PSO implementation
        swarm = []
        for _ in range(swarm_size):
            particle = {
                'position': {
                    'kp': np.random.uniform(bounds['kp'][0], bounds['kp'][1]),
                    'ki': np.random.uniform(bounds['ki'][0], bounds['ki'][1]),
                    'kd': np.random.uniform(bounds['kd'][0], bounds['kd'][1])
                },
                'velocity': {'kp': 0, 'ki': 0, 'kd': 0},
                'best_position': None,
                'best_fitness': float('-inf')
            }
            swarm.append(particle)

        global_best = None
        global_best_fitness = float('-inf')

        for _ in range(iterations):
            for particle in swarm:
                # Mock fitness evaluation
                fitness = np.random.random()

                if fitness > particle['best_fitness']:
                    particle['best_fitness'] = fitness
                    particle['best_position'] = particle['position'].copy()

                if fitness > global_best_fitness:
                    global_best_fitness = fitness
                    global_best = particle['position'].copy()

        return PIDParameters(**global_best)


class PredictiveController:
    """Model Predictive Control (MPC) for advanced control."""

    def __init__(self, prediction_horizon: int = 10, control_horizon: int = 5):
        self.prediction_horizon = prediction_horizon
        self.control_horizon = control_horizon
        self.process_model = None  # Would be learned or provided

    def optimize_control_sequence(self, current_state: np.ndarray, setpoint: float,
                                constraints: Dict[str, Any]) -> np.ndarray:
        """Compute optimal control sequence using MPC."""
        # Simplified MPC implementation
        control_sequence = np.random.random(self.control_horizon) * 10  # Mock
        return control_sequence

    def update_process_model(self, historical_data: pd.DataFrame):
        """Update internal process model from data."""
        # Would implement system identification
        pass


class MultiLoopCoordinator:
    """Coordinator for multiple interacting control loops."""

    def __init__(self):
        self.loop_interactions = {}  # Graph of loop interactions
        self.coordination_rules = []

    def add_interaction(self, loop1: str, loop2: str, interaction_type: str, strength: float):
        """Add interaction between control loops."""
        if loop1 not in self.loop_interactions:
            self.loop_interactions[loop1] = {}
        if loop2 not in self.loop_interactions:
            self.loop_interactions[loop2] = {}

        self.loop_interactions[loop1][loop2] = {'type': interaction_type, 'strength': strength}
        self.loop_interactions[loop2][loop1] = {'type': interaction_type, 'strength': strength}

    def coordinate_control(self, loop_states: Dict[str, Any]) -> Dict[str, float]:
        """Coordinate control actions across multiple loops."""
        coordinated_actions = {}

        for loop_id, state in loop_states.items():
            base_action = state.get('base_action', 0)

            # Apply coordination adjustments
            adjustment = 0
            if loop_id in self.loop_interactions:
                for other_loop, interaction in self.loop_interactions[loop_id].items():
                    if other_loop in loop_states:
                        other_action = loop_states[other_loop].get('base_action', 0)
                        adjustment += interaction['strength'] * (other_action - base_action)

            coordinated_actions[loop_id] = base_action + adjustment * 0.1  # Dampened adjustment

        return coordinated_actions


class AdaptiveControlLoops(LoggerMixin):
    """
    Advanced adaptive control system with real-time PID optimization, MPC, and multi-loop coordination.

    This class implements adaptive control loops that can automatically tune
    PID parameters based on process characteristics and performance metrics,
    with advanced features like predictive control and loop coordination.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AdaptiveControlLoops system.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

        # Control loops registry
        self.control_loops: Dict[str, PIDParameters] = {}
        self.performance_history: Dict[str, List[ControlPerformance]] = {}

        # Adaptive tuning settings
        self.adaptation_enabled = self.config.get("adaptation_enabled", True)
        self.tuning_method = self.config.get(
            "tuning_method", "ziegler_nichols"
        )  # 'ziegler_nichols', 'cohen_coon', 'relay'
        self.adaptation_interval = self.config.get(
            "adaptation_interval", 300
        )  # seconds
        self.performance_window = self.config.get("performance_window", 3600)  # seconds

        # Ziegler-Nichols tuning parameters
        self.zn_ultimate_gain = {}
        self.zn_oscillation_period = {}

        # Performance thresholds
        self.performance_thresholds = {
            "max_overshoot": 0.1,  # 10%
            "max_settling_time": 60.0,  # seconds
            "max_steady_state_error": 0.05,  # 5%
            "min_damping_ratio": 0.3,
        }
        self.performance_thresholds.update(
            self.config.get("performance_thresholds", {})
        )

        self.logger.info("AdaptiveControlLoops initialized")

    @validate_input(
        {
            "loop_id": {
                "type": "string",
                "max_length": 50,
                "required": True,
                "pattern": "^[a-zA-Z0-9_-]{1,50}$",
            }
        }
    )
    def create_control_loop(
        self,
        loop_id: str,
        initial_params: PIDParameters,
        mode: ControlMode = ControlMode.AUTOMATIC,
    ) -> None:
        """
        Create a new control loop.

        Args:
            loop_id: Unique identifier for the control loop
            initial_params: Initial PID parameters
            mode: Control mode

        Raises:
            ValueError: If loop_id is invalid
            InvalidPIDParametersError: If parameters are invalid
        """
        if not loop_id or not loop_id.strip():
            raise ValueError("Loop ID cannot be empty")

        self._validate_pid_parameters(initial_params)

        self.control_loops[loop_id] = initial_params
        self.performance_history[loop_id] = []

        self.logger.info(f"Created control loop {loop_id} with mode {mode.value}")

    @monitor_operation("adaptive_control_loops.optimize_controller")
    def optimize_controller(
        self, loop_id: str, process_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Optimize PID controller parameters for a control loop.

        Args:
            loop_id: ID of the control loop to optimize
            process_data: Optional historical process data for analysis

        Returns:
            Dictionary with optimization results

        Raises:
            ValueError: If loop_id not found
        """
        if loop_id not in self.control_loops:
            raise ValueError(f"Control loop {loop_id} not found")

        try:
            current_params = self.control_loops[loop_id]
            optimization_result = {
                "loop_id": loop_id,
                "original_parameters": asdict(current_params),
                "optimization_method": self.tuning_method,
                "timestamp": datetime.now(),
            }

            if self.tuning_method == "ziegler_nichols":
                optimized_params = self._ziegler_nichols_tuning(loop_id, process_data)
            elif self.tuning_method == "cohen_coon":
                optimized_params = self._cohen_coon_tuning(loop_id, process_data)
            elif self.tuning_method == "relay":
                optimized_params = self._relay_tuning(loop_id, process_data)
            else:
                # Default to Ziegler-Nichols
                optimized_params = self._ziegler_nichols_tuning(loop_id, process_data)

            # Apply optimized parameters
            self.control_loops[loop_id] = optimized_params

            optimization_result["optimized_parameters"] = asdict(optimized_params)
            optimization_result["improvements"] = self._calculate_improvements(
                current_params, optimized_params
            )

            self.logger.info(
                f"Optimized control loop {loop_id} using {self.tuning_method}"
            )
            return optimization_result

        except Exception as e:
            self.logger.error(f"Error optimizing controller {loop_id}: {e}")
            raise AdaptiveControlError(f"Failed to optimize controller: {e}") from e

    @monitor_operation("adaptive_control_loops.analyze_controller")
    def analyze_controller(
        self, loop_id: str, analysis_window: int = 3600
    ) -> Dict[str, Any]:
        """
        Analyze control loop performance and stability.

        Args:
            loop_id: ID of the control loop to analyze
            analysis_window: Time window for analysis in seconds

        Returns:
            Dictionary with analysis results

        Raises:
            ValueError: If loop_id not found
        """
        if loop_id not in self.control_loops:
            raise ValueError(f"Control loop {loop_id} not found")

        try:
            history = self.performance_history.get(loop_id, [])
            if not history:
                return {
                    "loop_id": loop_id,
                    "status": "no_data",
                    "message": "No performance data available",
                }

            # Filter recent data
            cutoff_time = datetime.now() - timedelta(seconds=analysis_window)
            recent_data = [p for p in history if p.timestamp > cutoff_time]

            if not recent_data:
                return {
                    "loop_id": loop_id,
                    "status": "insufficient_data",
                    "message": f"No data in last {analysis_window} seconds",
                }

            analysis = {
                "loop_id": loop_id,
                "analysis_period": analysis_window,
                "data_points": len(recent_data),
                "current_parameters": asdict(self.control_loops[loop_id]),
                "performance_metrics": self._calculate_performance_metrics(recent_data),
                "stability_analysis": self._analyze_stability(recent_data),
                "recommendations": [],
            }

            # Generate recommendations
            analysis["recommendations"] = self._generate_control_recommendations(
                loop_id, analysis
            )

            self.logger.info(f"Completed analysis for control loop {loop_id}")
            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing controller {loop_id}: {e}")
            raise AdaptiveControlError(f"Failed to analyze controller: {e}") from e

    def update_process_feedback(
        self,
        loop_id: str,
        setpoint: float,
        process_variable: float,
        control_output: float,
        timestamp: Optional[datetime] = None,
    ) -> ControlPerformance:
        """
        Update control loop with process feedback for adaptive tuning.

        Args:
            loop_id: ID of the control loop
            setpoint: Desired setpoint
            process_variable: Current process variable
            control_output: Controller output
            timestamp: Optional timestamp

        Returns:
            ControlPerformance object

        Raises:
            ValueError: If loop_id not found
        """
        if loop_id not in self.control_loops:
            raise ValueError(f"Control loop {loop_id} not found")

        try:
            update_time = timestamp or datetime.now()
            params = self.control_loops[loop_id]

            # Calculate errors
            error = setpoint - process_variable
            integral_error = getattr(self, f"_integral_{loop_id}", 0) + error
            derivative_error = error - getattr(self, f"_prev_error_{loop_id}", 0)

            # Apply integral limits
            integral_error = max(
                params.integral_limits[0],
                min(params.integral_limits[1], integral_error),
            )

            # Store for next iteration
            setattr(self, f"_integral_{loop_id}", integral_error)
            setattr(self, f"_prev_error_{loop_id}", error)

            # Create performance record
            performance = ControlPerformance(
                timestamp=update_time,
                setpoint=setpoint,
                process_variable=process_variable,
                control_output=control_output,
                error=error,
                integral_error=integral_error,
                derivative_error=derivative_error,
            )

            # Store in history
            if loop_id not in self.performance_history:
                self.performance_history[loop_id] = []
            self.performance_history[loop_id].append(performance)

            # Limit history size
            max_history = self.config.get("max_history_size", 10000)
            if len(self.performance_history[loop_id]) > max_history:
                self.performance_history[loop_id] = self.performance_history[loop_id][
                    -max_history:
                ]

            # Check for adaptation trigger
            if self.adaptation_enabled:
                self._check_adaptation_trigger(loop_id)

            return performance

        except Exception as e:
            self.logger.error(f"Error updating process feedback for {loop_id}: {e}")
            raise AdaptiveControlError(f"Failed to update process feedback: {e}") from e

    def _validate_pid_parameters(self, params: PIDParameters) -> None:
        """Validate PID parameters."""
        if params.kp < 0:
            raise InvalidPIDParametersError("Kp must be non-negative")
        if params.ki < 0:
            raise InvalidPIDParametersError("Ki must be non-negative")
        if params.kd < 0:
            raise InvalidPIDParametersError("Kd must be non-negative")

        if params.output_limits[0] >= params.output_limits[1]:
            raise InvalidPIDParametersError(
                "Output limits must be (min, max) with min < max"
            )

    def _ziegler_nichols_tuning(
        self, loop_id: str, process_data: Optional[pd.DataFrame]
    ) -> PIDParameters:
        """Implement Ziegler-Nichols tuning method."""
        # This is a simplified implementation
        # In practice, this would involve step response analysis

        current_params = self.control_loops[loop_id]

        # Default tuning ratios (conservative)
        if self.tuning_method == "ziegler_nichols":
            # P-only controller first
            kp_zn = 0.5 * current_params.kp
            ti_zn = 0.5  # Integral time
            td_zn = 0.125  # Derivative time

            return PIDParameters(
                kp=kp_zn,
                ki=kp_zn / ti_zn,
                kd=kp_zn * td_zn,
                setpoint=current_params.setpoint,
                output_limits=current_params.output_limits,
                integral_limits=current_params.integral_limits,
            )

        return current_params

    def _cohen_coon_tuning(
        self, loop_id: str, process_data: Optional[pd.DataFrame]
    ) -> PIDParameters:
        """Implement Cohen-Coon tuning method."""
        # Simplified Cohen-Coon implementation
        current_params = self.control_loops[loop_id]

        # Cohen-Coon tuning constants
        kp_cc = current_params.kp * 1.35
        ti_cc = 2.5  # Integral time
        td_cc = 0.37  # Derivative time

        return PIDParameters(
            kp=kp_cc,
            ki=kp_cc / ti_cc,
            kd=kp_cc * td_cc,
            setpoint=current_params.setpoint,
            output_limits=current_params.output_limits,
            integral_limits=current_params.integral_limits,
        )

    def _relay_tuning(
        self, loop_id: str, process_data: Optional[pd.DataFrame]
    ) -> PIDParameters:
        """Implement relay feedback tuning method."""
        # This would typically involve relay oscillation experiments
        # Simplified implementation
        current_params = self.control_loops[loop_id]

        return PIDParameters(
            kp=current_params.kp * 0.6,
            ki=current_params.ki * 0.5,
            kd=current_params.kd * 0.125,
            setpoint=current_params.setpoint,
            output_limits=current_params.output_limits,
            integral_limits=current_params.integral_limits,
        )

    def _calculate_performance_metrics(
        self, performance_data: List[ControlPerformance]
    ) -> Dict[str, Any]:
        """Calculate control performance metrics."""
        if not performance_data:
            return {}

        errors = [p.error for p in performance_data]
        setpoints = [p.setpoint for p in performance_data]
        process_vars = [p.process_variable for p in performance_data]

        metrics = {
            "mean_error": np.mean(errors),
            "std_error": np.std(errors),
            "max_error": max(errors),
            "min_error": min(errors),
            "rmse": np.sqrt(np.mean(np.square(errors))),
            "mae": np.mean(np.abs(errors)),
        }

        # Calculate overshoot if setpoint changes detected
        setpoint_changes = self._detect_setpoint_changes(setpoints)
        if setpoint_changes:
            overshoots = []
            for change_idx in setpoint_changes:
                if change_idx + 10 < len(process_vars):
                    segment = process_vars[change_idx : change_idx + 10]
                    max_val = max(segment)
                    setpoint_val = setpoints[change_idx]
                    overshoot = (
                        (max_val - setpoint_val) / setpoint_val
                        if setpoint_val != 0
                        else 0
                    )
                    overshoots.append(overshoot)

            if overshoots:
                metrics["max_overshoot"] = max(overshoots)
                metrics["avg_overshoot"] = np.mean(overshoots)

        return metrics

    def _analyze_stability(
        self, performance_data: List[ControlPerformance]
    ) -> Dict[str, Any]:
        """Analyze control loop stability."""
        if len(performance_data) < 10:
            return {"status": "insufficient_data"}

        errors = [p.error for p in performance_data]

        # Simple stability checks
        stability = {
            "is_stable": True,
            "oscillation_detected": False,
            "damping_ratio": None,
            "issues": [],
        }

        # Check for oscillations (simplified)
        if len(errors) > 20:
            # Calculate autocorrelation to detect oscillations
            autocorr = np.correlate(errors, errors, mode="full")
            autocorr = autocorr[autocorr.size // 2 :]

            # Find peaks in autocorrelation
            peaks = []
            for i in range(1, len(autocorr) - 1):
                if autocorr[i] > autocorr[i - 1] and autocorr[i] > autocorr[i + 1]:
                    peaks.append((i, autocorr[i]))

            if (
                peaks and peaks[0][1] > 0.5
            ):  # Strong autocorrelation indicates oscillation
                stability["oscillation_detected"] = True
                stability["issues"].append("Oscillations detected in control loop")

        # Check for instability (integral windup, etc.)
        integral_errors = [p.integral_error for p in performance_data]
        if (
            max(integral_errors)
            > self.control_loops.get("integral_limits", (0, 100))[1] * 0.9
        ):
            stability["issues"].append("Potential integral windup detected")

        if stability["issues"]:
            stability["is_stable"] = False

        return stability

    def _generate_control_recommendations(
        self, loop_id: str, analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for control loop improvement."""
        recommendations = []
        performance = analysis.get("performance_metrics", {})
        stability = analysis.get("stability_analysis", {})

        # Performance-based recommendations
        if (
            performance.get("max_overshoot", 0)
            > self.performance_thresholds["max_overshoot"]
        ):
            recommendations.append("Reduce proportional gain to decrease overshoot")

        if performance.get("rmse", 0) > 0.1:
            recommendations.append(
                "Consider retuning PID parameters for better setpoint tracking"
            )

        # Stability-based recommendations
        if stability.get("oscillation_detected"):
            recommendations.append(
                "Reduce gains to eliminate oscillations - consider Ziegler-Nichols retuning"
            )

        if not stability.get("is_stable", True):
            recommendations.append(
                "Control loop stability issues detected - manual intervention recommended"
            )

        return recommendations

    def _calculate_improvements(
        self, original: PIDParameters, optimized: PIDParameters
    ) -> Dict[str, float]:
        """Calculate expected improvements from parameter changes."""
        # Simplified improvement calculation
        improvements = {
            "kp_change": (optimized.kp - original.kp) / original.kp
            if original.kp != 0
            else 0,
            "ki_change": (optimized.ki - original.ki) / original.ki
            if original.ki != 0
            else 0,
            "kd_change": (optimized.kd - original.kd) / original.kd
            if original.kd != 0
            else 0,
        }

        return improvements

    def _detect_setpoint_changes(
        self, setpoints: List[float], threshold: float = 0.01
    ) -> List[int]:
        """Detect indices where setpoint changes occur."""
        changes = []
        for i in range(1, len(setpoints)):
            if abs(setpoints[i] - setpoints[i - 1]) > threshold:
                changes.append(i)
        return changes

    def _check_adaptation_trigger(self, loop_id: str) -> None:
        """Check if adaptation should be triggered."""
        # This would implement logic to trigger re-tuning based on performance degradation
        # For now, it's a placeholder
        pass

    def get_control_stats(self, loop_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for control loop(s).

        Args:
            loop_id: Optional specific loop ID

        Returns:
            Dictionary with control statistics
        """
        if loop_id:
            if loop_id not in self.control_loops:
                raise ValueError(f"Control loop {loop_id} not found")

            params = self.control_loops[loop_id]
            history = self.performance_history.get(loop_id, [])

            return {
                "loop_id": loop_id,
                "parameters": asdict(params),
                "performance_records": len(history),
                "last_update": history[-1].timestamp if history else None,
                "avg_error": np.mean([p.error for p in history]) if history else None,
            }
        else:
            # Stats for all loops
            stats = {}
            for lid, params in self.control_loops.items():
                stats[lid] = self.get_control_stats(lid)

            return {
                "total_loops": len(self.control_loops),
                "active_loops": len(
                    [s for s in stats.values() if s["performance_records"] > 0]
                ),
                "individual_stats": stats,
            }

    async def optimize_with_rl(
        self, loop_id: str, current_parameters: Dict[str, float]
    ) -> Optional[Dict[str, float]]:
        """
        Optimize control parameters using integrated RL engine.

        Args:
            loop_id: ID of the control loop
            current_parameters: Current parameter values

        Returns:
            Optimized parameters if RL is available, None otherwise
        """
        if not RL_AVAILABLE:
            self.logger.warning("RL engine not available for optimization")
            return None

        try:
            # Use RL engine to optimize parameters
            optimized = rl_engine.optimize_parameters(current_parameters)

            if optimized:
                self.logger.info(
                    f"RL optimization completed for control loop {loop_id}"
                )
                # Update control loop parameters
                current_params = self.control_loops[loop_id]
                for param, value in optimized.items():
                    if hasattr(current_params, param):
                        setattr(current_params, param, value)

                return optimized
            else:
                self.logger.warning(
                    f"RL optimization returned no results for {loop_id}"
                )
                return None

        except Exception as e:
            self.logger.error(f"RL optimization failed for control loop {loop_id}: {e}")
            return None

    async def predict_performance_with_automl(
        self, loop_id: str, future_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """
        Predict future control performance using integrated AutoML engine.

        Args:
            loop_id: ID of the control loop
            future_data: Data for performance prediction

        Returns:
            Performance predictions if AutoML is available, None otherwise
        """
        if not AUTOML_AVAILABLE or not automl_engine.best_model:
            self.logger.warning(
                "AutoML engine not available for performance prediction"
            )
            return None

        try:
            # Make predictions using AutoML
            predictions = automl_engine.predict(future_data)

            result = {
                "loop_id": loop_id,
                "predictions": predictions.tolist()
                if hasattr(predictions, "tolist")
                else predictions,
                "model_used": automl_engine.best_model_name,
                "prediction_timestamp": datetime.now(),
                "data_shape": future_data.shape,
            }

            self.logger.info(f"AutoML performance prediction completed for {loop_id}")
            return result

        except Exception as e:
            self.logger.error(
                f"AutoML performance prediction failed for {loop_id}: {e}"
            )
            return None

    async def adaptive_optimization_cycle(self, loop_id: str) -> Dict[str, Any]:
        """
        Complete adaptive optimization cycle using both RL and AutoML.

        Args:
            loop_id: ID of the control loop to optimize

        Returns:
            Dictionary with optimization results
        """
        if loop_id not in self.control_loops:
            raise ValueError(f"Control loop {loop_id} not found")

        results = {
            "loop_id": loop_id,
            "timestamp": datetime.now(),
            "rl_optimization": None,
            "automl_prediction": None,
            "combined_recommendations": [],
        }

        try:
            current_params = self.control_loops[loop_id]
            current_param_dict = {
                "kp": current_params.kp,
                "ki": current_params.ki,
                "kd": current_params.kd,
            }

            # RL-based parameter optimization
            rl_optimized = await self.optimize_with_rl(loop_id, current_param_dict)
            if rl_optimized:
                results["rl_optimization"] = rl_optimized

            # AutoML-based performance prediction (if historical data available)
            history = self.performance_history.get(loop_id, [])
            if len(history) > 10:
                # Prepare data for prediction
                history_df = pd.DataFrame(
                    [asdict(p) for p in history[-50:]]
                )  # Last 50 points
                if len(history_df) > 0:
                    automl_pred = await self.predict_performance_with_automl(
                        loop_id, history_df
                    )
                    if automl_pred:
                        results["automl_prediction"] = automl_pred

            # Generate combined recommendations
            results[
                "combined_recommendations"
            ] = self._generate_combined_recommendations(loop_id, results)

            self.logger.info(f"Adaptive optimization cycle completed for {loop_id}")
            return results

        except Exception as e:
            self.logger.error(f"Adaptive optimization cycle failed for {loop_id}: {e}")
            results["error"] = str(e)
            return results

    def _generate_combined_recommendations(
        self, loop_id: str, optimization_results: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on RL and AutoML results."""
        recommendations = []

        rl_opt = optimization_results.get("rl_optimization")
        automl_pred = optimization_results.get("automl_prediction")

        if rl_opt:
            # Check if RL suggests significant parameter changes
            current = self.control_loops[loop_id]
            changes = []
            for param in ["kp", "ki", "kd"]:
                if param in rl_opt:
                    change_pct = abs(rl_opt[param] - getattr(current, param)) / getattr(
                        current, param
                    )
                    if change_pct > 0.1:  # More than 10% change
                        changes.append(
                            f"{param}: {getattr(current, param):.3f} -> {rl_opt[param]:.3f}"
                        )

            if changes:
                recommendations.append(
                    f"RL suggests parameter adjustments: {', '.join(changes)}"
                )

        if automl_pred:
            predictions = automl_pred.get("predictions", [])
            if isinstance(predictions, list) and len(predictions) > 0:
                avg_prediction = np.mean(predictions)
                if avg_prediction > 0.8:  # High predicted performance
                    recommendations.append(
                        "AutoML predicts good future performance with current settings"
                    )
                elif avg_prediction < 0.5:  # Poor predicted performance
                    recommendations.append(
                        "AutoML predicts performance degradation - consider parameter tuning"
                    )

        # Stability recommendations based on recent performance
        analysis = self.analyze_controller(loop_id)
        stability = analysis.get("stability_analysis", {})

        if stability.get("oscillation_detected"):
            recommendations.append(
                "Control oscillations detected - reduce proportional gain"
            )
        elif not stability.get("is_stable", True):
            recommendations.append(
                "Control instability detected - manual intervention recommended"
            )

        return recommendations
