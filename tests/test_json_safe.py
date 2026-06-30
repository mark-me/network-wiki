"""Tests for JSON serialization safety utilities."""

import pytest
from network_wiki.json_safe import (
    serialize_json,
    validate_json_injection_safety,
    _EscapedJSONEncoder,
)


class TestSerializeJson:
    def test_basic_object(self):
        result = serialize_json({"name": "test", "count": 42})
        assert '"name"' in result
        assert '"count": 42' in result

    def test_non_ascii_characters(self):
        result = serialize_json({"emoji": "🎉", "chinese": "中文"})
        assert "🎉" in result  # Not escaped by default

    def test_large_payload_rejected(self):
        huge_list = ["x" * 10000 for _ in range(1500)]  # ~15MB total
        with pytest.raises(ValueError, match="too large"):
            serialize_json(huge_list)

    def test_unserializable_type_raises(self):
        class CustomObj:
            pass

        with pytest.raises(TypeError):
            serialize_json({"obj": CustomObj()})


class TestValidationSafety:
    def test_clean_json_passes(self):
        valid = serialize_json({"key": "value"})
        validate_json_injection_safety(valid)  # Should not raise

    def test_script_tags_escape_properly(self):
        malicious = {"payload": "<script>alert('xss')</script>"}
        encoded = serialize_json(malicious)

        # Verify < becomes \u003c
        assert "\\u003cs" in encoded.lower() or "&lt;" in encoded
        validate_json_injection_safety(encoded)  # Should pass

    def test_malformed_json_raises(self):
        broken = '{"unclosed": "string}'
        with pytest.raises(ValueError):
            validate_json_injection_safety(broken)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])