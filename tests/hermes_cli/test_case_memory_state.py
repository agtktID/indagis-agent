"""Tests for hermes_cli/case_memory_state.py — the cross-investigation IOC index."""

from hermes_cli.case_memory_state import (
    list_investigations,
    list_iocs,
    lookup_ioc,
    normalize_ioc,
    record_investigation,
    record_sighting,
    stats,
)


class TestNormalizeIoc:
    def test_lowercases_and_strips(self):
        assert normalize_ioc("DOMAIN", "  Evil.Example.COM  ") == "evil.example.com"

    def test_empty_value(self):
        assert normalize_ioc("DOMAIN", "") == ""


class TestRecordSighting:
    def test_first_sighting_is_not_a_correlation(self):
        is_correlation = record_sighting(
            ioc_type="IP_ADDRESS", value="198.51.100.1", investigation="case-a",
            store_path="/tmp/a.json", evidence_id="EV-0001", actor=None, source="dns",
        )
        assert is_correlation is False

    def test_second_sighting_same_investigation_is_not_a_correlation(self):
        record_sighting(
            ioc_type="IP_ADDRESS", value="198.51.100.1", investigation="case-a",
            store_path="/tmp/a.json", evidence_id="EV-0001", actor=None, source="dns",
        )
        is_correlation = record_sighting(
            ioc_type="IP_ADDRESS", value="198.51.100.1", investigation="case-a",
            store_path="/tmp/a.json", evidence_id="EV-0002", actor=None, source="beacon",
        )
        assert is_correlation is False

    def test_sighting_in_different_investigation_is_a_correlation(self):
        record_sighting(
            ioc_type="IP_ADDRESS", value="198.51.100.1", investigation="case-a",
            store_path="/tmp/a.json", evidence_id="EV-0001", actor=None, source="dns",
        )
        is_correlation = record_sighting(
            ioc_type="IP_ADDRESS", value="198.51.100.1", investigation="case-b",
            store_path="/tmp/b.json", evidence_id="EV-0001", actor=None, source="beacon",
        )
        assert is_correlation is True

    def test_value_normalized_for_key(self):
        record_sighting(
            ioc_type="DOMAIN", value="Evil.Example.com", investigation="case-a",
            store_path="/tmp/a.json", evidence_id="EV-0001", actor=None, source="dns",
        )
        entry = lookup_ioc("evil.EXAMPLE.com")
        assert entry is not None
        assert entry["value"] == "Evil.Example.com"


class TestLookupIoc:
    def test_missing_returns_none(self):
        assert lookup_ioc("nothing-here.test") is None

    def test_finds_by_value_regardless_of_type_bucket(self):
        record_sighting(
            ioc_type="DOMAIN", value="evil.example.com", investigation="case-a",
            store_path="/tmp/a.json", evidence_id="EV-0001", actor=None, source="dns",
        )
        entry = lookup_ioc("evil.example.com")
        assert entry["type"] == "DOMAIN"


class TestListIocs:
    def test_filters_by_type(self):
        record_sighting(ioc_type="DOMAIN", value="d.test", investigation="c", store_path="p", evidence_id="e1", actor=None, source="s")
        record_sighting(ioc_type="IP_ADDRESS", value="1.2.3.4", investigation="c", store_path="p", evidence_id="e2", actor=None, source="s")
        assert len(list_iocs(ioc_type="DOMAIN")) == 1
        assert len(list_iocs()) == 2

    def test_sorted_by_last_seen_descending(self):
        record_sighting(ioc_type="DOMAIN", value="old.test", investigation="c", store_path="p", evidence_id="e1", actor=None, source="s")
        record_sighting(ioc_type="DOMAIN", value="new.test", investigation="c", store_path="p", evidence_id="e2", actor=None, source="s")
        entries = list_iocs()
        assert entries[0]["value"] == "new.test"


class TestInvestigations:
    def test_record_and_list(self):
        record_investigation("/tmp/a.json", "campaign-alpha")
        record_investigation("/tmp/b.json", "campaign-beta")
        names = {i["name"] for i in list_investigations()}
        assert names == {"campaign-alpha", "campaign-beta"}

    def test_re_recording_preserves_first_ingested_at(self):
        record_investigation("/tmp/a.json", "campaign-alpha")
        first = list_investigations()[0]["first_ingested_at"]
        record_investigation("/tmp/a.json", "campaign-alpha")
        second = list_investigations()[0]["first_ingested_at"]
        assert first == second


class TestStats:
    def test_empty(self):
        s = stats()
        assert s["total_iocs"] == 0
        assert s["total_investigations"] == 0
        assert s["cross_investigation_iocs"] == 0

    def test_counts_cross_investigation_iocs(self):
        record_investigation("/tmp/a.json", "case-a")
        record_investigation("/tmp/b.json", "case-b")
        record_sighting(ioc_type="IP_ADDRESS", value="1.1.1.1", investigation="case-a", store_path="/tmp/a.json", evidence_id="e1", actor=None, source="s")
        record_sighting(ioc_type="IP_ADDRESS", value="1.1.1.1", investigation="case-b", store_path="/tmp/b.json", evidence_id="e1", actor=None, source="s")
        record_sighting(ioc_type="DOMAIN", value="only-in-a.test", investigation="case-a", store_path="/tmp/a.json", evidence_id="e2", actor=None, source="s")

        s = stats()
        assert s["total_iocs"] == 2
        assert s["cross_investigation_iocs"] == 1
        assert s["by_type"] == {"IP_ADDRESS": 1, "DOMAIN": 1}
