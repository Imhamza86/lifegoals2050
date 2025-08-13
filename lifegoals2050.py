#!/usr/bin/env python3
# Life Goals Predictor 2050 📅 — Ultra Legendary Single-File Edition
# Author: Xignite Studios (for Hamzu)
# Zero dependencies. Works in SoloLearn / any Python 3.8+.
# Features: deterministic predictions, synergy rules, rerolls, Monte Carlo stats,
# JSON/Markdown export, interactive fallback.

import argparse
import hashlib
import json
import random
import sys
import textwrap
from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple

# =========================
# Content Pack (Embedded)
# =========================

TRAITS = {
    "career": [
        {"id":"ai_researcher","weight":9,"prestige":9,"risk":5,"tags":["tech","research"],"label":"AI Researcher","impact":"breakthroughs in human–AI collaboration"},
        {"id":"creative_director","weight":7,"prestige":7,"risk":4,"tags":["creative"],"label":"Creative Director","impact":"genre-bending campaigns and IP worlds"},
        {"id":"founder","weight":8,"prestige":8,"risk":9,"tags":["business","risk"],"label":"Startup Founder","impact":"a profitable mission-driven company"},
        {"id":"product_lead","weight":8,"prestige":8,"risk":6,"tags":["tech","product"],"label":"Product Lead","impact":"platforms used by millions"},
        {"id":"cinematic_vfx","weight":6,"prestige":7,"risk":6,"tags":["creative","film"],"label":"Cinematic VFX Director","impact":"award-winning visuals"},
        {"id":"wildcard_nomad","weight":3,"prestige":5,"risk":7,"tags":["travel","gig"],"label":"Digital Nomad","impact":"projects across continents"},
        {"id":"data_ethicist","weight":5,"prestige":7,"risk":3,"tags":["tech","policy"],"label":"Data Ethicist","impact":"safer, fairer AI systems"},
        {"id":"edu_creator","weight":6,"prestige":6,"risk":5,"tags":["creator","edu"],"label":"Edu Creator","impact":"teaching millions online"},
    ],
    "car": [
        {"id":"solid_ev","weight":10,"price":"mid","sustainability":8,"tags":["ev"],"label":"reliable EV"},
        {"id":"ultra_lux_ev","weight":3,"price":"ultra","sustainability":8,"tags":["ev","lux"],"label":"ultra-luxury EV"},
        {"id":"retro_mod","weight":4,"price":"mid_low","sustainability":5,"tags":["style"],"label":"retro-modern ride"},
        {"id":"no_car_city","weight":6,"price":"none","sustainability":10,"tags":["urban"],"label":"no personal car (city mobility)"},
        {"id":"smart_scooter","weight":5,"price":"low","sustainability":9,"tags":["urban","ev"],"label":"smart e-scooter + transit"},
    ],
    "house": [
        {"id":"smart_apartment","weight":10,"price":"mid","space":"mid","tags":["urban","smart"],"label":"smart apartment"},
        {"id":"skyline_penthouse","weight":2,"price":"ultra","space":"mid","tags":["lux"],"label":"skyline penthouse"},
        {"id":"villa_coastal","weight":3,"price":"high","space":"high","tags":["coast"],"label":"coastal villa"},
        {"id":"tiny_home","weight":4,"price":"low","space":"low","tags":["minimal"],"label":"tiny home"},
        {"id":"studio_loft","weight":6,"price":"mid_low","space":"mid_low","tags":["urban","creative"],"label":"studio loft"},
    ],
    "relationship": [
        {"id":"married_kids","weight":7,"label":"married with kids"},
        {"id":"married_no_kids","weight":6,"label":"married, no kids"},
        {"id":"partnered","weight":6,"label":"partnered"},
        {"id":"solo","weight":5,"label":"solo"},
        {"id":"global_long_distance","weight":2,"label":"global long-distance"},
    ],
    "fame": [
        {"id":"local_known","weight":8,"level":3,"label":"locally known"},
        {"id":"industry_respected","weight":8,"level":5,"label":"industry-respected"},
        {"id":"viral_creator","weight":4,"level":7,"label":"viral creator"},
        {"id":"global_icon","weight":1,"level":10,"label":"global icon"},
        {"id":"low_profile","weight":6,"level":1,"label":"low profile"},
    ]
}

