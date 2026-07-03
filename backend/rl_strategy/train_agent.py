"""
FormulaIQ — PPO Agent Training Script
Trains an F1 strategy agent using Ray RLlib (or a lightweight pure-NumPy PPO fallback).
"""
import os
import sys
import pickle
from pathlib import Path
import numpy as np
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))

from rl_strategy.config import TRAIN_EPISODES, LEARNING_RATE, GAMMA, PPO_CLIP
from rl_strategy.env import F1StrategyEnv

# Setup checkpoints directory
CHECKPOINT_DIR = Path(__file__).parent / "checkpoints"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_PATH = CHECKPOINT_DIR / "f1_ppo_checkpoint.pkl"


# ── Custom NumPy Actor-Critic PPO Fallback ────────────────────────────────────
class NumPyPPOAgent:
    """
    A lightweight Multi-Layer Perceptron PPO/Actor-Critic policy network in pure NumPy.
    Ensures immediate, crash-free execution on Python 3.14 environments.
    """
    def __init__(self, state_dim: int = 15, action_dim: int = 4, hidden_dim: int = 32):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        
        # Policy (Actor) weights
        self.W1_actor = np.random.randn(state_dim, hidden_dim) * np.sqrt(2.0 / state_dim)
        self.b1_actor = np.zeros((1, hidden_dim))
        self.W2_actor = np.random.randn(hidden_dim, action_dim) * np.sqrt(2.0 / hidden_dim)
        self.b2_actor = np.zeros((1, action_dim))
        
        # Value (Critic) weights
        self.W1_critic = np.random.randn(state_dim, hidden_dim) * np.sqrt(2.0 / state_dim)
        self.b1_critic = np.zeros((1, hidden_dim))
        self.W2_critic = np.random.randn(hidden_dim, 1) * np.sqrt(2.0 / hidden_dim)
        self.b2_critic = np.zeros((1, 1))

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)

    def _relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)

    def forward(self, state: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Forward pass for both Actor and Critic.
        Returns: (action_probabilities, state_value)
        """
        # Ensure batch format
        if state.ndim == 1:
            state = state.reshape(1, -1)
            
        # Actor forward
        h_actor = self._relu(np.dot(state, self.W1_actor) + self.b1_actor)
        probs = self._softmax(np.dot(h_actor, self.W2_actor) + self.b2_actor)
        
        # Critic forward
        h_critic = self._relu(np.dot(state, self.W1_critic) + self.b1_critic)
        value = np.dot(h_critic, self.W2_critic) + self.b2_critic
        
        return probs.squeeze(), value.squeeze()

    def select_action(self, state: np.ndarray) -> Tuple[int, float]:
        probs, _ = self.forward(state)
        action = np.random.choice(self.action_dim, p=probs)
        return action, probs[action]

    def train_step(self, states, actions, rewards, next_states, dones):
        """
        Actor-Critic policy gradient update step.
        """
        states = np.array(states)
        actions = np.array(actions)
        rewards = np.array(rewards)
        next_states = np.array(next_states)
        dones = np.array(dones)
        
        # 1. Forward passes
        h1_act = self._relu(np.dot(states, self.W1_actor) + self.b1_actor)
        probs = self._softmax(np.dot(h1_act, self.W2_actor) + self.b2_actor)
        
        h1_crit = self._relu(np.dot(states, self.W1_critic) + self.b1_critic)
        values = np.dot(h1_crit, self.W2_critic) + self.b2_critic
        
        _, next_values = self.forward(next_states)
        next_values = next_values.reshape(-1, 1)
        
        # 2. TD Target and Advantage
        targets = rewards.reshape(-1, 1) + GAMMA * next_values * (1.0 - dones.reshape(-1, 1))
        advantages = targets - values
        
        # 3. Simple policy gradient backprop
        # Critic gradients
        grad_v_out = -advantages
        grad_W2_critic = np.dot(h1_crit.T, grad_v_out) / len(states)
        grad_b2_critic = np.mean(grad_v_out, axis=0, keepdims=True)
        
        grad_h1_crit = np.dot(grad_v_out, self.W2_critic.T) * (h1_crit > 0)
        grad_W1_critic = np.dot(states.T, grad_h1_crit) / len(states)
        grad_b1_critic = np.mean(grad_h1_crit, axis=0, keepdims=True)
        
        # Actor gradients (policy loss gradient)
        grad_a_out = probs.copy()
        # d/da (log prob) = a_prob - 1 (for chosen action)
        for i, a in enumerate(actions):
            grad_a_out[i, a] -= 1.0
        grad_a_out = grad_a_out * advantages  # Scale by advantage
        
        grad_W2_actor = np.dot(h1_act.T, grad_a_out) / len(states)
        grad_b2_actor = np.mean(grad_a_out, axis=0, keepdims=True)
        
        grad_h1_act = np.dot(grad_a_out, self.W2_actor.T) * (h1_act > 0)
        grad_W1_actor = np.dot(states.T, grad_h1_act) / len(states)
        grad_b1_actor = np.mean(grad_h1_act, axis=0, keepdims=True)
        
        # 4. SGD Step
        lr = LEARNING_RATE
        self.W1_actor -= lr * grad_W1_actor
        self.b1_actor -= lr * grad_b1_actor
        self.W2_actor -= lr * grad_W2_actor
        self.b2_actor -= lr * grad_b2_actor
        
        self.W1_critic -= lr * grad_W1_critic
        self.b1_critic -= lr * grad_b1_critic
        self.W2_critic -= lr * grad_W2_critic
        self.b2_critic -= lr * grad_b2_critic

    def save(self, filepath: str):
        with open(filepath, "wb") as f:
            pickle.dump({
                "W1_actor": self.W1_actor,
                "b1_actor": self.b1_actor,
                "W2_actor": self.W2_actor,
                "b2_actor": self.b2_actor,
                "W1_critic": self.W1_critic,
                "b1_critic": self.b1_critic,
                "W2_critic": self.W2_critic,
                "b2_critic": self.b2_critic,
            }, f)

    def load(self, filepath: str):
        if not os.path.exists(filepath):
            return False
        with open(filepath, "rb") as f:
            weights = pickle.load(f)
            self.W1_actor = weights["W1_actor"]
            self.b1_actor = weights["b1_actor"]
            self.W2_actor = weights["W2_actor"]
            self.b2_actor = weights["b2_actor"]
            self.W1_critic = weights["W1_critic"]
            self.b1_critic = weights["b1_critic"]
            self.W2_critic = weights["W2_critic"]
            self.b2_critic = weights["b2_critic"]
        return True


# ── Train Function ────────────────────────────────────────────────────────────
def train_numpy_fallback():
    """
    Fallback training loop in pure NumPy.
    Runs fast and produces reliable checkpoints.
    """
    logger.info("Initializing F1StrategyEnv Gymnasium environment...")
    env = F1StrategyEnv()
    
    logger.info("Creating custom NumPy PPO/Actor-Critic policy agent...")
    agent = NumPyPPOAgent()
    
    logger.info("Training F1 AI Strategist for {} episodes...", TRAIN_EPISODES)
    
    recent_rewards = []
    
    for episode in range(1, TRAIN_EPISODES + 1):
        state, _ = env.reset()
        done = False
        
        states, actions, rewards, next_states, dones = [], [], [], [], []
        episode_reward = 0.0
        
        while not done:
            action, _ = agent.select_action(state)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            
            states.append(state)
            actions.append(action)
            rewards.append(reward)
            next_states.append(next_state)
            dones.append(done)
            
            state = next_state
            episode_reward += reward
            
        # Update weights (policy step)
        agent.train_step(states, actions, rewards, next_states, dones)
        recent_rewards.append(episode_reward)
        
        # Log progress
        if episode % 100 == 0 or episode == 1:
            mean_r = np.mean(recent_rewards[-100:])
            logger.info("Episode {:4d}/{} | Mean Reward (Last 100): {:.2f}", episode, TRAIN_EPISODES, mean_r)
            
    logger.success("Training complete!")
    agent.save(str(CHECKPOINT_PATH))
    logger.info("Saved trained checkpoint to: {}", CHECKPOINT_PATH)
    return str(CHECKPOINT_PATH)


def train_rllib():
    """
    Ray RLlib training config. Will fail back to NumPy if Ray is not installed.
    """
    try:
        import ray
        from ray import tune
        from ray.rllib.algorithms.ppo import PPOConfig
        
        logger.info("Initializing Ray cluster...")
        ray.init(ignore_reinit_error=True)
        
        # Register custom env
        from ray.tune.registry import register_env
        register_env("F1StrategyEnv-v0", lambda config: F1StrategyEnv(config))
        
        # RLlib PPO config
        config = (
            PPOConfig()
            .environment("F1StrategyEnv-v0")
            .framework("torch")
            .rollouts(num_rollout_workers=1)
            .training(
                lr=LEARNING_RATE,
                gamma=GAMMA,
                clip_param=PPO_CLIP,
                sgd_minibatch_size=64,
                train_batch_size=1024
            )
            .resources(num_gpus=0)
        )
        
        logger.info("Starting Ray RLlib tune training...")
        results = tune.run(
            "PPO",
            config=config.to_dict(),
            stop={"training_iteration": 10},
            checkpoint_at_end=True,
            local_dir=str(CHECKPOINT_DIR)
        )
        
        # Save checkpoint
        checkpoint = results.get_last_checkpoint()
        logger.success("Ray RLlib PPO training completed! Checkpoint: {}", checkpoint)
        return checkpoint
    except ImportError:
        logger.warning("Ray/RLlib is not installed (or not supported on this Python/OS version).")
        logger.info("Falling back to the custom NumPy PPO/Actor-Critic trainer.")
        return train_numpy_fallback()


if __name__ == "__main__":
    train_rllib()
