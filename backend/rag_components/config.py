"""Configuration Manager for RAG system."""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from .models import RAGConfig

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Manages RAG configuration parsing and validation.
    
    Handles loading, validating, saving, and serializing RAG configuration
    from JSON files.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to config JSON file (optional)
        """
        self.config_path = Path(config_path) if config_path else None
        logger.info(f"ConfigurationManager initialized with config_path={config_path}")
    
    def load_config(self) -> RAGConfig:
        """Load configuration from file or use defaults.
        
        Returns:
            RAGConfig instance
            
        Raises:
            ValueError: If configuration is invalid
            FileNotFoundError: If config file doesn't exist and is required
        """
        # If no config path specified, use defaults
        if not self.config_path:
            logger.info("No config path specified, using default configuration")
            return RAGConfig()
        
        # If config file doesn't exist, use defaults
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            return RAGConfig()
        
        try:
            logger.info(f"Loading configuration from {self.config_path}")
            with open(self.config_path, 'r') as f:
                config_dict = json.load(f)
            
            # Parse configuration
            config = self.parse_config(json.dumps(config_dict))
            
            # Validate configuration
            self.validate_config(config)
            
            logger.info("Configuration loaded and validated successfully")
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            logger.info("Using default configuration")
            return RAGConfig()
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            logger.info("Using default configuration")
            return RAGConfig()
    
    def validate_config(self, config: RAGConfig) -> None:
        """Validate configuration parameters.
        
        Checks:
        - chunk_size > 0
        - chunk_overlap < chunk_size
        - min_chunk_chars > 0
        - top_k > 0
        - score_threshold in [0, 1]
        - relevance_threshold in [0, 1]
        - llm_temperature in [0, 2]
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If validation fails with descriptive message
        """
        errors = []
        
        # Validate chunk_size
        if config.chunk_size <= 0:
            errors.append(f"chunk_size must be > 0, got {config.chunk_size}")
        
        # Validate chunk_overlap
        if config.chunk_overlap < 0:
            errors.append(f"chunk_overlap must be >= 0, got {config.chunk_overlap}")
        if config.chunk_overlap >= config.chunk_size:
            errors.append(
                f"chunk_overlap ({config.chunk_overlap}) must be < chunk_size ({config.chunk_size})"
            )
        
        # Validate min_chunk_chars
        if config.min_chunk_chars <= 0:
            errors.append(f"min_chunk_chars must be > 0, got {config.min_chunk_chars}")
        
        # Validate top_k
        if config.top_k <= 0:
            errors.append(f"top_k must be > 0, got {config.top_k}")
        
        # Validate score_threshold
        if not (0 <= config.score_threshold <= 1):
            errors.append(
                f"score_threshold must be in [0, 1], got {config.score_threshold}"
            )
        
        # Validate relevance_threshold
        if not (0 <= config.relevance_threshold <= 1):
            errors.append(
                f"relevance_threshold must be in [0, 1], got {config.relevance_threshold}"
            )
        
        # Validate llm_temperature
        if not (0 <= config.llm_temperature <= 2):
            errors.append(
                f"llm_temperature must be in [0, 2], got {config.llm_temperature}"
            )
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.debug("Configuration validation passed")
    
    def save_config(self, config: RAGConfig, path: Path) -> None:
        """Save configuration to JSON file.
        
        Args:
            config: Configuration to save
            path: Output file path
            
        Raises:
            IOError: If file cannot be written
        """
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            config_dict = config.to_dict()
            
            with open(path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            logger.info(f"Configuration saved to {path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise IOError(f"Failed to save configuration to {path}: {e}") from e
    
    def parse_config(self, json_str: str) -> RAGConfig:
        """Parse configuration from JSON string.
        
        Args:
            json_str: JSON configuration string
            
        Returns:
            RAGConfig instance
            
        Raises:
            ValueError: If JSON is invalid or missing required fields
        """
        try:
            config_dict = json.loads(json_str)
            
            # Extract nested configuration if present
            if "embedding" in config_dict:
                embedding_config = config_dict.get("embedding", {})
                config_dict["embedding_model"] = embedding_config.get(
                    "model_name", "all-MiniLM-L6-v2"
                )
                config_dict["embedding_dimension"] = embedding_config.get(
                    "dimension", 384
                )
            
            if "chunking" in config_dict:
                chunking_config = config_dict.get("chunking", {})
                config_dict["chunk_size"] = chunking_config.get("chunk_size", 700)
                config_dict["chunk_overlap"] = chunking_config.get("overlap", 100)
                config_dict["min_chunk_chars"] = chunking_config.get("min_chunk_chars", 120)
            
            if "retrieval" in config_dict:
                retrieval_config = config_dict.get("retrieval", {})
                config_dict["top_k"] = retrieval_config.get("top_k", 4)
                config_dict["score_threshold"] = retrieval_config.get("score_threshold", 0.20)
            
            if "reranking" in config_dict:
                reranking_config = config_dict.get("reranking", {})
                config_dict["reranking_enabled"] = reranking_config.get("enabled", True)
                config_dict["reranking_model"] = reranking_config.get(
                    "model_name", "cross-encoder/ms-marco-MiniLM-L-6-v2"
                )
                config_dict["relevance_threshold"] = reranking_config.get(
                    "relevance_threshold", 0.3
                )
            
            if "llm" in config_dict:
                llm_config = config_dict.get("llm", {})
                config_dict["llm_model"] = llm_config.get("model", "llama-3.3-70b-versatile")
                config_dict["llm_temperature"] = llm_config.get("temperature", 0.2)
            
            # Create RAGConfig from dictionary
            config = RAGConfig.from_dict(config_dict)
            
            logger.debug("Configuration parsed successfully")
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            raise ValueError(f"Invalid JSON configuration: {e}") from e
        except Exception as e:
            logger.error(f"Failed to parse configuration: {e}")
            raise ValueError(f"Failed to parse configuration: {e}") from e
    
    def format_config(self, config: RAGConfig) -> str:
        """Format configuration as JSON string.
        
        Args:
            config: Configuration to format
            
        Returns:
            Pretty-printed JSON string
        """
        config_dict = {
            "embedding": {
                "model_name": config.embedding_model,
                "dimension": config.embedding_dimension,
            },
            "chunking": {
                "chunk_size": config.chunk_size,
                "overlap": config.chunk_overlap,
                "min_chunk_chars": config.min_chunk_chars,
            },
            "retrieval": {
                "top_k": config.top_k,
                "score_threshold": config.score_threshold,
            },
            "reranking": {
                "enabled": config.reranking_enabled,
                "model_name": config.reranking_model,
                "relevance_threshold": config.relevance_threshold,
            },
            "llm": {
                "model": config.llm_model,
                "temperature": config.llm_temperature,
            },
        }
        
        json_str = json.dumps(config_dict, indent=2)
        logger.debug("Configuration formatted successfully")
        return json_str


def get_config_manager(config_path: Optional[Path] = None) -> ConfigurationManager:
    """Factory function to get a ConfigurationManager instance.
    
    Args:
        config_path: Path to config JSON file (optional)
        
    Returns:
        ConfigurationManager instance
    """
    return ConfigurationManager(config_path)