MICRO_FACTS = {
    "tech": ["holds 12 patents", "keynoted at a global dev summit", "open-sourced a popular toolkit"],
    "research": ["published in top journals", "mentored young scholars", "led a cross-lab consortium"],
    "creative": ["curated a traveling exhibition", "designed an award-winning brand system", "scored a streaming hit"],
    "film": ["won a VFX guild award", "pioneered real-time virtual production", "helmed a festival favorite"],
    "business": ["backed climate-positive suppliers", "bootstrapped to profitability", "exited a venture gracefully"],
    "creator": ["hit 100M monthly views", "launched a community fund", "toured three continents"],
    "urban": ["bikes on car-free weekdays", "hosts maker nights", "chairs the neighborhood council"],
    "minimal": ["lives with 42 carefully chosen items", "donates yearly to libraries", "keeps a zero-waste kitchen"],
    "coast": ["surfs at sunrise", "restores coral reefs", "hosts beach cleanups"],
    "smart": ["home runs on local solar", "uses edge-AI for safety", "digital twin optimizes energy"],
}

DOMAINS = ["career", "car", "house", "relationship", "fame"]

# =========================
# Utilities
# =========================

def seed_from(name: str, timeline: str = "prime") -> int:
    key = (name.strip().lower() + "::" + timeline.strip().lower()).encode("utf-8")
    return int(hashlib.sha256(key).hexdigest(), 16) % (2**32 - 1)

def rng_for(name: str, timeline: str = "prime", salt: str = "") -> random.Random:
    base = seed_from(name, timeline)
    salted = hashlib.sha256(f"{base}:{salt}".encode()).hexdigest()
    return random.Random(int(salted, 16) % (2**32 - 1))

def weighted_choice(rng: random.Random, items: List[dict], key="weight") -> dict:
    total = sum(max(0.0, float(i.get(key, 0))) for i in items)
    pick = rng.uniform(0, total) if total > 0 else 0
    c = 0.0
    for it in items:
        c += max(0.0, float(it.get(key, 0)))
        if pick <= c:
            return it
    return items[-1] if items else {}

def fame_meter(level: int) -> str:
    level = max(0, min(level, 10))
    return "★" * level + "☆" * (10 - level)

def wrap(s: str, width: int = 84) -> str:
    return textwrap.fill(s, width=width)

# =========================
# Rule Engine
# =========================

@dataclass
class Picks:
    career: dict
    car: dict
    house: dict
    relationship: dict
    fame: dict
    trace: List[str] = field(default_factory=list)

def apply_rules(p: Picks, rng: random.Random) -> Picks:
    """Adjust domain pools or final picks to keep results coherent and flavorful."""
    prestige = int(p.career.get("prestige", 5))
    risk = int(p.career.get("risk", 5))
    fame_level = int(p.fame.get("level", 1))
    rel_id = p.relationship["id"]

    # Adjust car pool
    car_pool = [dict(x) for x in TRAITS["car"]]
    if prestige >= 8 and fame_level >= 7:
        for it in car_pool:
            if it["id"] == "ultra_lux_ev":
                it["weight"] += 3
        p.trace.append("car: luxury boost (prestige ≥8 & fame ≥7)")
    else:
        # Slightly damp ultra luxury
        for it in car_pool:
            if it["id"] == "ultra_lux_ev":
                it["weight"] = max(1, it["weight"] - 2)
        p.trace.append("car: luxury damped (prestige/fame below threshold)")

    # If urban tags in current house or career, nudge no_car_city/scooter
    is_urbanish = ("urban" in p.house.get("tags", [])) or ("tech" in p.career.get("tags", []))
    if is_urbanish:
        for it in car_pool:
            if it["id"] in ("no_car_city", "smart_scooter"):
                it["weight"] += 2
        p.trace.append("car: urban mobility boost")

    # Re-pick car with adjusted weights
    p.car = weighted_choice(rng, car_pool)

    # Adjust house pool
    house_pool = [dict(x) for x in TRAITS["house"]]
    if rel_id == "solo":
        for it in house_pool:
            if it["id"] in ("tiny_home", "studio_loft"):
                it["weight"] += 3
        p.trace.append("house: compact-living boost (solo)")
    if p.car["id"] in ("no_car_city", "smart_scooter"):
        for it in house_pool:
            if "urban" in it.get("tags", []):
                it["weight"] += 2
        p.trace.append("house: urban access boost (city mobility)")
    if prestige >= 8 and fame_level >= 7:
        for it in house_pool:
            if it["id"] == "skyline_penthouse":
                it["weight"] += 2
        p.trace.append("house: penthouse boost (prestige & fame)")

    p.house = weighted_choice(rng, house_pool)

    # Fame interplay with career (mild): creators and founders get a tiny fame nudge
    fame_pool = [dict(x) for x in TRAITS["fame"]]
    if "creator" in p.career.get("tags", []) or p.career["id"] in ("founder","cinematic_vfx"):
        for it in fame_pool:
            if it["id"] in ("viral_creator","industry_respected"):
                it["weight"] += 1
        p.trace.append("fame: creator/founder nudge")
        p.fame = weighted_choice(rng, fame_pool)

    return p

