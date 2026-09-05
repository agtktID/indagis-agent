#!/usr/bin/env python3
"""Phone Intel — what a phone number can and cannot tell you.

Python stdlib only. No API key, no network, no new dependency.

WHAT THIS REFUSES TO DO, and why it matters more than what it does:

  * It does not name a carrier. Number portability means the prefix a
    number was *allocated* under is not the network it is *on* today, and
    has not been for twenty years in most of the world. Every free
    "carrier lookup" that reads a prefix table is reporting the original
    allocation and calling it the current carrier. That is the single most
    common way a phone lookup misleads an investigation, so this tool
    reports the allocation and labels it as such, or says nothing.

  * It does not name a subscriber. A number alone does not carry one.

  * It does not say whether the line is live. That needs a call or an HLR
    query — one is intrusive, the other is paid.

  * It does not guess. An unrecognised country code or an area code absent
    from the bundled table is reported as unknown, never approximated to a
    neighbour. A confident wrong location sends an analyst to the wrong
    city; "I don't know" sends them to a better source.

What it does do is the part that is actually reliable offline: normalise to
E.164, validate the structure against the numbering plan, identify the
country, resolve NANP area codes to their region, and hand back the search
leads worth pursuing by hand.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

# ─── Country calling codes ───────────────────────────────────────────────
# Longest-prefix wins, so +1 (NANP) does not shadow +1242 (Bahamas): the
# NANP entries below are resolved separately by area code.
_CALLING_CODES: Dict[str, str] = {
    "1": "NANP (US, Canada, and Caribbean territories)",
    "7": "Russia / Kazakhstan",
    "20": "Egypt", "27": "South Africa",
    "30": "Greece", "31": "Netherlands", "32": "Belgium", "33": "France",
    "34": "Spain", "36": "Hungary", "39": "Italy",
    "40": "Romania", "41": "Switzerland", "43": "Austria",
    "44": "United Kingdom", "45": "Denmark", "46": "Sweden", "47": "Norway",
    "48": "Poland", "49": "Germany",
    "51": "Peru", "52": "Mexico", "53": "Cuba", "54": "Argentina",
    "55": "Brazil", "56": "Chile", "57": "Colombia", "58": "Venezuela",
    "60": "Malaysia", "61": "Australia", "62": "Indonesia",
    "63": "Philippines", "64": "New Zealand", "65": "Singapore",
    "66": "Thailand",
    "81": "Japan", "82": "South Korea", "84": "Vietnam", "86": "China",
    "90": "Turkey", "91": "India", "92": "Pakistan", "93": "Afghanistan",
    "94": "Sri Lanka", "95": "Myanmar", "98": "Iran",
    "212": "Morocco", "213": "Algeria", "216": "Tunisia", "218": "Libya",
    "220": "Gambia", "221": "Senegal", "223": "Mali", "225": "Côte d'Ivoire",
    "226": "Burkina Faso", "227": "Niger", "228": "Togo", "229": "Benin",
    "233": "Ghana", "234": "Nigeria", "235": "Chad", "236": "Central African Republic",
    "237": "Cameroon", "241": "Gabon", "243": "DR Congo", "244": "Angola",
    "249": "Sudan", "250": "Rwanda", "251": "Ethiopia", "254": "Kenya",
    "255": "Tanzania", "256": "Uganda", "260": "Zambia", "263": "Zimbabwe",
    "264": "Namibia", "265": "Malawi", "267": "Botswana", "268": "Eswatini",
    "351": "Portugal", "352": "Luxembourg", "353": "Ireland", "354": "Iceland",
    "355": "Albania", "356": "Malta", "357": "Cyprus", "358": "Finland",
    "359": "Bulgaria",
    "370": "Lithuania", "371": "Latvia", "372": "Estonia", "373": "Moldova",
    "374": "Armenia", "375": "Belarus", "376": "Andorra", "377": "Monaco",
    "378": "San Marino", "380": "Ukraine", "381": "Serbia", "382": "Montenegro",
    "383": "Kosovo", "385": "Croatia", "386": "Slovenia", "387": "Bosnia and Herzegovina",
    "389": "North Macedonia",
    "420": "Czechia", "421": "Slovakia", "423": "Liechtenstein",
    "500": "Falkland Islands", "501": "Belize", "502": "Guatemala",
    "503": "El Salvador", "504": "Honduras", "505": "Nicaragua",
    "506": "Costa Rica", "507": "Panama", "509": "Haiti",
    "51": "Peru", "591": "Bolivia", "592": "Guyana", "593": "Ecuador",
    "595": "Paraguay", "598": "Uruguay",
    "670": "Timor-Leste", "673": "Brunei", "674": "Nauru", "675": "Papua New Guinea",
    "676": "Tonga", "677": "Solomon Islands", "679": "Fiji", "685": "Samoa",
    "852": "Hong Kong", "853": "Macau", "855": "Cambodia", "856": "Laos",
    "880": "Bangladesh", "886": "Taiwan",
    "960": "Maldives", "961": "Lebanon", "962": "Jordan", "963": "Syria",
    "964": "Iraq", "965": "Kuwait", "966": "Saudi Arabia", "967": "Yemen",
    "968": "Oman", "970": "Palestine", "971": "United Arab Emirates",
    "972": "Israel", "973": "Bahrain", "974": "Qatar", "975": "Bhutan",
    "976": "Mongolia", "977": "Nepal", "992": "Tajikistan", "993": "Turkmenistan",
    "994": "Azerbaijan", "995": "Georgia", "996": "Kyrgyzstan", "998": "Uzbekistan",
}

# ─── NANP area codes ─────────────────────────────────────────────────────
# Deliberately incomplete rather than approximate. An area code absent here
# is reported as "not in the bundled table", never rounded to a neighbour.
_NANP_AREAS: Dict[str, str] = {
    # Caribbean and territories — these matter most, because a +1 number
    # outside the US/Canada is the case an analyst is most likely to misread.
    "242": "Bahamas", "246": "Barbados", "264": "Anguilla", "268": "Antigua and Barbuda",
    "284": "British Virgin Islands", "340": "US Virgin Islands", "345": "Cayman Islands",
    "441": "Bermuda", "473": "Grenada", "649": "Turks and Caicos", "664": "Montserrat",
    "670": "Northern Mariana Islands", "671": "Guam", "684": "American Samoa",
    "721": "Sint Maarten", "758": "Saint Lucia", "767": "Dominica",
    "784": "Saint Vincent and the Grenadines", "787": "Puerto Rico", "939": "Puerto Rico",
    "809": "Dominican Republic", "829": "Dominican Republic", "849": "Dominican Republic",
    "868": "Trinidad and Tobago", "869": "Saint Kitts and Nevis", "876": "Jamaica",
    "658": "Jamaica",
    # Canada
    "204": "Manitoba, CA", "226": "Ontario, CA", "236": "British Columbia, CA",
    "249": "Ontario, CA", "250": "British Columbia, CA", "289": "Ontario, CA",
    "306": "Saskatchewan, CA", "343": "Ontario, CA", "365": "Ontario, CA",
    "403": "Alberta, CA", "416": "Toronto, ON, CA", "418": "Quebec, CA",
    "431": "Manitoba, CA", "437": "Toronto, ON, CA", "438": "Montreal, QC, CA",
    "450": "Quebec, CA", "506": "New Brunswick, CA", "514": "Montreal, QC, CA",
    "519": "Ontario, CA", "579": "Quebec, CA", "581": "Quebec, CA",
    "587": "Alberta, CA", "604": "Vancouver, BC, CA", "613": "Ottawa, ON, CA",
    "639": "Saskatchewan, CA", "647": "Toronto, ON, CA", "705": "Ontario, CA",
    "709": "Newfoundland and Labrador, CA", "778": "British Columbia, CA",
    "780": "Alberta, CA", "807": "Ontario, CA", "819": "Quebec, CA",
    "867": "Northwest Territories / Nunavut / Yukon, CA", "873": "Quebec, CA",
    "902": "Nova Scotia / PEI, CA", "905": "Ontario, CA",
    # United States — major metros and single-area-code states.
    "202": "Washington, DC", "205": "Alabama", "206": "Seattle, WA",
    "212": "New York, NY", "213": "Los Angeles, CA", "214": "Dallas, TX",
    "215": "Philadelphia, PA", "302": "Delaware", "303": "Denver, CO",
    "305": "Miami, FL", "307": "Wyoming", "312": "Chicago, IL",
    "313": "Detroit, MI", "314": "St. Louis, MO", "315": "New York",
    "316": "Wichita, KS", "317": "Indianapolis, IN", "319": "Iowa",
    "323": "Los Angeles, CA", "401": "Rhode Island", "404": "Atlanta, GA",
    "405": "Oklahoma City, OK", "406": "Montana", "410": "Baltimore, MD",
    "412": "Pittsburgh, PA", "414": "Milwaukee, WI", "415": "San Francisco, CA",
    "419": "Ohio", "469": "Dallas, TX", "501": "Arkansas", "502": "Louisville, KY",
    "503": "Portland, OR", "504": "New Orleans, LA", "505": "New Mexico",
    "512": "Austin, TX", "513": "Cincinnati, OH", "515": "Des Moines, IA",
    "516": "Long Island, NY", "517": "Michigan", "518": "Albany, NY",
    "601": "Mississippi", "602": "Phoenix, AZ", "603": "New Hampshire",
    "605": "South Dakota", "606": "Kentucky", "607": "New York",
    "608": "Madison, WI", "609": "New Jersey", "612": "Minneapolis, MN",
    "614": "Columbus, OH", "615": "Nashville, TN", "617": "Boston, MA",
    "619": "San Diego, CA", "623": "Phoenix, AZ", "626": "Pasadena, CA",
    "628": "San Francisco, CA", "646": "New York, NY", "650": "San Mateo, CA",
    "651": "St. Paul, MN", "678": "Atlanta, GA", "682": "Fort Worth, TX",
    "701": "North Dakota", "702": "Las Vegas, NV", "703": "Northern Virginia",
    "704": "Charlotte, NC", "713": "Houston, TX", "714": "Orange County, CA",
    "716": "Buffalo, NY", "717": "Pennsylvania", "718": "New York, NY",
    "720": "Denver, CO", "725": "Las Vegas, NV", "737": "Austin, TX",
    "757": "Virginia", "770": "Georgia", "773": "Chicago, IL",
    "781": "Massachusetts", "801": "Salt Lake City, UT", "802": "Vermont",
    "803": "South Carolina", "804": "Richmond, VA", "805": "California",
    "808": "Hawaii", "810": "Michigan", "813": "Tampa, FL", "814": "Pennsylvania",
    "815": "Illinois", "816": "Kansas City, MO", "817": "Fort Worth, TX",
    "818": "Los Angeles, CA", "828": "North Carolina", "832": "Houston, TX",
    "843": "South Carolina", "845": "New York", "847": "Illinois",
    "850": "Florida", "856": "New Jersey", "857": "Boston, MA",
    "858": "San Diego, CA", "859": "Kentucky", "860": "Connecticut",
    "862": "New Jersey", "870": "Arkansas", "872": "Chicago, IL",
    "901": "Memphis, TN", "903": "Texas", "904": "Jacksonville, FL",
    "906": "Michigan", "907": "Alaska", "908": "New Jersey", "909": "California",
    "910": "North Carolina", "912": "Georgia", "913": "Kansas",
    "914": "Westchester, NY", "915": "El Paso, TX", "916": "Sacramento, CA",
    "917": "New York, NY", "918": "Tulsa, OK", "919": "Raleigh, NC",
    "920": "Wisconsin", "925": "California", "928": "Arizona", "929": "New York, NY",
    "930": "Indiana", "931": "Tennessee", "936": "Texas", "937": "Ohio",
    "940": "Texas", "941": "Florida", "947": "Michigan", "949": "Orange County, CA",
    "951": "California", "952": "Minnesota", "954": "Fort Lauderdale, FL",
    "956": "Texas", "959": "Connecticut", "970": "Colorado", "971": "Oregon",
    "972": "Dallas, TX", "973": "New Jersey", "978": "Massachusetts",
    "979": "Texas", "980": "North Carolina", "984": "North Carolina",
    "985": "Louisiana", "989": "Michigan",
}

# NANP service codes that are never a person's line.
_NANP_NON_GEOGRAPHIC = {
    "800": "toll-free", "833": "toll-free", "844": "toll-free", "855": "toll-free",
    "866": "toll-free", "877": "toll-free", "888": "toll-free", "900": "premium-rate",
    "500": "personal communications", "521": "personal communications",
    "533": "personal communications", "544": "personal communications",
    "566": "personal communications", "577": "personal communications",
    "588": "personal communications", "710": "US Government",
}

# Per-country national-number length, where the plan is fixed enough to
# check. Absent from this map means "length not validated", not "any length
# is fine" — the output says which.
_NATIONAL_LENGTHS: Dict[str, Tuple[int, ...]] = {
    "1": (10,), "33": (9,), "44": (10,), "49": (10, 11), "34": (9,),
    "39": (9, 10), "31": (9,), "32": (9,), "41": (9,), "351": (9,),
    "61": (9,), "64": (8, 9), "81": (10,), "82": (9, 10), "86": (11,),
    "91": (10,), "55": (10, 11), "52": (10,), "7": (10,),
}


def _digits(raw: str) -> str:
    return re.sub(r"\D", "", raw or "")


def normalise(raw: str, default_country: Optional[str] = None) -> Dict[str, Any]:
    """Fold a human-typed number into E.164, or explain why it will not fold.

    ``default_country`` is the calling code to assume for a number typed
    without one (``--country 33``). Without it, a bare national number is
    reported as ambiguous rather than assigned to a country — guessing the
    country from digit count alone is how a French mobile becomes a
    Australian landline in a report.
    """
    text = (raw or "").strip()
    has_plus = text.startswith("+") or text.startswith("00")
    digits = _digits(text)

    if text.startswith("00"):
        digits = digits[2:]

    if not digits:
        return {"input": raw, "error": "no digits in input"}

    if not has_plus:
        if default_country:
            digits = _digits(default_country) + digits.lstrip("0")
        else:
            return {
                "input": raw,
                "error": (
                    "no country code, and none supplied. Pass --country <code> "
                    "(e.g. --country 33). Inferring a country from digit count "
                    "alone is unreliable and this tool will not do it."
                ),
            }

    if len(digits) > 15:
        return {"input": raw, "error": f"{len(digits)} digits — E.164 allows at most 15"}

    return {"input": raw, "e164": "+" + digits, "digits": digits}


def _split_country(digits: str) -> Tuple[Optional[str], Optional[str], str]:
    """Longest calling code that matches, plus its country and the rest."""
    for length in (3, 2, 1):
        code = digits[:length]
        if code in _CALLING_CODES:
            return code, _CALLING_CODES[code], digits[length:]
    return None, None, digits


def inspect(raw: str, default_country: Optional[str] = None) -> Dict[str, Any]:
    """Everything that can honestly be said about one number, offline."""
    base = normalise(raw, default_country)
    if "error" in base:
        return base

    digits = base["digits"]
    code, country, national = _split_country(digits)

    report: Dict[str, Any] = {
        **base,
        "country_code": code,
        "country": country or "unknown — calling code not in the bundled table",
        "national_number": national,
        "national_length": len(national),
        "notes": [],
        "leads": [],
    }

    expected = _NATIONAL_LENGTHS.get(code or "")
    if expected is None:
        report["length_check"] = "not validated — no bundled plan for this country"
    elif len(national) in expected:
        report["length_check"] = "ok"
    else:
        report["length_check"] = f"unexpected — plan expects {' or '.join(map(str, expected))} digits"
        report["notes"].append(
            "The national number length does not match this country's plan. Either the "
            "number is wrong, or it carries a trunk prefix that was not stripped."
        )

    if code == "1":
        report.update(_nanp_detail(national))

    report["notes"].append(
        "Carrier is NOT reported. Number portability means an allocation prefix is not "
        "the network the number is on today; every free prefix-based 'carrier lookup' "
        "reports the original allocation and mislabels it as current."
    )
    report["leads"] = _leads(report)

    return report


def _nanp_detail(national: str) -> Dict[str, Any]:
    """NANP is worth decomposing because +1 spans 20+ countries."""
    out: Dict[str, Any] = {}

    if len(national) != 10:
        out["nanp"] = {"error": f"expected 10 digits after +1, got {len(national)}"}
        return out

    npa, nxx, line = national[:3], national[3:6], national[6:]
    detail: Dict[str, Any] = {"area_code": npa, "exchange": nxx, "subscriber": line}

    if npa in _NANP_NON_GEOGRAPHIC:
        detail["region"] = f"non-geographic ({_NANP_NON_GEOGRAPHIC[npa]})"
        detail["personal_line"] = False
    elif npa in _NANP_AREAS:
        detail["region"] = _NANP_AREAS[npa]
        detail["personal_line"] = True
    else:
        # Deliberately not approximated to a neighbouring code.
        detail["region"] = "not in the bundled area-code table"
        detail["personal_line"] = None

    # Structural rules from the plan itself — a violation means the number
    # is malformed, not merely unallocated.
    if npa[0] in "01":
        detail["structure"] = "invalid — an NANP area code cannot start with 0 or 1"
    elif nxx[0] in "01":
        detail["structure"] = "invalid — an NANP exchange cannot start with 0 or 1"
    elif npa[1] == "1" and npa[2] == "1":
        detail["structure"] = f"reserved service code (N11): {npa}"
    else:
        detail["structure"] = "ok"

    out["nanp"] = detail
    return out


def _leads(report: Dict[str, Any]) -> List[Dict[str, str]]:
    """Where to actually look next. The tool is offline; these are not."""
    e164 = report.get("e164", "")
    national = report.get("national_number", "")

    leads = [
        {
            "what": "Exact-match search across the open web",
            "how": f'Search the number in every format it is written: "{e164}", "{national}", '
                   "and the locally-formatted variant. Sellers, forum posts and leaked "
                   "directories rarely use E.164.",
        },
        {
            "what": "Messaging-platform presence",
            "how": "Check whether the number resolves to a profile on the platforms in scope. "
                   "This confirms the line is in use and often exposes a display name or photo.",
        },
        {
            "what": "Breach corpora",
            "how": "Phone numbers appear in breach dumps as often as emails. Cross-check with "
                   "'indagis intel breach-email' on any address you already tie to this person.",
        },
    ]

    if report.get("nanp", {}).get("personal_line") is False:
        leads.insert(0, {
            "what": "This is not a personal line",
            "how": "A toll-free or premium-rate number belongs to an organisation. Pivot to "
                   "the business: the number is usually published on its own site, which "
                   "links it to a legal entity rather than an individual.",
        })

    return leads


def to_evidence_entry(report: Dict[str, Any]) -> Dict[str, Any]:
    """Shape a lookup as an evidence-store entry.

    Matches the schema ``evidence-store.py`` writes, so a number lands in a
    case the same way any other artefact does and 'indagis dossier build'
    renders it with its integrity re-check intact.
    """
    bits = [report.get("country") or "unknown country"]
    nanp = report.get("nanp") or {}
    if nanp.get("region"):
        bits.append(nanp["region"])
    if report.get("length_check") not in (None, "ok"):
        bits.append(report["length_check"])

    return {
        "type": "ioc",
        "source": "phone-intel",
        "content": report["e164"],
        "ioc_type": "PHONE",
        "notes": " · ".join(bits),
    }


def _render(report: Dict[str, Any]) -> None:
    if "error" in report:
        print(f"✗ {report['input']}: {report['error']}", file=sys.stderr)
        return

    print(f"■ {report['e164']}")
    print(f"    Country            {report['country']}")
    print(f"    National number    {report['national_number']}  ({report['national_length']} digits)")
    print(f"    Length check       {report['length_check']}")

    nanp = report.get("nanp")
    if nanp:
        if "error" in nanp:
            print(f"    NANP               {nanp['error']}")
        else:
            print(f"    Area code          {nanp['area_code']}  → {nanp['region']}")
            print(f"    Structure          {nanp['structure']}")

    if report["notes"]:
        print()
        for note in report["notes"]:
            print(f"  ! {note}")

    print()
    print("  Where to look next")
    for lead in report["leads"]:
        print(f"    · {lead['what']}")
        print(f"        {lead['how']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and locate a phone number offline. Reports what a number "
                    "can honestly tell you and refuses to guess the rest.",
    )
    parser.add_argument("number", help="A phone number in any format")
    parser.add_argument(
        "--country",
        help="Calling code to assume when the number has none (e.g. 33). Without it, a "
             "bare national number is reported as ambiguous rather than guessed.",
    )
    parser.add_argument("--json", action="store_true", help="Emit the raw report as JSON")
    parser.add_argument(
        "--evidence",
        metavar="STORE",
        help="Append the finding to an existing evidence-store JSON file",
    )
    args = parser.parse_args()

    report = inspect(args.number, args.country)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _render(report)

    if "error" in report:
        return 1

    if args.evidence:
        import hashlib
        import os
        from datetime import datetime, timezone

        try:
            with open(args.evidence, "r", encoding="utf-8-sig") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Could not read evidence store: {exc}", file=sys.stderr)
            return 1

        if not isinstance(data, dict) or "evidence" not in data:
            print("Not an evidence-store file (expected an object with an 'evidence' array)", file=sys.stderr)
            return 1

        entry = to_evidence_entry(report)
        existing = data.setdefault("evidence", [])
        now = datetime.now(timezone.utc).isoformat()
        entry_id = f"ev-{len(existing) + 1:03d}"
        existing.append({
            "id": entry_id,
            **entry,
            # Hash the content field, matching evidence-store.py, so the
            # dossier's integrity re-check passes on this entry too.
            "content_sha256": hashlib.sha256(entry["content"].encode("utf-8")).hexdigest(),
            "collected_at": now,
            "verification": "unverified",
        })
        data.setdefault("chain_of_custody", []).append(
            {"action": "add", "evidence_id": entry_id, "timestamp": now, "source": "phone-intel"}
        )

        tmp = args.evidence + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        os.replace(tmp, args.evidence)
        print(f"\n✓ Appended {entry_id} to {args.evidence}")
        print("  Re-sign it with 'indagis custody sign' — the digest has changed.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
