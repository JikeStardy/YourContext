import os
import yaml
from typing import Any, Dict, Optional, Union
from pathlib import Path
import copy

from yourcontext.consts import CommonConst
import threading


class ConfigValidationError(Exception):
    """
    配置验证错误异常。
    """
    pass


class ConfigManager:
    """
    配置管理器负责读取和访问YAML配置文件。
    """

    _instance: Optional["ConfigManager"] = None
    _lock: threading.Lock = threading.Lock()

    @classmethod
    def singleton(cls, config_path: Union[str, Path] = CommonConst.DEFAULT_CONFIG_PATH) -> "ConfigManager":
        """
        Return the singleton instance of ConfigManager.
        If it doesn't exist, create it with the given config_path.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config_path)
        return cls._instance

    def __init__(self, config_path: Union[str, Path]=None):
        """
        Initialize the ConfigManager with a path to the YAML configuration file.

        Args:
            config_path: Path to the YAML configuration file
        """
        if config_path is None:
            config_path = os.getenv("CONFIG_PATH")
            if config_path is None:
                raise ValueError("No config_path provided and CONFIG_PATH environment variable is not set")
        self.config_path = Path(config_path)
        self._config_data: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from the YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._config_data = yaml.safe_load(file) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}")
        except Exception as e:
            raise RuntimeError(f"Error reading configuration file: {e}")

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value by key.

        Supports dot notation for nested keys (e.g., 'database.host').

        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value to return if key is not found

        Returns:
            Configuration value or default if key is not found
        """
        keys = key.split('.')
        value = self._config_data

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value by key.

        Supports dot notation for nested keys (e.g., 'database.host').

        Args:
            key: Configuration key (supports dot notation for nested keys)
            value: Value to set
        """
        keys = key.split('.')
        config = self._config_data

        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the value
        config[keys[-1]] = value

    def reload(self) -> None:
        """Reload configuration from the YAML file."""
        self._load_config()

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration data.

        Returns:
            Dictionary containing all configuration data
        """
        return copy.deepcopy(self._config_data)

    def save(self, output_path: Optional[Union[str, Path]] = None) -> None:
        """
        Save the current configuration to a YAML file.

        Args:
            output_path: Path to save the configuration file. 
                         If not provided, saves to the original config_path.
        """
        save_path = Path(output_path) if output_path else self.config_path
        
        try:
            with open(save_path, 'w', encoding='utf-8') as file:
                yaml.dump(self._config_data, file, default_flow_style=False, 
                         allow_unicode=True, indent=2)
        except Exception as e:
            raise RuntimeError(f"Error saving configuration file: {e}")

    def get_typed(self, key: str, expected_type: type, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value with type checking.

        Args:
            key: Configuration key
            expected_type: Expected type of the value
            default: Default value to return if key is not found

        Returns:
            Configuration value cast to expected type

        Raises:
            TypeError: If the value cannot be cast to the expected type
        """
        value = self.get(key, default)
        
        if value is default and default is not None:
            return default
            
        if value is None:
            return None
            
        if not isinstance(value, expected_type):
            try:
                # Try to convert to the expected type
                return expected_type(value)
            except (ValueError, TypeError):
                raise TypeError(f"Configuration value for '{key}' is not of type {expected_type.__name__}")
                
        return value

    def require(self, key: str) -> Any:
        """
        Get a required configuration value.

        Args:
            key: Configuration key

        Returns:
            Configuration value

        Raises:
            KeyError: If the key is not found
        """
        value = self.get(key, default=...)
        if value is ...:
            raise KeyError(f"Required configuration key '{key}' is missing")
        return value
    

if __name__ == "__main__":
    print(ConfigManager.singleton().get("YourContext.tool.aliyun_asr.base_url"))