# =========================
# Prediction & Narrative
# =========================

def pick_all(name: str, timeline: str, lock: Dict[str, dict]=None, salt: str="") -> Picks:
    rng = rng_for(name, timeline, salt=salt)
    lock = lock or {}
    career = lock.get("career") or weighted_choice(rng, TRAITS["career"])
    fame   = lock.get("fame")   or weighted_choice(rng, TRAITS["fame"])
    relationship = lock.get("relationship") or weighted_choice(rng, TRAITS["relationship"])
    # temp car/house; final after rules
    car    = lock.get("car")    or weighted_choice(rng, TRAITS["car"])
    house  = lock.get("house")  or weighted_choice(rng, TRAITS["house"])
    p = Picks(career, car, house, relationship, fame, [])
    p = apply_rules(p, rng)
    return p

def short_label(d: dict) -> str:
    return d.get("label") or d.get("id")

def microfacts_for(p: Picks, rng: random.Random, k: int = 2) -> List[str]:
    tag_pool = set(p.career.get("tags", [])) | set(p.house.get("tags", [])) | set(p.car.get("tags", []))
    options = []
    for t in tag_pool:
        options.extend(MICRO_FACTS.get(t, []))
    rng.shuffle(options)
    return options[:k]

def narrative(name: str, p: Picks, timeline: str) -> str:
    first = name.strip().split()[0].title() if name.strip() else "You"
    fame_bar = fame_meter(int(p.fame.get("level", 1)))
    line1 = f"By 2050, {first} is a {short_label(p.career)} known for {p.career.get('impact','meaningful work')}."
    line2 = f"They live in a {short_label(p.house)} and get around with {short_label(p.car)}."
    line3 = f"Relationship status: {p.relationship['label']}. Fame: {p.fame['label']} ({fame_bar})."
    rng = rng_for(name, timeline, salt="facts")
    facts = microfacts_for(p, rng, k=2)
    line4 = ("Highlights: " + ", ".join(facts) + ".") if facts else ""
    return "\n".join([wrap(line1), wrap(line2), wrap(line3), wrap(line4)])

def explanation(p: Picks) -> List[str]:
    return [
        f"career: {p.career['id']} (prestige={p.career.get('prestige','?')}, risk={p.career.get('risk','?')})",
        f"car: {p.car['id']}",
        f"house: {p.house['id']}",
        f"relationship: {p.relationship['id']}",
        f"fame: {p.fame['id']} (level={p.fame.get('level','?')})",
        *[f"rule → {t}" for t in p.trace]
    ]

# =========================
# Monte Carlo
# =========================

def monte_carlo(name: str, timeline: str, n: int = 500) -> Dict[str, Dict[str, int]]:
    counts = {d: {} for d in DOMAINS}
    # Independent runs with varying salt; each run is deterministic given name+timeline+index
    for i in range(n):
        p = pick_all(name, timeline, salt=f"mc:{i}")
        for d in DOMAINS:
            key = getattr(p, d)["id"]
            counts[d][key] = counts[d].get(key, 0) + 1
    return counts

def prob_bars(counts: Dict[str, Dict[str, int]], total: int, width: int = 28) -> str:
    lines = []
    for domain in DOMAINS:
        lines.append(f"\n[{domain.upper()}]")
        items = sorted(counts[domain].items(), key=lambda kv: kv[1], reverse=True)[:6]
        for k, c in items:
            p = c / max(1, total)
            bars = "█" * int(p * width)
            pct = f"{p*100:5.1f}%"
            lines.append(f" - {k:20s} {pct} {bars}")
    return "\n".join(lines)

# =========================
# Export
# =========================

def to_json(name: str, timeline: str, p: Picks, counts: Dict[str, Dict[str, int]] = None, total: int = 0) -> str:
    obj = {
        "name": name,
        "timeline": timeline,
        "picks": {d: getattr(p, d) for d in DOMAINS},
        "explanation": explanation(p),
    }
    if counts:
        obj["monte_carlo"] = {"trials": total, "counts": counts}
    return json.dumps(obj, ensure_ascii=False, indent=2)

