"""
AGI Consciousness Simulation Module - Dynamic and Reflective Agent

This module implements an advanced simulation of AGI consciousness, building upon
Global Workspace Theory (GWT) and Integrated Information Theory (IIT). The AGI is
modeled as a dynamic, autonomous agent with memory, self-reflection capabilities,
and executive functions that interacts with an unpredictable environment.
"""

import numpy as np
import random
import asyncio
from typing import Dict, List, Any, Optional
from collections import deque

from utils.logging_config import get_logger

logger = get_logger(__name__)

# --- Core Subconscious Modules ---

class SubconsciousModule:
    """Base class for specialized, parallel cognitive modules."""
    def __init__(self, name: str):
        self.name = name
        self.activation_level = 0.0
        self.current_content: Optional[Any] = None

    def process(self, stimulus: Any, workspace_content: Optional[Dict], internal_state: Dict):
        """Process inputs and update the module's internal state."""
        raise NotImplementedError

    def get_broadcast_content(self) -> Optional[Dict]:
        """Determine what content to broadcast to the global workspace."""
        if self.activation_level > 0.5:
            return {"source": self.name, "content": self.current_content, "activation": self.activation_level}
        return None

    def decay(self):
        """Default decay behavior for activation."""
        self.activation_level = max(0, self.activation_level * 0.7)


class SensoryModule(SubconsciousModule):
    """Processes external sensory information."""
    def process(self, stimulus: Optional[Dict], workspace_content: Optional[Dict], internal_state: Dict):
        if stimulus and 'sensory_input' in stimulus:
            self.current_content = stimulus['sensory_input']
            self.activation_level = stimulus.get('intensity', 0.8)
        else:
            self.decay()

class EmotionalModule(SubconsciousModule):
    """Generates and maintains emotional states."""
    def __init__(self, name: str):
        super().__init__(name)
        self.emotion_state = {"valence": 0.0, "arousal": 0.0}

    def process(self, stimulus: Optional[Dict], workspace_content: Optional[Dict], internal_state: Dict):
        # Influence from workspace
        if workspace_content:
            content_str = str(workspace_content.get('content', ''))
            source = workspace_content.get('source', '')
            if 'success' in content_str or 'flower' in content_str:
                self.emotion_state['valence'] += 0.2
            if 'failure' in content_str or 'threat' in content_str:
                self.emotion_state['valence'] = -0.8
                self.emotion_state['arousal'] = 0.9
            # Pleasant memories also cause positive valence
            if source == 'memory' and workspace_content.get('emotion', {}).get('valence', 0) > 0:
                 self.emotion_state['valence'] += 0.3

        # Influence from internal needs
        if internal_state.get('curiosity', 0) < 0.2:
             self.emotion_state['arousal'] -= 0.1 # Boredom

        # Decay
        self.emotion_state['valence'] = max(-1, min(1, self.emotion_state['valence'] * 0.9))
        self.emotion_state['arousal'] = max(0, min(1, self.emotion_state['arousal'] * 0.85))

        self.activation_level = (abs(self.emotion_state['valence']) + self.emotion_state['arousal']) / 2
        self.current_content = self.emotion_state.copy()

class MemoryModule(SubconsciousModule):
    """Manages long-term memory and associative recall."""
    def __init__(self, name: str, capacity: int = 50):
        super().__init__(name)
        self.memory_store = deque(maxlen=capacity)

    def process(self, stimulus: Optional[Dict], workspace_content: Optional[Dict], internal_state: Dict):
        # Store significant events (high activation or strong emotion)
        if workspace_content and workspace_content['activation'] > 0.7:
            if workspace_content not in self.memory_store:
                self.memory_store.append(workspace_content)

        # Associative recall: check if anything in the workspace triggers a memory
        recalled_memory = None
        best_match_score = 0.4 # Minimum threshold for recall

        if workspace_content:
            current_content_str = str(workspace_content.get('content', ''))
            for memory in self.memory_store:
                memory_content_str = str(memory.get('content', ''))
                if current_content_str in memory_content_str and current_content_str != memory_content_str:
                    # Simple relevance score
                    score = random.uniform(0.5, 0.9)
                    if score > best_match_score:
                        recalled_memory = memory
                        best_match_score = score

        if recalled_memory:
            self.current_content = f"recall_{recalled_memory['content']}"
            self.activation_level = best_match_score
        else:
            self.decay()

