from pathlib import Path
import pytest
import os
from yourcontext.config import ConfigManager, ConfigValidationError

EXAMPLE_DATA = {
    "YourContext": {
        "api": {
            "port": 8000
        },
        "model": [
            "qwen3-max",
            "qwen3-omni-flash"
        ],
        "storage": {
            "chromadb": {
                "enable": False
            },
            "file": {
                "enable": True,
                "max_file_count": 1000,
                "max_file_size": 1000000000,
                "path": "./storage"
            }
        },
        "tool": {
            "bilibili": {
                "sessdata": "bilibili_sessdata"
            },
            "aliyun_bailian": {
                "api_key": "aliyun_bailian_aksk"
            },
            "tavily": {
                "api_key": "tavily_api_key"
            }
        }
    }
}

class TestConfigManager():

    @pytest.mark.parametrize("config_path", ["./config_default.yaml"])
    @pytest.mark.run(order=1)
    def test_init_with_valid_file(self, config_path):
        """Test initialization with a valid configuration file."""
        # Should not raise any exceptions
        config = ConfigManager(config_path)
        assert config.config_path == Path(config_path)
    
    @pytest.mark.parametrize("config_path", ["/nonexistent/path/config.yaml"])
    @pytest.mark.run(order=2)
    def test_init_with_nonexistent_file(self, config_path):
        """Test initialization with a nonexistent file."""
        with pytest.raises(FileNotFoundError):
            ConfigManager(config_path)
    
    @pytest.mark.parametrize("config_path", ["./config_default.yaml"])
    @pytest.mark.run(order=3)
    def test_get_simple_key(self, config_path):
        """Test getting a simple top-level key."""
        config = ConfigManager(config_path)
        result = config.get("YourContext")
        assert result == EXAMPLE_DATA["YourContext"]
    
    @pytest.mark.parametrize("config_path", ["./config_default.yaml"])
    @pytest.mark.run(order=4)
    def test_get_nested_key(self, config_path):
        """Test getting a nested key using dot notation."""
        config = ConfigManager(config_path)
        result = config.get("YourContext.tool.bilibili.sessdata")
        assert result == EXAMPLE_DATA["YourContext"]["tool"]["bilibili"]["sessdata"]
        
        result = config.get("YourContext.tool.aliyun_bailian.api_key")
        assert result == EXAMPLE_DATA["YourContext"]["tool"]["aliyun_bailian"]["api_key"]
        
        result = config.get("YourContext.tool.tavily.api_key")
        assert result == EXAMPLE_DATA["YourContext"]["tool"]["tavily"]["api_key"]
    
    @pytest.mark.parametrize("config_path", ["./config_default.yaml"])
    @pytest.mark.run(order=5)
    def test_get_with_default(self, config_path):
        """Test getting a value with a default for missing keys."""
        config = ConfigManager(config_path)
        result = config.get("nonexistent.key", "default_value")
        assert result == "default_value"
    
    @pytest.mark.parametrize("config_path", ["./config_default.yaml"])
    @pytest.mark.run(order=6)
    def test_get_typed(self, config_path):
        """Test getting typed values."""
        # Test int conversion
        config = ConfigManager(config_path)
        result = config.get_typed("YourContext.api.port", int)
        assert result == EXAMPLE_DATA["YourContext"]["api"]["port"]
        assert isinstance(result, int)
        
        # Test bool conversion
        result = config.get_typed("YourContext.storage.file.enable", bool)
        assert result == EXAMPLE_DATA["YourContext"]["storage"]["file"]["enable"]
        assert isinstance(result, bool)
        
        # Test with default
        result = config.get_typed("nonexistent.key", str, "default")
        assert result == "default"
    
    @pytest.mark.parametrize("config_path", ["./config_default.yaml"])
    @pytest.mark.run(order=7)
    def test_get_typed_conversion_error(self, config_path):
        """Test get_typed with invalid type conversion."""
        # Try to convert a string to int when it's not possible
        config = ConfigManager(config_path)
        with pytest.raises(TypeError):
            config.get_typed("YourContext.api.port", list)
    
    @pytest.mark.parametrize("config_path", ["./config_default.yaml"])
    @pytest.mark.run(order=8)
    def test_require(self, config_path):
        """Test requiring a value."""
        config = ConfigManager(config_path)
        result = config.require("YourContext.api.port")
        assert result == EXAMPLE_DATA["YourContext"]["api"]["port"]
        
        with pytest.raises(KeyError):
            config.require("nonexistent.key")
    
    @pytest.mark.parametrize("config_path", ["./config_default.yaml"])
    @pytest.mark.run(order=9)
    def test_set(self, config_path):
        """Test setting values."""
        # Set a new top-level value
        config = ConfigManager(config_path)
        config.set("YourContext.new_key", "new_value")
        assert config.get("YourContext.new_key") == "new_value"
        config.set("YourContext.keys", ["a", "b", "c"])
        assert config.get("YourContext.keys") == ["a", "b", "c"]
        
        # Set a nested value
        config.set("YourContext.new_nested.key", "nested_value")
        assert config.get("YourContext.new_nested.key") == "nested_value"
        config.set("YourContext.new_nested_keys.val", ["a", "b", "c"])
        assert config.get("YourContext.new_nested_keys.val") == ["a", "b", "c"]
        
        # Override existing value
        config.set("YourContext.name", "NewAppName")
        assert config.get("YourContext.name") == "NewAppName"
    
    @pytest.mark.parametrize("config_path", ["./config_default.yaml"])
    @pytest.mark.run(order=10)
    def test_reload(self, config_path):
        """Test reloading configuration from file."""
        # Modify the file directly
        config = ConfigManager(config_path)
        modified_config = config.get_all()
        modified_config["YourContext"]["api"]["port"] = 9999
        
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(modified_config, f, default_flow_style=False, allow_unicode=True)
        
        # Before reload, value should be unchanged
        assert config.get("YourContext.api.port") == EXAMPLE_DATA["YourContext"]["api"]["port"]
        
        # After reload, value should be updated
        config.reload()
        assert config.get("YourContext.api.port") == 9999

        modified_config["YourContext"]["api"]["port"] = 8000
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(modified_config, f, default_flow_style=False, allow_unicode=True)
        
    @pytest.mark.parametrize("config_path", ["./config_default.yaml"])
    @pytest.mark.run(order=11)
    def test_get_all(self, config_path):
        """Test getting all configuration data."""
        config = ConfigManager(config_path)
        result = config.get_all()
        assert result == EXAMPLE_DATA
        
        # Verify it's a copy, not the original dict
        result["new_key"] = "new_value"
        assert config.get_all() != result
    
    @pytest.mark.parametrize("config_path", ["./config_default.yaml"])
    @pytest.mark.run(order=12)
    def test_save(self, config_path):
        """Test saving configuration to file."""
        # Modify configuration
        config = ConfigManager(config_path)
        config.set("YourContext.name", "SavedApp")
        
        # Save to a new file
        new_path = "/tmp/saved_config.yaml"
        try:
            config.save(new_path)
            
            # Load the saved file and verify contents
            saved_config = ConfigManager(new_path)
            assert saved_config.get("YourContext.name") == "SavedApp"
        finally:
            if os.path.exists(new_path):
                os.unlink(new_path)
    
    # def test_add_validator_and_validate(self, config_path):
    #     """Test adding validators and validating configuration."""
    #     # Add validators
    #     config = ConfigManager(config_path)
    #     config.add_validator(
    #         "database.port",
    #         lambda x: isinstance(x, int) and 1 <= x <= 65535,
    #         "Port must be between 1 and 65535"
    #     )
        
    #     config.add_validator(
    #         "app.name",
    #         lambda x: isinstance(x, str) and len(x) > 0,
    #         "App name must be a non-empty string"
    #     )
        
    #     # Valid configuration should pass validation
    #     try:
    #         config.validate()
    #     except ConfigValidationError:
    #         pytest.fail("Valid configuration should pass validation")
        
    #     # Invalid configuration should fail validation
    #     config.set("database.port", 99999)  # Invalid port
    #     with pytest.raises(ConfigValidationError) as cm:
    #         config.validate()
        
    #     assert "Port must be between 1 and 65535" in str(cm.value)
