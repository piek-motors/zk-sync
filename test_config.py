import os
import pytest
from config import _parse_ip_codes, config


class TestParseIpCodes:
    def test_empty_string(self):
        assert _parse_ip_codes(None) == []
        assert _parse_ip_codes('') == []

    def test_single_ip_code_pair(self):
        result = _parse_ip_codes('192.168.1.1:001')
        assert result == [{'ip': '192.168.1.1', 'origin_id': 1}]

    def test_multiple_ip_code_pairs(self):
        result = _parse_ip_codes('192.168.1.1:001,192.168.1.2:002')
        assert result == [
            {'ip': '192.168.1.1', 'origin_id': 1},
            {'ip': '192.168.1.2', 'origin_id': 2},
        ]

    def test_whitespace_handling(self):
        result = _parse_ip_codes(' 192.168.1.1:001 , 192.168.1.2:002 ')
        assert result == [
            {'ip': '192.168.1.1', 'origin_id': 1},
            {'ip': '192.168.1.2', 'origin_id': 2},
        ]

    def test_invalid_format_ignored(self):
        result = _parse_ip_codes('192.168.1.1:001,invalid,192.168.1.2:002')
        assert result == [
            {'ip': '192.168.1.1', 'origin_id': 1},
            {'ip': '192.168.1.2', 'origin_id': 2},
        ]

    def test_invalid_code_ignored(self):
        result = _parse_ip_codes('192.168.1.1:001,192.168.1.2:abc,192.168.1.3:003')
        assert result == [
            {'ip': '192.168.1.1', 'origin_id': 1},
            {'ip': '192.168.1.3', 'origin_id': 3},
        ]


class TestConfig:
    def test_config_has_required_keys(self):
        assert 'ip_codes' in config
        assert 'password' in config

    def test_config_ip_codes_is_list(self):
        assert isinstance(config['ip_codes'], list)

    def test_config_password_is_string(self):
        assert isinstance(config['password'], str)
