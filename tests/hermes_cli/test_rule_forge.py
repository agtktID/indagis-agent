"""Tests for hermes_cli/rule_forge.py — Sigma/YARA rule generation."""

import uuid

import yaml

from hermes_cli.rule_forge import sigma_rule_for_ioc, yara_rule_for_ioc


class TestSigmaRuleForIoc:
    def test_domain_maps_to_dns_logsource(self):
        text = sigma_rule_for_ioc("DOMAIN", "evil.example.com", ["case-a"])
        rule = yaml.safe_load(text)
        assert rule["logsource"] == {"category": "dns"}
        assert rule["detection"]["selection"]["query|contains"] == "evil.example.com"
        assert rule["detection"]["condition"] == "selection"

    def test_ip_address_maps_to_network_connection(self):
        text = sigma_rule_for_ioc("IP_ADDRESS", "198.51.100.1", ["case-a"])
        rule = yaml.safe_load(text)
        assert rule["logsource"] == {"category": "network_connection"}
        assert rule["detection"]["selection"]["DestinationIp"] == "198.51.100.1"

    def test_package_name_maps_to_process_creation(self):
        text = sigma_rule_for_ioc("PACKAGE_NAME", "evil-pkg", ["case-a"])
        rule = yaml.safe_load(text)
        assert rule["logsource"] == {"category": "process_creation"}
        assert rule["detection"]["selection"]["CommandLine|contains"] == "evil-pkg"

    def test_unmapped_type_falls_back_to_keyword_search(self):
        text = sigma_rule_for_ioc("SECRET", "sk-abc123", ["case-a"])
        rule = yaml.safe_load(text)
        assert rule["logsource"] == {"category": "file_event"}
        assert rule["detection"]["keywords"] == ["sk-abc123"]
        assert rule["detection"]["condition"] == "keywords"

    def test_id_is_a_valid_uuid(self):
        text = sigma_rule_for_ioc("DOMAIN", "x.test", [])
        rule = yaml.safe_load(text)
        uuid.UUID(rule["id"])  # raises ValueError if malformed

    def test_id_is_stable_for_same_input(self):
        text1 = sigma_rule_for_ioc("DOMAIN", "x.test", ["a"])
        text2 = sigma_rule_for_ioc("DOMAIN", "x.test", ["b"])
        assert yaml.safe_load(text1)["id"] == yaml.safe_load(text2)["id"]

    def test_id_differs_for_different_value(self):
        text1 = sigma_rule_for_ioc("DOMAIN", "a.test", [])
        text2 = sigma_rule_for_ioc("DOMAIN", "b.test", [])
        assert yaml.safe_load(text1)["id"] != yaml.safe_load(text2)["id"]

    def test_description_names_investigations(self):
        text = sigma_rule_for_ioc("DOMAIN", "x.test", ["campaign-alpha", "campaign-beta"])
        rule = yaml.safe_load(text)
        assert "campaign-alpha" in rule["description"]
        assert "campaign-beta" in rule["description"]

    def test_output_is_valid_yaml_with_all_required_fields(self):
        text = sigma_rule_for_ioc("ACTOR_USERNAME", "mallory", ["case-a"])
        rule = yaml.safe_load(text)
        for field in ("title", "id", "status", "description", "author", "date", "logsource", "detection", "level"):
            assert field in rule


class TestYaraRuleForIoc:
    def test_contains_indicator_and_meta(self):
        text = yara_rule_for_ioc("IP_ADDRESS", "198.51.100.1", ["case-a"])
        assert "rule IndagisRuleForge_IP_ADDRESS_" in text
        assert '$indicator = "198.51.100.1" ascii wide' in text
        assert 'ioc_type = "IP_ADDRESS"' in text
        assert "case-a" in text
        assert "condition:" in text
        assert "$indicator" in text.split("condition:")[1]

    def test_quotes_and_backslashes_escaped(self):
        text = yara_rule_for_ioc("SECRET", 'sk-"quoted"\\value', [])
        assert '\\"quoted\\"' in text
        assert "\\\\value" in text

    def test_rule_name_is_valid_identifier_shape(self):
        text = yara_rule_for_ioc("DOMAIN", "x.test", [])
        rule_name = text.split("\n", 1)[0].split()[1]
        assert rule_name.replace("_", "").isalnum()

    def test_no_investigations_falls_back_to_unknown(self):
        text = yara_rule_for_ioc("DOMAIN", "x.test", [])
        assert 'investigations = "unknown"' in text
