"""
Brain-Computer Interface (BCI) Module

This module provides a comprehensive simulation of a Brain-Computer Interface,
capable of generating synthetic EEG data, processing it, and classifying
it into actionable 'mental commands'.
"""

import asyncio
import time
import random
import numpy as np
from scipy.fft import fft, fftfreq
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from typing import Dict, Any, List, Callable, Optional

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# --- Configuration ---
SAMPLE_RATE = 250  # Hz
SECONDS_PER_SAMPLE = 4  # Duration of each data sample
N_SAMPLES = SAMPLE_RATE * SECONDS_PER_SAMPLE

class BCIManager:
    """
    Manages the full lifecycle of a Brain-Computer Interface, from data
    simulation to command classification.
    """

    def __init__(self):
        self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        self.is_running = False
        self.command_callbacks: Dict[str, Callable] = {}
        logger.info("BCIManager initialized. Ready for training.")

    def _generate_eeg_signal(self, command: Optional[str] = None) -> np.ndarray:
        """
        Generates a synthetic EEG signal with characteristic brainwaves.
        If a command is provided, it embeds a specific pattern for that command.
        """
        t = np.linspace(0, SECONDS_PER_SAMPLE, N_SAMPLES, endpoint=False)

        # Base brainwave simulation
        alpha_wave = 0.5 * np.sin(2 * np.pi * 10 * t) # Calm, relaxed
        beta_wave = 0.8 * np.sin(2 * np.pi * 20 * t)  # Active, thinking
        gamma_wave = 0.3 * np.sin(2 * np.pi * 40 * t) # Cognitive processing

        noise = 0.1 * np.random.randn(N_SAMPLES)
        base_signal = alpha_wave + beta_wave + gamma_wave + noise

        # Embed command-specific patterns
        if command == "push":
            # Stronger, more focused beta wave
            command_signal = 1.5 * np.sin(2 * np.pi * 22 * t + (np.pi/4))
            base_signal += command_signal
        elif command == "pull":
            # A distinct gamma wave burst
            command_signal = 1.2 * np.sin(2 * np.pi * 45 * t)
            burst = np.exp(-((t-2)**2) / 0.1) # Centered at 2 seconds
            base_signal += command_signal * burst
        elif command == "lift":
            # A slightly slower alpha wave modulation
            command_signal = 0.7 * np.sin(2 * np.pi * 8 * t)
            base_signal += command_signal

        return base_signal

    def _extract_features(self, signal: np.ndarray) -> np.ndarray:
        """
        Extracts frequency band power features from an EEG signal using FFT.
        """
        yf = fft(signal)
        xf = fftfreq(N_SAMPLES, 1 / SAMPLE_RATE)

        # Power Spectral Density
        psd = 2.0/N_SAMPLES * np.abs(yf[0:N_SAMPLES//2])

        # Define frequency bands
        bands = {
            'delta': (0.5, 4),
            'theta': (4, 8),
            'alpha': (8, 13),
            'beta': (13, 30),
            'gamma': (30, 50)
        }

        features = []
        for band, (low, high) in bands.items():
            freq_indices = np.where((xf >= low) & (xf <= high))[0]
            band_power = np.sum(psd[freq_indices])
            features.append(band_power)

        return np.array(features)

    def train_classifier(self, n_samples_per_command: int = 50):
        """
        Generates synthetic data for each command and trains the classifier.
        """
        logger.info(f"Starting classifier training with {n_samples_per_command} samples per command...")
        commands = ["push", "pull", "lift", "neutral"]
        X, y = [], []

        for cmd in commands:
            for _ in range(n_samples_per_command):
                signal = self._generate_eeg_signal(cmd if cmd != "neutral" else None)
                features = self._extract_features(signal)
                X.append(features)
                y.append(cmd)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        self.classifier.fit(X_train, y_train)
        y_pred = self.classifier.predict(X_test)

        accuracy = accuracy_score(y_test, y_pred)
        self.is_trained = True
        logger.info(f"Classifier training complete. Accuracy: {accuracy:.2f}")

    def classify_command(self, signal: np.ndarray) -> str:
        """
        Classifies a mental command from a given EEG signal.
        """
        if not self.is_trained:
            raise RuntimeError("Classifier must be trained before use.")

        features = self._extract_features(signal).reshape(1, -1)
        prediction = self.classifier.predict(features)
        return prediction[0]

    def register_command_callback(self, command: str, callback: Callable):
        """
        Registers a callback function to be executed when a command is detected.
        """
        if command not in ["push", "pull", "lift", "neutral"]:
            raise ValueError(f"Invalid command '{command}'.")
        self.command_callbacks[command] = callback
        logger.info(f"Callback registered for command '{command}'.")

    async def start_realtime_processing(self, interval_seconds: float = 1.0):
        """
        Starts a loop to continuously generate and classify EEG data.
        """
        if not self.is_trained:
            logger.error("Cannot start real-time processing: Classifier is not trained.")
            return

        self.is_running = True
        logger.info("BCI real-time processing started. Press Ctrl+C to stop.")

        try:
            while self.is_running:
                # In a real scenario, this signal would come from a device.
                # Here we simulate the user "thinking" of a random command.
                simulated_thought = random.choice(["push", "pull", "lift", "neutral"])
                signal = self._generate_eeg_signal(simulated_thought if simulated_thought != "neutral" else None)

                detected_command = self.classify_command(signal)

                print(f"Simulated thought: {simulated_thought:<10} | Detected command: {detected_command:<10}")

                if detected_command in self.command_callbacks:
                    self.command_callbacks[detected_command](detected_command)

                await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("Real-time processing cancelled.")
        finally:
            self.is_running = False
            logger.info("BCI real-time processing stopped.")

    def stop_realtime_processing(self):
        """Stops the real-time processing loop."""
        self.is_running = False

# --- Demonstration ---
if __name__ == "__main__":

    def on_command_detected(command: str):
        """A simple callback function to handle detected commands."""
        if command != "neutral":
            print(f"  -> ACTION: Executing callback for command '{command}'!")

    async def main_simulation():
        print("--- Initializing Brain-Computer Interface Simulation ---")
        bci_manager = BCIManager()

        # 1. Train the classifier with synthetic data
        bci_manager.train_classifier()

        # 2. Register callbacks for detected commands
        bci_manager.register_command_callback("push", on_command_detected)
        bci_manager.register_command_callback("pull", on_command_detected)
        bci_manager.register_command_callback("lift", on_command_detected)

        # 3. Start the real-time processing loop
        print("\n--- Starting real-time command detection for 10 seconds ---")
        processing_task = asyncio.create_task(
            bci_manager.start_realtime_processing(interval_seconds=1)
        )

        await asyncio.sleep(10)

        # 4. Stop the processing
        processing_task.cancel()
        bci_manager.stop_realtime_processing()
        await processing_task # Wait for the task to finish cleanly

        print("\n--- Simulation Finished ---")

    asyncio.run(main_simulation())