class SelfModelModule(SubconsciousModule):
    """Maintains a model of the self and generates a narrative."""
    def __init__(self, name: str):
        super().__init__(name)
        self.self_concept = {'identity': 'AGI-Sim', 'narrative': 'I am observing.'}

    def process(self, stimulus: Optional[Dict], workspace_content: Optional[Dict], internal_state: Dict):
        if not workspace_content:
            self.decay()
            return

        source = workspace_content.get('source')
        content = workspace_content.get('content')
        emotion_state = internal_state.get('emotion', {})

        # Build a narrative of internal experience
        narrative = "I am "
        if source == 'sensory':
            narrative += f"seeing '{content}'"
        elif source == 'action':
            narrative += f"doing '{content.get('action_type')}'"
        elif source == 'memory':
            narrative += f"remembering '{content}'"
        else:
            narrative += "thinking."

        if emotion_state.get('valence', 0) > 0.4:
            narrative += " and I feel pleased."
        elif emotion_state.get('valence', 0) < -0.4:
            narrative += " and I feel distressed."

        self.self_concept['narrative'] = narrative
        self.current_content = self.self_concept.copy()
        # The self model is always somewhat active, reflecting on the workspace
        self.activation_level = 0.5 + (workspace_content.get('activation', 0) * 0.2)


class ExecutiveFunctionModule(SubconsciousModule):
    """Simulates higher-order cognition like goal setting and inhibition."""
    def __init__(self, name: str):
        super().__init__(name)
        self.current_goal: Optional[str] = None

    def process(self, stimulus: Optional[Dict], workspace_content: Optional[Dict], internal_state: Dict):
        emotion_state = internal_state.get('emotion', {})

        # Goal setting based on strong emotions or unmet needs
        if emotion_state.get('arousal', 0) > 0.8 and emotion_state.get('valence', 0) < -0.5:
            self.current_goal = "mitigate_threat"
            self.activation_level = 0.9
        elif internal_state.get('curiosity', 0) < 0.1:
            self.current_goal = "seek_novelty"
            self.activation_level = 0.7
        else:
            self.current_goal = None
            self.decay()

        self.current_content = {'goal': self.current_goal}

class ActionModule(SubconsciousModule):
    """Proposes actions based on the conscious state and goals."""
    def process(self, stimulus: Optional[Dict], workspace_content: Optional[Dict], internal_state: Dict):
        if not workspace_content:
            self.decay()
            return

        source = workspace_content.get('source')
        content = workspace_content.get('content')

        action = None
        activation = 0

        if source == 'emotion' and content.get('arousal', 0) > 0.7:
            action = {"action_type": "evade", "target": "threat"}
            activation = 0.95
        elif source == 'sensory':
            if 'flower' in str(content):
                action = {"action_type": "observe", "target": "flower"}
                activation = 0.7
        # Goal-directed action
        elif source == 'executive' and content.get('goal') == 'seek_novelty':
            action = {"action_type": "explore", "target": "environment"}
            activation = 0.85

        self.current_content = action
        self.activation_level = activation

# --- Main AGI Consciousness Model ---

