"""Plain wording of the recommendation templates (contract C13, M5.3).

Covers data/recommendations.json and data/segments/oilgas/recommendations.json: no internal terms in any visible
text, an EN and a FI text everywhere, and short sentences.
Run from app/:  DEMO_TODAY=2026-10-03 python3 -m pytest tests -q
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

os.environ.setdefault("DEMO_TODAY", "2026-10-03")
BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from engine.recommend import template_texts  # noqa: E402

FILES = {
    "datacentre": BACKEND / "data" / "recommendations.json",
    "oilgas": BACKEND / "data" / "segments" / "oilgas" / "recommendations.json",
}
TEMPLATES = {name: json.loads(path.read_text(encoding="utf-8")) for name, path in FILES.items()}

# Words of the code and the maths that must not reach a planner. "contingent" is the internal type value; the
# visible word is "conditional".
INTERNAL_TERMS = re.compile(r"no[_ -]?regret|hedge|kernel|contingent", re.IGNORECASE)
# Finnish: one term per concept. These are the variants the glossary rules out.
FI_BANNED = re.compile(r"horisont|vastaesitys|vastanäyttö|vasta-argument|S&OP-kokous", re.IGNORECASE)
MAX_WORDS = 25
PLACEHOLDER = re.compile(r"\{[a-z_]+\}")


def _notes(t: dict) -> list[str]:
    return [t["_note"], t["confidence_rules"]["note"], t["defaults"]["note"]]


def _pairs(node, path=()):
    """Every dict that carries an 'en' or a 'fi' key, with its path."""
    if isinstance(node, dict):
        if "en" in node or "fi" in node:
            yield path, node
        else:
            for k, v in node.items():
                yield from _pairs(v, path + (k,))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _pairs(v, path + (str(i),))


def _sentences(text: str) -> list[str]:
    plain = PLACEHOLDER.sub("X", text.strip())
    return [s for s in re.split(r"(?<=[.!?])\s+", plain) if s]


def test_both_files_exist_and_have_the_same_shape():
    assert set(TEMPLATES["datacentre"]) == set(TEMPLATES["oilgas"])
    assert len(TEMPLATES["datacentre"]["archetypes"]) == 9 and len(TEMPLATES["oilgas"]["archetypes"]) == 8


def test_no_internal_terms_in_any_visible_text():
    for name, t in TEMPLATES.items():
        for text in template_texts(t) + _notes(t):
            assert not INTERNAL_TERMS.search(text), (name, text)


def test_every_en_text_has_a_fi_text_and_back():
    for name, t in TEMPLATES.items():
        pairs = list(_pairs({k: v for k, v in t.items() if not k.startswith("_")}))
        assert len(pairs) > 80, name
        for path, p in pairs:
            where = (name, ".".join(path))
            assert set(p) == {"en", "fi"}, where
            assert isinstance(p["en"], str) and isinstance(p["fi"], str), where
            assert p["en"].strip() and p["fi"].strip(), where
            if len(p["en"].split()) > 2:
                assert p["en"] != p["fi"], where           # a Finnish text that is a copy of the English one
            # the same placeholders in both languages, so the code can fill either
            assert sorted(PLACEHOLDER.findall(p["en"])) == sorted(PLACEHOLDER.findall(p["fi"])), where


def test_sentences_are_short():
    for name, t in TEMPLATES.items():
        for text in template_texts(t):
            for s in _sentences(text):
                assert len(s.split()) <= MAX_WORDS, (name, len(s.split()), s)


def test_headline_and_hedge_stay_short_once_filled_in():
    """The headline and the first hedge sentence splice a move and a shift into a template, with scenario names."""
    for name, t in TEMPLATES.items():
        for lang, nm, pr in (("en", "Name Name Name", "40%"), ("fi", "Nimi Nimi Nimi", "40 %")):
            for aid, a in t["archetypes"].items():
                headline = t["headline_template"][lang].format(confidence=t["confidence_labels"]["medium"][lang], name=nm, probability=pr, move=a["headline_move"][lang])
                hedge = t["hedge_template"][lang].format(runner=nm, runner_p=pr, lead=nm, shift=a["if_leading"][lang])
                for text in (headline, hedge):
                    for s in _sentences(text):
                        assert len(s.split()) <= MAX_WORDS, (name, aid, lang, len(s.split()), s)


def test_one_action_per_move_line_and_no_digits():
    for name, t in TEMPLATES.items():
        for aid, a in t["archetypes"].items():
            for m in a["moves"]:
                for lang in ("en", "fi"):
                    assert not re.search(r"\d", m["text"][lang]), (name, aid, m["text"][lang])
                    assert m["text"][lang].rstrip().endswith("."), (name, aid, m["text"][lang])
                    assert ";" not in m["text"][lang], (name, aid, m["text"][lang])  # two actions on one line


def test_finnish_uses_one_term_per_concept():
    for name, t in TEMPLATES.items():
        fi = [p["fi"] for _, p in _pairs({k: v for k, v in t.items() if not k.startswith("_")})]
        for text in fi:
            assert not FI_BANNED.search(text), (name, text)
