#!/usr/bin/env python3
"""Build data/members.json, the member picker's roster, from congress-legislators.

Source: https://github.com/unitedstates/congress-legislators (public domain).
Its social-media file lists only official (taxpayer-funded) accounts, so the X
handles here are each member's official account, not a campaign account.

    pip install pyyaml
    python3 tools/build_members.py            # downloads the latest roster
    python3 tools/build_members.py --from-dir path/with/yaml/files
"""
import argparse
import datetime
import json
import os
import urllib.request

import yaml

RAW = "https://raw.githubusercontent.com/unitedstates/congress-legislators/main/"
FILES = ("legislators-current.yaml", "legislators-social-media.yaml")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "members.json")

STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee",
    "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    "DC": "District of Columbia", "PR": "Puerto Rico", "GU": "Guam", "AS": "American Samoa",
    "VI": "U.S. Virgin Islands", "MP": "Northern Mariana Islands",
}
TERRITORIES = {"DC", "PR", "GU", "AS", "VI", "MP"}
PARTY = {"Democrat": "D", "Republican": "R", "Independent": "I"}


def ordinal(n):
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def load(from_dir):
    docs = []
    for name in FILES:
        if from_dir:
            with open(os.path.join(from_dir, name), encoding="utf-8") as f:
                docs.append(yaml.safe_load(f))
        else:
            with urllib.request.urlopen(RAW + name, timeout=60) as r:
                docs.append(yaml.safe_load(r.read()))
    return docs


def build(current, social):
    handles = {s["id"]["bioguide"]: s.get("social", {}) for s in social}
    members = []
    for person in current:
        term = person["terms"][-1]
        bioguide = person["id"]["bioguide"]
        names = person["name"]
        name = names.get("official_full") or f"{names.get('nickname') or names['first']} {names['last']}"
        state = term["state"]
        state_name = STATES.get(state, state)
        if term["type"] == "sen":
            chamber, title, seat, where = "senate", "Sen.", state_name, f"{state_name} (U.S. Senate)"
            district = None
        else:
            chamber, district = "house", term.get("district") or 0
            if state in TERRITORIES:
                title = "Res. Comm." if state == "PR" else "Del."
                seat = state
                where = f"{state_name} (non-voting House member)"
            elif district == 0:
                title, seat, where = "Rep.", f"{state}-AL", f"{state_name} (at-large House seat)"
            else:
                title, seat = "Rep.", f"{state}-{district}"
                where = f"{seat}, {state_name}'s {ordinal(district)} congressional district"
        sm = handles.get(bioguide, {})
        members.append({
            "id": bioguide,
            "name": name,
            "title": title,
            "chamber": chamber,
            "state": state,
            "district": district,
            "seat": seat,
            "where": where,
            "party": PARTY.get(term.get("party"), (term.get("party") or "?")[:1]),
            "x": sm.get("twitter") or None,
        })
    members.sort(key=lambda m: (STATES.get(m["state"], m["state"]), m["chamber"] != "senate", m["district"] or 0, m["name"]))
    return members


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from-dir", help="read the two YAML files from this folder instead of downloading them")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    current, social = load(args.from_dir)
    members = build(current, social)
    data = {
        "source": "https://github.com/unitedstates/congress-legislators",
        "updated": datetime.date.today().isoformat(),
        "count": len(members),
        "members": members,
    }
    # Keep the file stable when nothing changed, so the weekly job only commits real roster changes.
    try:
        with open(args.out, encoding="utf-8") as f:
            old = json.load(f)
        if old.get("members") == members:
            print(f"No roster changes ({len(members)} members).")
            return
    except (OSError, ValueError):
        pass
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    with_x = sum(1 for m in members if m["x"])
    print(f"Wrote {len(members)} members ({with_x} with an official X account) to {os.path.relpath(args.out)}.")


if __name__ == "__main__":
    main()