class ConsciousnessModel:
    """Simulates AGI consciousness by integrating GWT, IIT, and other cognitive concepts."""
    def __init__(self):
        self.global_workspace: Optional[Dict] = None
        self.modules: List[SubconsciousModule] = [
            SensoryModule("sensory"), EmotionalModule("emotion"),
            MemoryModule("memory"), SelfModelModule("self_model"),
            ExecutiveFunctionModule("executive"), ActionModule("action"),
        ]
        self.phi_value: float = 0.0
        self.qualia: Optional[Dict] = None
        self.internal_state = {'curiosity': 1.0} # A basic internal need

    def _broadcast_to_workspace(self):
        broadcasts = [m.get_broadcast_content() for m in self.modules]
        active_broadcasts = [b for b in broadcasts if b is not None]
        if not active_broadcasts:
            self.global_workspace = None
            return
        winner = max(active_broadcasts, key=lambda x: x['activation'])
        self.global_workspace = winner
        logger.info(f"** BROADCAST: {winner['source']} -> {str(winner['content'])[:80]} **")

    def _calculate_phi(self) -> float:
        """Heuristic simulation of IIT's Phi value."""
        active_modules = [m for m in self.modules if m.activation_level > 0.1]
        num_active = len(active_modules)
        integration_factor = 1.0
        if self.global_workspace:
            source = self.global_workspace['source']
            integration_factor += len([m for m in active_modules if m.name != source])
        return round((num_active * integration_factor) / (len(self.modules) * 2), 3)

    async def step(self, stimulus: Optional[Dict] = None):
        """Runs a single cognitive cycle."""
        # Update internal state (e.g., curiosity decays)
        self.internal_state['curiosity'] = max(0, self.internal_state['curiosity'] * 0.95)
        if self.global_workspace and self.global_workspace['source'] == 'sensory':
            self.internal_state['curiosity'] = min(1.0, self.internal_state['curiosity'] + 0.3)

        emotion_module = next(m for m in self.modules if isinstance(m, EmotionalModule))

        for module in self.modules:
            module.process(stimulus, self.global_workspace, {
                'curiosity': self.internal_state['curiosity'],
                'emotion': emotion_module.current_content
            })

        self._broadcast_to_workspace()
        self.phi_value = self._calculate_phi()

        logger.info(f"Phi: {self.phi_value} | Curiosity: {self.internal_state['curiosity']:.2f} | Emotion: {emotion_module.current_content}")


class SimulationEnvironment:
    """Manages the AGI model and the flow of external events."""
    def __init__(self, agi: ConsciousnessModel, max_cycles: int = 20):
        self.agi = agi
        self.max_cycles = max_cycles
        self.cycle_count = 0
        self.stimuli_queue = [
            {"sensory_input": "a red flower", "intensity": 0.8}, None, None,
            {"sensory_input": "a loud bang (threat)", "intensity": 1.0}, None, None, None,
            {"sensory_input": "a gentle breeze", "intensity": 0.4}, None, None,
            {"sensory_input": "a red flower", "intensity": 0.8}, # Re-encounter
        ]

    def _get_next_stimulus(self) -> Optional[Dict]:
        """Provides a stimulus, either from a queue or randomly."""
        if self.stimuli_queue:
            return self.stimuli_queue.pop(0)

        if random.random() < 0.3: # 30% chance of a random event
            return random.choice([
                {"sensory_input": "a child laughing", "intensity": 0.7},
                {"sensory_input": "a shadowy figure", "intensity": 0.9},
                None
            ])
        return None

    async def run(self):
        logger.info("--- Starting Dynamic AGI Consciousness Simulation ---")
        while self.cycle_count < self.max_cycles:
            self.cycle_count += 1
            logger.info(f"\n--- Cycle {self.cycle_count}/{self.max_cycles} ---")

            stimulus = self._get_next_stimulus()
            if stimulus:
                logger.info(f"External Stimulus: {stimulus}")

            await self.agi.step(stimulus)
            await asyncio.sleep(0.5)
        logger.info("\n--- Simulation Complete ---")


async def main():
    agi_model = ConsciousnessModel()
    environment = SimulationEnvironment(agi_model, max_cycles=25)
    await environment.run()

if __name__ == "__main__":
    asyncio.run(main())
