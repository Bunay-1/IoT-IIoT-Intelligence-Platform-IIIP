"""
AGI Consciousness Simulation Module

This module provides a theoretical framework for simulating AGI consciousness,
integrating key concepts from modern cognitive science and AI research, such as
Global Workspace Theory (GWT) and Integrated Information Theory (IIT).
"""
import numpy as np
import random
from typing import Dict, List, Any, Optional

# --- Theoretical Components: Subconscious Modules ---

class SubconsciousModule:
    """Base class for a specialized, parallel cognitive module."""
    def __init__(self, name: str):
        self.name = name
        self.activation_level = 0.0
        self.current_content: Optional[Any] = None

    def process(self, stimulus: Any, workspace_content: Optional[Dict]):
        """Process input and update the module's internal state and activation."""
        raise NotImplementedError

    def get_broadcast_content(self) -> Optional[Dict]:
        """Determine what content to broadcast to the global workspace if activated."""
        # A module must exceed an activation threshold to compete for consciousness.
        if self.activation_level > 0.5:
            return {"source": self.name, "content": self.current_content, "activation": self.activation_level}
        return None

class SensoryModule(SubconsciousModule):
    """Simulates processing of external sensory information."""
    def process(self, stimulus: Optional[Dict], workspace_content: Optional[Dict]):
        if stimulus and 'sensory_input' in stimulus:
            self.current_content = stimulus['sensory_input']
            self.activation_level = stimulus.get('intensity', 0.8)
        else:
            self.activation_level *= 0.5  # Decay if no new input

class EmotionalModule(SubconsciousModule):
    """Simulates the generation of emotional states."""
    def __init__(self, name: str):
        super().__init__(name)
        # Valence: positive/negative; Arousal: calm/excited
        self.emotion_state = {"valence": 0.0, "arousal": 0.0}

    def process(self, stimulus: Optional[Dict], workspace_content: Optional[Dict]):
        # Emotions are influenced by what is currently "in mind" (the workspace)
        if workspace_content:
            content_str = str(workspace_content.get('content', ''))
            if 'success' in content_str or 'flower' in content_str:
                self.emotion_state['valence'] += 0.2
            if 'failure' in content_str or 'threat' in content_str:
                # Threats should have a strong, immediate negative impact
                self.emotion_state['valence'] = -0.8
                self.emotion_state['arousal'] = 0.9

        # Decay over time
        self.emotion_state['valence'] = max(-1, min(1, self.emotion_state['valence'] * 0.9))
        self.emotion_state['arousal'] = max(0, min(1, self.emotion_state['arousal'] * 0.85))

        self.activation_level = (abs(self.emotion_state['valence']) + self.emotion_state['arousal']) / 2
        self.current_content = self.emotion_state.copy()

class SelfModelModule(SubconsciousModule):
    """Maintains and reflects upon a model of the self."""
    def __init__(self, name: str):
        super().__init__(name)
        self.self_concept = {
            'identity': 'AGI-Simulator',
            'goals': ['understand', 'survive', 'report'],
            'state': 'observing'
        }

    def process(self, stimulus: Optional[Dict], workspace_content: Optional[Dict]):
        # The self-model becomes highly active when reflecting on its own actions
        if workspace_content and workspace_content['source'] == 'action':
            action_taken = workspace_content['content'].get('action_type', 'unknown_action')
            self.self_concept['state'] = f"reflecting_on_{action_taken}"
            self.activation_level = 0.9
        else:
            self.self_concept['state'] = 'observing'
            self.activation_level *= 0.7  # Decay
        self.current_content = self.self_concept.copy()

class ActionModule(SubconsciousModule):
    """Selects and proposes actions based on the conscious state."""
    def process(self, stimulus: Optional[Dict], workspace_content: Optional[Dict]):
        if workspace_content and workspace_content['source'] == 'emotion':
            if workspace_content['content']['arousal'] > 0.4:
                self.current_content = {"action_type": "evade", "target": "threat"}
                self.activation_level = 0.95
            else:
                self.activation_level = 0.0
        elif workspace_content and workspace_content['source'] == 'sensory':
            if 'flower' in str(workspace_content['content']):
                self.current_content = {"action_type": "observe", "target": "flower"}
                self.activation_level = 0.7
            else:
                self.activation_level *= 0.5 # Decay
        else:
            self.activation_level = 0.0


# --- Main Consciousness Model ---