def to_markdown(name: str, timeline: str, story: str, p: Picks, counts: Dict[str, Dict[str, int]] = None, total: int = 0) -> str:
    md = []
    md.append(f"# Life Goals Predictor 2050 📅")
    md.append(f"**Name:** {name}  \n**Timeline:** `{timeline}`\n")
    md.append("## Snapshot\n")
    md.append("```text\n" + story + "\n```")
    md.append("## Picks\n")
    for d in DOMAINS:
        v = getattr(p, d)
        if d == "fame":
            md.append(f"- **{d.capitalize()}**: {v['label']} ({fame_meter(int(v.get('level',1)))}) [`{v['id']}`]")
        else:
            md.append(f"- **{d.capitalize()}**: {v.get('label', v['id'])} [`{v['id']}`]")
    md.append("\n## Why this result\n")
    md.append("```text\n" + "\n".join(explanation(p)) + "\n```")
    if counts:
        md.append("\n## Monte Carlo Outlook\n")
        for d in DOMAINS:
            md.append(f"### {d.capitalize()}")
            items = sorted(counts[d].items(), key=lambda kv: kv[1], reverse=True)[:8]
            for k, c in items:
                pct = (c / max(1, total)) * 100
                md.append(f"- `{k}` — **{pct:.1f}%**")
    return "\n".join(md)

# =========================
# Rerolls
# =========================

def reroll_section(name: str, timeline: str, domain: str, base: Picks) -> Picks:
    """Reroll one domain deterministically (using a domain salt) while keeping others locked."""
    locks = {d: getattr(base, d) for d in DOMAINS if d != domain}
    return pick_all(name, timeline, lock=locks, salt=f"reroll:{domain}")

# =========================
# CLI / Interactive
# =========================

def parse_args(argv: List[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Life Goals Predictor 2050 — deterministic, synergistic, and fun.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    ap.add_argument("--name", type=str, help="Your name")
    ap.add_argument("--timeline", type=str, default="prime", help="Timeline seed (try: prime, neon, eco, creator, zen)")
    ap.add_argument("--reroll", type=str, choices=DOMAINS, help="Reroll only this section (locks the rest)")
    ap.add_argument("--mc", type=int, default=0, help="Monte Carlo trial count for probability bars (0 to skip)")
    ap.add_argument("--json", action="store_true", help="Output JSON instead of story (stdout)")
    ap.add_argument("--md", action="store_true", help="Output Markdown card instead of story (stdout)")
    ap.add_argument("--out", type=str, help="Write JSON/Markdown to this file instead of stdout")
    return ap.parse_args(argv)

def run(name: str, timeline: str, reroll: str = None, mc_trials: int = 0, od_json=False, od_md=False, out_path: str = None):
    if not name:
        name = input("Enter your name: ").strip()
        if not name:
            print("Name cannot be empty.")
            sys.exit(1)
    if not timeline:
        timeline = (input("Timeline seed (Enter for 'prime'): ").strip() or "prime")

    # First pick
    base = pick_all(name, timeline)
    p = reroll_section(name, timeline, reroll, base) if reroll else base

    story = narrative(name, p, timeline)

    counts = None
    if mc_trials and mc_trials > 0:
        counts = monte_carlo(name, timeline, n=mc_trials)

    # Output selection
    if od_json:
        payload = to_json(name, timeline, p, counts, mc_trials)
    elif od_md:
        payload = to_markdown(name, timeline, story, p, counts, mc_trials)
    else:
        # Human-friendly console view
        print("\nLife Goals Predictor 2050 📅")
        print(f"Name: {name} | Timeline: {timeline}\n")
        print(story + "\n")
        print("Why this result:")
        for line in explanation(p):
            print(" - " + line)
        if counts:
            print("\nProbability outlook (Monte Carlo):")
            print(prob_bars(counts, mc_trials))
        return

    # If JSON/MD was requested:
    if out_path:
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(payload)
            print(f"Wrote output → {out_path}")
        except Exception as e:
            print(payload)
            print(f"\n[warning] Failed to write file: {e}\nAbove is the output printed to stdout.")
    else:
        print(payload)

def main():
    args = parse_args(sys.argv[1:])
    run(
        name=args.name,
        timeline=args.timeline,
        reroll=args.reroll,
        mc_trials=args.mc,
        od_json=args.json,
        od_md=args.md,
        out_path=args.out
    )

if __name__ == "__main__":
    main()