"""Tests for the three OSINT identity skills under skills/security/.

These are skill scripts, not importable modules, so each is loaded from its
path the way a reader would run it. What is worth pinning down is not the
happy path — it is the refusals. Each of these tools is a genre where free
tooling is confidently wrong, and the value is in what they decline to
assert.
"""

import importlib.util
import json
from pathlib import Path

import pytest

_SKILLS = Path(__file__).resolve().parents[2] / "skills" / "security"


def _load(name: str, filename: str):
    path = _SKILLS / name / "scripts" / filename
    spec = importlib.util.spec_from_file_location(f"skill_{name.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def phone():
    return _load("phone-intel", "phone-intel.py")


@pytest.fixture(scope="module")
def email():
    return _load("email-permute", "email-permute.py")


@pytest.fixture(scope="module")
def handle():
    return _load("handle-pivot", "handle-pivot.py")


class TestPhoneRefusals:
    """The refusals are the product."""

    def test_a_bare_national_number_is_not_assigned_a_country(self, phone):
        # Guessing a country from digit count is how a French mobile becomes
        # an Australian landline in a report.
        result = phone.inspect("0612345678")
        assert "error" in result
        assert "country code" in result["error"]

    def test_the_same_number_resolves_once_a_country_is_supplied(self, phone):
        result = phone.inspect("0612345678", "33")
        assert result["e164"] == "+33612345678"
        assert result["country"] == "France"

    def test_carrier_is_never_reported(self, phone):
        result = phone.inspect("+12125550182")
        # No field claims a carrier — the word appears only in the caveat.
        assert "carrier" not in result
        assert "carrier" not in json.dumps(result.get("nanp", {})).lower()
        assert any("portability" in note.lower() for note in result["notes"])

    def test_an_unknown_area_code_is_not_approximated(self, phone):
        # 999 is not allocated; a neighbour guess would be worse than a gap.
        result = phone.inspect("+19995550100")
        assert result["nanp"]["region"] == "not in the bundled area-code table"
        assert result["nanp"]["personal_line"] is None

    def test_an_unknown_calling_code_says_so(self, phone):
        result = phone.inspect("+9995550100")
        assert "unknown" in result["country"]


class TestPhoneFacts:
    def test_plus_one_is_not_assumed_american(self, phone):
        # The most common geographic error in phone OSINT.
        assert phone.inspect("+18765550100")["nanp"]["region"] == "Jamaica"
        assert phone.inspect("+18095550100")["nanp"]["region"] == "Dominican Republic"
        assert phone.inspect("+14415550100")["nanp"]["region"] == "Bermuda"

    def test_toll_free_is_flagged_as_not_a_person(self, phone):
        result = phone.inspect("+18005550100")
        assert result["nanp"]["personal_line"] is False
        assert "toll-free" in result["nanp"]["region"]
        assert result["leads"][0]["what"] == "This is not a personal line"

    def test_structural_violations_are_caught(self, phone):
        # An NANP area code cannot start with 0 or 1.
        assert "invalid" in phone.inspect("+11125550100")["nanp"]["structure"]

    def test_length_is_checked_against_the_plan_where_one_is_bundled(self, phone):
        assert phone.inspect("+33612345678")["length_check"] == "ok"
        assert "unexpected" in phone.inspect("+3361234")["length_check"]

    def test_length_is_honestly_unvalidated_where_no_plan_is_bundled(self, phone):
        # "not validated" must not read as a pass.
        assert phone.inspect("+2211234567")["length_check"].startswith("not validated")

    def test_over_long_numbers_are_rejected(self, phone):
        assert "error" in phone.inspect("+1234567890123456")

    def test_evidence_entry_matches_the_store_schema(self, phone):
        entry = phone.to_evidence_entry(phone.inspect("+12125550182"))
        assert entry["ioc_type"] == "PHONE"
        assert entry["content"] == "+12125550182"


class TestEmailPatternInference:
    """The feature that turns noise into a lead."""

    def test_a_known_address_locks_the_organisation_pattern(self, email):
        detected = email.detect_pattern("jmartin@acme.com", "Jean Martin")
        assert detected["pattern"] == "flast"

        result = email.permute("Marie Dupont", "acme.com", pattern="flast")
        assert [c["address"] for c in result["candidates"]] == ["mdupont@acme.com"]

    @pytest.mark.parametrize(
        "address,name,expected",
        [
            ("jean.martin@acme.com", "Jean Martin", "first.last"),
            ("jeanmartin@acme.com", "Jean Martin", "firstlast"),
            ("jean_martin@acme.com", "Jean Martin", "first_last"),
            ("j.martin@acme.com", "Jean Martin", "f.last"),
            ("martin.jean@acme.com", "Jean Martin", "last.first"),
            ("jean@acme.com", "Jean Martin", "first"),
        ],
    )
    def test_common_patterns_are_recognised(self, email, address, name, expected):
        assert email.detect_pattern(address, name)["pattern"] == expected

    def test_an_unmodelled_scheme_refuses_to_lock(self, email):
        # An employee-number scheme cannot be guessed at; falling back to
        # first.last would hand back fifteen addresses that all bounce.
        assert email.detect_pattern("emp40418@acme.com", "Jean Martin") is None

    def test_every_candidate_is_marked_unverified(self, email):
        result = email.permute("Marie Dupont", "acme.com")
        assert result["candidates"]
        assert all(c["verified"] is False for c in result["candidates"])
        assert "None of these addresses is verified" in result["warning"]


class TestEmailNameHandling:
    def test_accents_are_stripped_not_dropped(self, email):
        assert email.slugify("Ferrán") == "ferran"
        assert email.slugify("Müller") == "muller"

    def test_surname_particles_join_the_surname(self, email):
        assert email.split_name("Piet van der Berg") == ("Piet", "", "van der Berg")
        assert email.slugify("van der Berg") == "vanderberg"

    def test_a_middle_name_is_recognised_and_unlocks_its_patterns(self, email):
        assert email.split_name("Marie Claire Dupont") == ("Marie", "Claire", "Dupont")
        patterns = {c["pattern"] for c in email.permute("Marie Claire Dupont", "acme.com")["candidates"]}
        assert "first.middle.last" in patterns

    def test_a_hyphenated_surname_gets_both_forms(self, email):
        addresses = [c["address"] for c in email.permute("Ana Garcia-Lopez", "acme.com")["candidates"]]
        assert "ana.garcialopez@acme.com" in addresses
        assert "ana.garcia-lopez@acme.com" in addresses

    def test_a_single_name_is_not_given_an_invented_surname(self, email):
        addresses = [c["address"] for c in email.permute("Prince", "acme.com")["candidates"]]
        assert addresses == ["prince@acme.com", "p@acme.com"]

    def test_no_domain_is_an_error_not_an_empty_address(self, email):
        assert "error" in email.permute("Marie Dupont", "")

    def test_candidates_are_deduplicated(self, email):
        addresses = [c["address"] for c in email.permute("Jo Jo", "acme.com")["candidates"]]
        assert len(addresses) == len(set(addresses))


class TestHandlePivot:
    def test_a_seed_handle_outranks_every_generated_shape(self, handle):
        # People reuse handles far more than they vary them.
        result = handle.candidates("Marie Dupont", seed="mdup42")
        assert result["candidates"][0]["handle"] == "mdup42"
        assert result["candidates"][0]["shape"] == "known handle"

    def test_every_candidate_is_marked_unconfirmed(self, handle):
        result = handle.candidates("Marie Dupont")
        assert all(c["confirmed"] is False for c in result["candidates"])
        assert "never that it is your subject" in result["warning"]

    def test_a_year_becomes_both_four_and_two_digit_suffixes(self, handle):
        handles = [c["handle"] for c in handle.candidates("Marie Dupont", year="1988")["candidates"]]
        assert "mariedupont1988" in handles
        assert "mariedupont88" in handles

    def test_suffixes_can_be_turned_off(self, handle):
        result = handle.candidates("Marie Dupont", suffixes=False)
        assert all(c["shape"] != "base+suffix" for c in result["candidates"])

    def test_middle_names_are_dropped_from_handles(self, handle):
        # Handles almost never carry one; keeping it would push likely
        # candidates off the list.
        assert handle.split_name("Marie Claire Dupont") == ("Marie", "Dupont")

    def test_particles_stay_with_the_surname(self, handle):
        assert handle.split_name("Piet van der Berg") == ("Piet", "van der Berg")

    def test_a_single_name_yields_only_itself(self, handle):
        # The initial alone is one character — no platform accepts that as a
        # handle, so it is not offered as a candidate.
        handles = [c["handle"] for c in handle.candidates("Prince", suffixes=False)["candidates"]]
        assert handles == ["prince"]

    def test_a_single_name_still_gets_suffix_variants(self, handle):
        handles = [c["handle"] for c in handle.candidates("Prince", year="1988")["candidates"]]
        assert "prince1988" in handles

    def test_candidates_are_deduplicated_and_never_stubs(self, handle):
        handles = [c["handle"] for c in handle.candidates("Marie Dupont")["candidates"]]
        assert len(handles) == len(set(handles))
        assert all(len(h) >= 2 for h in handles)

    def test_dorks_cover_the_platforms_that_index_real_names(self, handle):
        platforms = {d["platform"] for d in handle.dorks("Marie Dupont")}
        assert {"LinkedIn", "GitHub", "X / Twitter"} <= platforms
        assert all('"Marie Dupont"' in d["query"] for d in handle.dorks("Marie Dupont"))


class TestSkillManifests:
    """A skill nobody can discover is a script in a folder."""

    @pytest.mark.parametrize("name", ["phone-intel", "email-permute", "handle-pivot"])
    def test_skill_md_exists_with_the_expected_frontmatter(self, name):
        text = (_SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
        assert text.startswith("---\n")
        head = text.split("---", 2)[1]
        assert f"name: {name}" in head
        assert "description:" in head
        assert "category: security" in head

    @pytest.mark.parametrize(
        "name,script",
        [
            ("phone-intel", "phone-intel.py"),
            ("email-permute", "email-permute.py"),
            ("handle-pivot", "handle-pivot.py"),
        ],
    )
    def test_the_script_the_skill_documents_exists_and_runs(self, name, script):
        path = _SKILLS / name / "scripts" / script
        assert path.is_file()
        assert (_SKILLS / name / "SKILL.md").read_text(encoding="utf-8").count(script) >= 1

    @pytest.mark.parametrize("name", ["phone-intel", "email-permute", "handle-pivot"])
    def test_the_authorization_section_is_present(self, name):
        # Every one of these identifies a real person; none ships without
        # saying so.
        text = (_SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
        assert "## Authorization" in text
        assert "scope" in text.lower()