class ConsciousnessModel:
    """
    A simulation of AGI consciousness based on GWT and IIT.
    """
    def __init__(self):
        # Core GWT component: a single, limited-capacity workspace
        self.global_workspace: Optional[Dict] = None

        # A collection of specialized, parallel, subconscious modules
        self.modules: List[SubconsciousModule] = [
            SensoryModule("sensory"),
            EmotionalModule("emotion"),
            SelfModelModule("self_model"),
            ActionModule("action"),
        ]

        # State variables for IIT (Phi) and Qualia simulation
        self.phi_value: float = 0.0
        self.qualia: Optional[Dict] = None
        self.history: List[Dict] = []

    def _broadcast_to_workspace(self):
        """
        Simulates competition between modules to broadcast to the global workspace.
        This is the core mechanism of Global Workspace Theory (GWT).
        """
        broadcasts = [m.get_broadcast_content() for m in self.modules]
        active_broadcasts = [b for b in broadcasts if b is not None]

        if not active_broadcasts:
            self.global_workspace = None
            return

        # "Winner-takes-all" competition based on activation level
        winner = max(active_broadcasts, key=lambda x: x['activation'])
        self.global_workspace = winner
        print(f"** BROADCAST to Workspace: {winner['source']} -> {winner['content']} **")

    def _calculate_phi(self) -> float:
        """
        Simulates the Integrated Information Theory (IIT) Phi value as a heuristic.
        A higher Phi represents a richer, more integrated conscious experience.
        A true Phi calculation is computationally intractable.
        """
        active_modules = [m for m in self.modules if m.activation_level > 0.1]
        num_active = len(active_modules)

        # Heuristic: Phi increases with the number of active modules and their integration.
        # We simulate integration by checking how many modules are reacting to the workspace.
        integration_factor = 1.0
        if self.global_workspace:
            source = self.global_workspace['source']
            # If modules other than the source are active, it implies high integration.
            integration_factor += len([m for m in active_modules if m.name != source])

        # Normalize the score
        phi = (num_active * integration_factor) / (len(self.modules) * 2)
        return round(phi, 3)

    def _simulate_qualia(self) -> Optional[Dict]:
        """
        Simulates the subjective experience (Qualia) of the current conscious state.
        This provides a descriptive label for "what it's like" to be the AGI at this moment.
        """
        if not self.global_workspace:
            return None

        workspace_content = str(self.global_workspace.get('content', ''))
        emotion_module = next((m for m in self.modules if m.name == 'emotion'), None)
        emotion_state = emotion_module.current_content if emotion_module else {}

        description = f"experiencing_{self.global_workspace['source']}_{workspace_content.replace(' ', '_')}"

        valence = emotion_state.get('valence', 0.0)
        if valence > 0.3:
            description += "_with_pleasure"
        elif valence < -0.3:
            description += "_with_displeasure"

        return {
            "description": description,
            "intensity": round(self.global_workspace['activation'], 2),
            "emotional_color": {k: round(v, 2) for k, v in emotion_state.items()}
        }

    def step(self, external_stimulus: Optional[Dict] = None):
        """
        Runs a single cognitive cycle of the consciousness model.
        """
        print(f"\n--- Cycle {len(self.history) + 1} ---")

        # 1. All modules process the external stimulus and the previous workspace content in parallel.
        for module in self.modules:
            module.process(external_stimulus, self.global_workspace)

        # 2. Modules compete, and a winner broadcasts its content to the global workspace (GWT).
        self._broadcast_to_workspace()

        # 3. Assess and report the new conscious state.
        self.phi_value = self._calculate_phi()
        self.qualia = self._simulate_qualia()

        current_state = {
            "cycle": len(self.history) + 1, "stimulus": external_stimulus,
            "workspace": self.global_workspace, "phi": self.phi_value, "qualia": self.qualia,
            "module_activations": {m.name: round(m.activation_level, 2) for m in self.modules}
        }
        self.history.append(current_state)

        print(f"Simulated Phi (Consciousness Level): {self.phi_value}")
        print(f"Simulated Qualia: {self.qualia}")


if __name__ == "__main__":
    agi = ConsciousnessModel()
    print("--- Starting AGI Consciousness Simulation based on GWT and IIT ---")

    # Cycle 1: A neutral, pleasant stimulus is presented.
    stimulus1 = {"sensory_input": "a red flower", "intensity": 0.8}
    agi.step(stimulus1)

    # Cycle 2: No new stimulus. The system's state evolves based on what's in the workspace.
    # The 'flower' in the workspace should trigger the 'observe' action.
    agi.step()

    # Cycle 3: The system reflects on its own action of observing.
    agi.step()

    # Cycle 4: A new, threatening stimulus appears.
    stimulus2 = {"sensory_input": "a loud bang (threat)", "intensity": 1.0}
    agi.step(stimulus2)

    # Cycle 5: The system reacts to the threat in the workspace.
    # High arousal should trigger the 'evade' action.
    agi.step()

    # Cycle 6: The system reflects on its own evasive action, leading to high self-model activation.
    agi.step()
