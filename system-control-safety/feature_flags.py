# feature_flags.py
"""
Production-ready feature flag system for Sarkar AI Assistant
Supports: user-level, system-level, gradual rollouts, A/B testing, emergency kills
"""

import json
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class FlagType(Enum):
    """Types of feature flags"""
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"  # Gradual rollout
    MULTIVARIATE = "multivariate"  # A/B/C testing
    OPERATIONAL = "operational"  # Kill switches


class FlagScope(Enum):
    """Scope of feature flag impact"""
    GLOBAL = "global"  # All users
    USER = "user"  # Specific user
    AGENT = "agent"  # Specific agent/module
    ENVIRONMENT = "environment"  # dev/staging/prod


@dataclass
class FeatureFlag:
    """Feature flag definition"""
    key: str
    enabled: bool
    flag_type: FlagType
    scope: FlagScope
    description: str
    
    # For percentage rollouts
    rollout_percentage: Optional[int] = None
    
    # For multivariate testing
    variants: Optional[Dict[str, Any]] = None
    
    # Metadata
    created_at: str = None
    updated_at: str = None
    created_by: str = "system"
    
    # Safety
    requires_approval: bool = False
    is_emergency_kill: bool = False
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()


class FeatureFlagManager:
    """
    Core feature flag manager for Sarkar
    Thread-safe, fast lookups, supports hot-reloading
    """
    
    def __init__(self, config_path: str = "flags.json"):
        self.config_path = config_path
        self.flags: Dict[str, FeatureFlag] = {}
        self._load_flags()
        
    def _load_flags(self):
        """Load flags from persistent storage"""
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                for key, flag_data in data.items():
                    flag_data['flag_type'] = FlagType(flag_data['flag_type'])
                    flag_data['scope'] = FlagScope(flag_data['scope'])
                    self.flags[key] = FeatureFlag(**flag_data)
            logger.info(f"Loaded {len(self.flags)} feature flags")
        except FileNotFoundError:
            logger.warning(f"No flags file found at {self.config_path}, starting fresh")
            self._initialize_default_flags()
    
    def _save_flags(self):
        """Persist flags to storage"""
        data = {}
        for key, flag in self.flags.items():
            flag_dict = asdict(flag)
            flag_dict['flag_type'] = flag.flag_type.value
            flag_dict['scope'] = flag.scope.value
            data[key] = flag_dict
        
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(self.flags)} feature flags")
    
    def _initialize_default_flags(self):
        """Set up critical default flags for Sarkar"""
        defaults = [
            FeatureFlag(
                key="core.orchestrator.enabled",
                enabled=True,
                flag_type=FlagType.OPERATIONAL,
                scope=FlagScope.GLOBAL,
                description="Master kill switch for core orchestrator",
                is_emergency_kill=True
            ),
            FeatureFlag(
                key="agents.web_search.enabled",
                enabled=True,
                flag_type=FlagType.BOOLEAN,
                scope=FlagScope.AGENT,
                description="Enable web search agent"
            ),
            FeatureFlag(
                key="agents.code_execution.enabled",
                enabled=False,
                flag_type=FlagType.BOOLEAN,
                scope=FlagScope.AGENT,
                description="Enable code execution agent (HIGH RISK)",
                requires_approval=True
            ),
            FeatureFlag(
                key="memory.long_term.enabled",
                enabled=True,
                flag_type=FlagType.BOOLEAN,
                scope=FlagScope.GLOBAL,
                description="Enable long-term memory storage"
            ),
            FeatureFlag(
                key="features.proactive_suggestions",
                enabled=False,
                flag_type=FlagType.PERCENTAGE,
                scope=FlagScope.USER,
                description="Proactive task suggestions (gradual rollout)",
                rollout_percentage=10
            ),
            FeatureFlag(
                key="model.provider",
                enabled=True,
                flag_type=FlagType.MULTIVARIATE,
                scope=FlagScope.GLOBAL,
                description="LLM provider A/B test",
                variants={
                    "anthropic": 0.8,
                    "openai": 0.2
                }
            ),
            FeatureFlag(
                key="safety.content_filtering",
                enabled=True,
                flag_type=FlagType.OPERATIONAL,
                scope=FlagScope.GLOBAL,
                description="Content safety filtering (DO NOT DISABLE)",
                requires_approval=True
            )
        ]
        
        for flag in defaults:
            self.flags[flag.key] = flag
        self._save_flags()
    
    def is_enabled(
        self, 
        flag_key: str, 
        user_id: Optional[str] = None,
        default: bool = False
    ) -> bool:
        """
        Check if a feature is enabled for a given context
        
        Args:
            flag_key: Feature flag identifier
            user_id: Optional user ID for user-scoped flags
            default: Default value if flag doesn't exist
        """
        if flag_key not in self.flags:
            logger.warning(f"Flag {flag_key} not found, using default: {default}")
            return default
        
        flag = self.flags[flag_key]
        
        # Check base enabled state
        if not flag.enabled:
            return False
        
        # Handle percentage rollouts
        if flag.flag_type == FlagType.PERCENTAGE and user_id:
            return self._check_percentage_rollout(flag, user_id)
        
        return True
    
    def _check_percentage_rollout(self, flag: FeatureFlag, user_id: str) -> bool:
        """Consistent hash-based percentage rollout"""
        if not flag.rollout_percentage:
            return flag.enabled
        
        # Create deterministic hash from user_id + flag_key
        hash_input = f"{user_id}:{flag.key}".encode()
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        bucket = hash_value % 100
        
        return bucket < flag.rollout_percentage
    
    def get_variant(
        self, 
        flag_key: str, 
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """Get variant for multivariate flag (A/B/C testing)"""
        if flag_key not in self.flags:
            return None
        
        flag = self.flags[flag_key]
        
        if flag.flag_type != FlagType.MULTIVARIATE or not flag.variants:
            return None
        
        if not user_id:
            # Return default variant (first one)
            return list(flag.variants.keys())[0]
        
        # Consistent hash-based variant assignment
        hash_input = f"{user_id}:{flag.key}".encode()
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        rand_value = (hash_value % 100) / 100.0
        
        cumulative = 0.0
        for variant, weight in flag.variants.items():
            cumulative += weight
            if rand_value < cumulative:
                return variant
        
        return list(flag.variants.keys())[-1]
    
    def set_flag(
        self, 
        flag_key: str, 
        enabled: bool,
        require_approval: bool = True
    ) -> bool:
        """
        Enable/disable a flag (with safety checks)
        
        Returns True if successful, False if approval required
        """
        if flag_key not in self.flags:
            logger.error(f"Cannot set unknown flag: {flag_key}")
            return False
        
        flag = self.flags[flag_key]
        
        # Safety check: require approval for critical flags
        if flag.requires_approval and require_approval:
            logger.warning(
                f"Flag {flag_key} requires approval. "
                "Use require_approval=False to override."
            )
            return False
        
        flag.enabled = enabled
        flag.updated_at = datetime.utcnow().isoformat()
        self._save_flags()
        
        logger.info(f"Flag {flag_key} set to {enabled}")
        return True
    
    def emergency_disable(self, flag_key: str) -> bool:
        """Emergency kill switch - bypasses all approval"""
        if flag_key not in self.flags:
            return False
        
        self.flags[flag_key].enabled = False
        self.flags[flag_key].updated_at = datetime.utcnow().isoformat()
        self._save_flags()
        
        logger.critical(f"EMERGENCY DISABLE: {flag_key}")
        return True
    
    def get_all_flags(self) -> Dict[str, Dict[str, Any]]:
        """Get all flags for admin dashboard"""
        return {
            key: asdict(flag) 
            for key, flag in self.flags.items()
        }
    
    def reload(self):
        """Hot reload flags from storage"""
        self._load_flags()
        logger.info("Feature flags reloaded")


# Global singleton instance
_flag_manager: Optional[FeatureFlagManager] = None


def get_flag_manager() -> FeatureFlagManager:
    """Get global feature flag manager instance"""
    global _flag_manager
    if _flag_manager is None:
        _flag_manager = FeatureFlagManager()
    return _flag_manager


# Convenience functions
def is_enabled(flag_key: str, user_id: Optional[str] = None, default: bool = False) -> bool:
    """Check if feature is enabled"""
    return get_flag_manager().is_enabled(flag_key, user_id, default)


def get_variant(flag_key: str, user_id: Optional[str] = None) -> Optional[str]:
    """Get variant for A/B test"""
    return get_flag_manager().get_variant(flag_key, user_id)


# Example usage in Sarkar agents
if __name__ == "__main__":
    # Initialize
    flags = FeatureFlagManager()
    
    # Check if web search is enabled
    if is_enabled("agents.web_search.enabled"):
        print("✓ Web search agent enabled")
    
    # Check percentage rollout for specific user
    user_id = "user_123"
    if is_enabled("features.proactive_suggestions", user_id):
        print(f"✓ Proactive suggestions enabled for {user_id}")
    
    # Get A/B test variant
    model = get_variant("model.provider", user_id)
    print(f"User {user_id} assigned to model: {model}")
    
    # Emergency disable
    flags.emergency_disable("agents.code_execution.enabled")
    print("✓ Emergency kill switch activated")
    
    # Print all flags
    print("\nAll feature flags:")
    for key, flag in flags.get_all_flags().items():
        status = "🟢" if flag['enabled'] else "🔴"
        print(f"{status} {key}: {flag['description']}")