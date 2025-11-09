"""
Model Configuration for Smart CLI Assistant

Defines model tiers with their specifications, pricing and use case
"""
from enum import Enum


class ModelTier(Enum):
    """Model tier enumeration"""
    ECONOMY = "economy"
    BALANCED = "balanced"
    PREMIUM = "premium"


class ModelConfig:
    """Configuration object for a model"""
    def __init__(self, config_dict: dict):
        self.model_id = config_dict["model_id"]
        self.name = config_dict["name"]
        self.description = config_dict["description"]
        self.cost_per_1m_input = config_dict["pricing"]["input"]
        self.cost_per_1m_output = config_dict["pricing"]["output"]
        self.capabilities = config_dict["capabilities"]
        self.use_cases = config_dict["use_cases"]
        # Convert tier string to enum
        tier_str = config_dict["tier"]
        if tier_str == "economy":
            self.tier = ModelTier.ECONOMY
        elif tier_str == "balanced":
            self.tier = ModelTier.BALANCED
        elif tier_str == "premium":
            self.tier = ModelTier.PREMIUM
        else:
            self.tier = ModelTier.ECONOMY


# Model configurations for different tiers
_MODELS_DICT = {
    "haiku": {
        "model_id": "anthropic.claude-3-5-haiku-20241022-v1:0",
        "name": "Claude 3.5 Haiku",
        "description": "Fast and cost-effective for simple tasks",
        "pricing": {
            "input": 0.80,   # per 1M tokens
            "output": 4.00   # per 1M tokens
        },
        "capabilities": {
            "streaming": True,
            "max_tokens": 200000,
            "context_window": 200000
        },
        "use_cases": [
            "Simple Q&A",
            "Quick calculations",
            "Basic file operations",
            "Testing and development"
        ],
        "tier": "economy"
    },

    "sonnet": {
        "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "name": "Claude 3.5 Sonnet",
        "description": "Balanced performance for most production work",
        "pricing": {
            "input": 3.00,   # per 1M tokens
            "output": 15.00  # per 1M tokens
        },
        "capabilities": {
            "streaming": True,
            "max_tokens": 200000,
            "context_window": 200000
        },
        "use_cases": [
            "Complex reasoning",
            "Code generation",
            "Data analysis",
            "Production workloads"
        ],
        "tier": "balanced"
    },

    "opus": {
        "model_id": "anthropic.claude-3-opus-20240229-v1:0",
        "name": "Claude 3 Opus",
        "description": "Premium model for complex reasoning tasks",
        "pricing": {
            "input": 15.00,  # per 1M tokens
            "output": 75.00  # per 1M tokens
        },
        "capabilities": {
            "streaming": True,
            "max_tokens": 200000,
            "context_window": 200000
        },
        "use_cases": [
            "Advanced reasoning",
            "Complex problem solving",
            "Research tasks",
            "Critical applications"
        ],
        "tier": "premium"
    }
}

# Convert dictionaries to ModelConfig objects
MODELS = {name: ModelConfig(config) for name, config in _MODELS_DICT.items()}

# Default model to use if none specified
DEFAULT_MODEL = "haiku"
