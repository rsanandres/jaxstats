import jax
import jax.numpy as jnp
from typing import Dict, List, Tuple
import numpy as np

class PerformanceModel:
    def __init__(self):
        # Initialize model parameters
        self.input_size = 15  # Number of features
        self.hidden_size = 32
        self.output_size = 1  # Single performance score
        
        # Initialize weights using Jax
        key = jax.random.PRNGKey(0)
        self.params = self._init_params(key)
        
        # Define the model architecture
        self.model = self._create_model()

    def _init_params(self, key: jnp.ndarray) -> Dict:
        """Initialize model parameters."""
        k1, k2 = jax.random.split(key)
        
        # Initialize weights and biases for each layer
        w1 = jax.random.normal(k1, (self.input_size, self.hidden_size)) * 0.01
        b1 = jnp.zeros(self.hidden_size)
        w2 = jax.random.normal(k2, (self.hidden_size, self.output_size)) * 0.01
        b2 = jnp.zeros(self.output_size)
        
        return {
            'w1': w1,
            'b1': b1,
            'w2': w2,
            'b2': b2
        }

    def _create_model(self):
        """Create the neural network model."""
        def forward(params, x):
            # First layer with ReLU activation
            h = jnp.dot(x, params['w1']) + params['b1']
            h = jax.nn.relu(h)
            
            # Output layer
            out = jnp.dot(h, params['w2']) + params['b2']
            return jax.nn.sigmoid(out) * 100  # Scale to 0-100 range
        
        return forward

    def _extract_features(self, match_data: Dict) -> jnp.ndarray:
        """Extract relevant features from match data for the model."""
        features = [
            match_data["basic_stats"]["kda"],
            match_data["basic_stats"]["cs_per_min"],
            match_data["vision_stats"]["vision_score"],
            match_data["vision_stats"]["wards_placed"],
            match_data["vision_stats"]["wards_killed"],
            match_data["objective_stats"]["objectives_secured"],
            match_data["damage_stats"]["damage_dealt"] / 1000,  # Scale down
            match_data["damage_stats"]["damage_taken"] / 1000,  # Scale down
            match_data["damage_stats"]["damage_mitigated"] / 1000,  # Scale down
            match_data["timeline"]["early_game"]["kills"],
            match_data["timeline"]["early_game"]["deaths"],
            match_data["timeline"]["mid_game"]["kills"],
            match_data["timeline"]["mid_game"]["deaths"],
            match_data["timeline"]["late_game"]["kills"],
            match_data["timeline"]["late_game"]["deaths"]
        ]
        return jnp.array(features, dtype=jnp.float32)

    def predict_performance(self, match_data: Dict) -> Tuple[float, str]:
        """Predict performance score and generate analysis."""
        features = self._extract_features(match_data)
        score = float(self.model(self.params, features)[0])
        
        # Generate analysis based on score
        if score >= 80:
            analysis = "Exceptional performance! You dominated the game with excellent mechanics and decision-making."
        elif score >= 60:
            analysis = "Good performance. You made positive contributions to the team's success."
        elif score >= 40:
            analysis = "Average performance. There's room for improvement in several areas."
        else:
            analysis = "Below average performance. Focus on improving your fundamentals and decision-making."

        return score, analysis

    def train_step(self, params: Dict, batch: Tuple[jnp.ndarray, jnp.ndarray]) -> Tuple[Dict, float]:
        """Single training step."""
        def loss_fn(params):
            x, y = batch
            pred = self.model(params, x)
            return jnp.mean((pred - y) ** 2)
        
        loss, grads = jax.value_and_grad(loss_fn)(params)
        return jax.tree_map(lambda p, g: p - 0.01 * g, params, grads), loss

    def train(self, training_data: List[Tuple[Dict, float]], epochs: int = 100):
        """Train the model on provided data."""
        # Convert training data to Jax arrays
        X = jnp.array([self._extract_features(x) for x, _ in training_data])
        y = jnp.array([y for _, y in training_data]).reshape(-1, 1)
        
        # Training loop
        for epoch in range(epochs):
            self.params, loss = self.train_step(self.params, (X, y))
            if epoch % 10 == 0:
                print(f"Epoch {epoch}, Loss: {loss:.4f}") 