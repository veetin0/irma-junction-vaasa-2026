"""Language-model access for the agents, with an honest replay fallback.

Design rule: the LLM reads and classifies text; it never produces a number that is
used in a calculation. Numeric fields the LLM extracts (a value quoted in a source)
are stored on the card with the source excerpt, and the engine computes from them.

Modes
    live    ANTHROPIC_API_KEY (or an `ant auth login` profile) is available and
            AGENT_MODE is not "replay": real calls through the Anthropic SDK.
    replay  no credentials or AGENT_MODE=replay: pre-recorded outputs for the demo
            item and deterministic heuristics for anything else. Every replayed
            output is labelled so the UI can show it.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Type

from pydantic import BaseModel

MODEL_ID = os.environ.get("ABB_MODEL", "claude-opus-5-5")

# Deterministic guardrail: strips purchase/stocking recommendations from any LLM text.
RECOMMENDATION_PATTERNS = [
    r"\b(order|buy|purchase|procure|stock up on)\s+(\d[\d,\.]*\s*\w*|more|now|additional|extra)\b",
    r"\b(increase|raise|reduce|cut|double|triple)\s+(the\s+|your\s+)?(order|orders|purchase|purchases|stock|inventory|buffer)\b",
    r"\bwe recommend\b",
    r"\b(you|abb) should (order|buy|purchase|procure|stock)\b",
    r"\b(reorder point|safety stock of|order quantity of|optimal order)\b",
    r"\bplace (an|the) order\b",
]


# Sentences that decline to recommend are kept: they state the boundary rather than cross it.
DISCLAIMER_PATTERNS = [
    r"\b(can(no|')t|cannot|won't|will not|do(es)? not|don't|doesn't|not able to)\b.{0,60}\b(recommend|tell you|advise|decide|say)\b",
    r"\bno (purchase |order |buying )?recommendation\b",
    r"\b(decision|judg(e)?ment|call)\b.{0,40}\b(yours|belongs to|rests with|is up to|for (you|the planner))\b",
    r"\bwhether (you|abb|we) should\b.{0,80}\b(is|remains|stays) (yours|your call|a decision|for)\b",
]


def recommendation_filter(text: str) -> tuple[str, list[str]]:
    """Remove sentences that recommend purchases, quantities or order timing. Returns (clean_text, removed).

    Works line by line so bullet lists keep their structure; removed sentences leave no marker in the
    text (the UI shows how many were removed). Sentences that decline to recommend are kept.
    """
    removed: list[str] = []
    out_lines: list[str] = []
    for line in (text or "").split("\n"):
        kept = []
        for sent in re.split(r"(?<=[.!?])\s+", line):
            recommends = any(re.search(p, sent, flags=re.IGNORECASE) for p in RECOMMENDATION_PATTERNS)
            disclaims = any(re.search(p, sent, flags=re.IGNORECASE) for p in DISCLAIMER_PATTERNS)
            if recommends and not disclaims:
                removed.append(sent)
            else:
                kept.append(sent)
        joined = " ".join(x for x in kept if x).rstrip()
        stripped_marker = re.sub(r"^\s*([-*\u2022]|\d+[.)])\s*$", "", joined)
        if joined and stripped_marker:
            out_lines.append(joined)
        elif not line.strip():
            out_lines.append("")
    clean = re.sub(r"\n{3,}", "\n\n", "\n".join(out_lines)).strip()
    return clean, removed


class LLMClient:
    def __init__(self) -> None:
        requested = os.environ.get("AGENT_MODE", "auto")
        has_key = bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))
        self.mode = "live" if (requested != "replay" and (has_key or requested == "live")) else "replay"
        self._client = None
        self.last_error: str | None = None
        self.blocked_domains: set[str] = set()
        if self.mode == "live":
            try:
                import anthropic  # noqa: WPS433 (optional dependency)

                self._client = anthropic.Anthropic()
            except Exception as exc:  # pragma: no cover - environment dependent
                self.mode = "replay"
                self.last_error = f"SDK unavailable: {exc}"

    # ---- structured classification -------------------------------------------------
    def classify(self, system: str, user: str, schema: Type[BaseModel]) -> tuple[BaseModel | None, dict[str, Any]]:
        if self.mode != "live" or self._client is None:
            return None, {"mode": "replay", "model": None}
        import anthropic

        try:
            response = self._client.messages.parse(
                model=MODEL_ID,
                max_tokens=4000,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_format=schema,
            )
            if response.stop_reason == "refusal":
                self.last_error = "refusal"
                return None, {"mode": "live", "model": MODEL_ID, "error": "refusal"}
            return response.parsed_output, {"mode": "live", "model": MODEL_ID, "usage": response.usage.to_dict()}
        except anthropic.RateLimitError as exc:
            self.last_error = f"rate limited: {exc.message}"
        except anthropic.APIStatusError as exc:
            self.last_error = f"api error {exc.status_code}: {exc.message}"
        except anthropic.APIConnectionError as exc:
            self.last_error = f"connection error: {exc}"
        return None, {"mode": "live-failed", "model": MODEL_ID, "error": self.last_error}

    # ---- free text (brief, interpretation) --------------------------------------------
    def write(self, system: str, user: str) -> tuple[str | None, dict[str, Any]]:
        if self.mode != "live" or self._client is None:
            return None, {"mode": "replay", "model": None}
        import anthropic

        try:
            response = self._client.messages.create(
                model=MODEL_ID,
                max_tokens=4000,
                system=system,
                messages=[{"role": "user", "content": user}],
                # Server-side refusal fallback (opt-in by default for Claude Opus 5.5 code).
                extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"},
                extra_body={"fallbacks": "default"},
            )
            if response.stop_reason == "refusal":
                self.last_error = "refusal"
                return None, {"mode": "live", "model": MODEL_ID, "error": "refusal"}
            text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
            return text, {"mode": "live", "model": response.model, "usage": response.usage.to_dict()}
        except anthropic.RateLimitError as exc:
            self.last_error = f"rate limited: {exc.message}"
        except anthropic.APIStatusError as exc:
            self.last_error = f"api error {exc.status_code}: {exc.message}"
        except anthropic.APIConnectionError as exc:
            self.last_error = f"connection error: {exc}"
        return None, {"mode": "live-failed", "model": MODEL_ID, "error": self.last_error}


    # ---- research with web search / fetch (server-side tools) ---------------------------
    def research(self, system: str, user: str, web: dict[str, Any], extra_domains: list[str] | None = None,
                 max_continuations: int = 2) -> tuple[str | None, dict[str, Any] | None, dict[str, Any]]:
        """Run one agent turn with web search and fetch. Returns (text, evidence, meta).

        Handles pause_turn by re-sending the accumulated assistant turn (no extra user message),
        at most max_continuations times. If the API rejects domains its search tool cannot access,
        those domains are remembered in self.blocked_domains and the call is retried without them
        (meta["dropped_domains"] lists them). On any other API error returns (None, None, meta) so
        the calling agent can fall back to its non-search path.
        """
        if self.mode != "live" or self._client is None:
            return None, None, {"mode": "replay", "model": None}
        import anthropic
        from agents.web import allowed_after_exclusion, build_tools, collect_web_evidence, parse_blocked_domains, response_text

        usage = {"input_tokens": 0, "output_tokens": 0, "web_search_requests": 0, "web_fetch_requests": 0, "requests": 0}
        dropped: list[str] = []
        for attempt in range(3):
            if (web.get("allowed_domains") or extra_domains) and not allowed_after_exclusion(web, extra_domains, self.blocked_domains):
                self.last_error = "no accessible domains left in the allowlist"
                return None, None, {"mode": "live-failed", "model": MODEL_ID, "error": self.last_error, "usage": usage, "dropped_domains": dropped}
            tools = build_tools(web, extra_domains, exclude=self.blocked_domains)
            blocks: list[Any] = []
            messages: list[dict[str, Any]] = [{"role": "user", "content": user}]
            stop = None
            try:
                for _ in range(max_continuations + 1):
                    response = self._client.messages.create(model=MODEL_ID, max_tokens=12000, system=system, tools=tools, messages=messages)
                    usage["requests"] += 1
                    u = getattr(response, "usage", None)
                    usage["input_tokens"] += int(getattr(u, "input_tokens", 0) or 0)
                    usage["output_tokens"] += int(getattr(u, "output_tokens", 0) or 0)
                    stu = getattr(u, "server_tool_use", None)
                    usage["web_search_requests"] += int(getattr(stu, "web_search_requests", 0) or 0)
                    usage["web_fetch_requests"] += int(getattr(stu, "web_fetch_requests", 0) or 0)
                    blocks.extend(response.content)
                    stop = response.stop_reason
                    if stop == "refusal":
                        self.last_error = "refusal"
                        return None, None, {"mode": "live+web", "model": MODEL_ID, "error": "refusal", "usage": usage, "dropped_domains": dropped}
                    if stop != "pause_turn":
                        break
                    messages = [{"role": "user", "content": user}, {"role": "assistant", "content": list(blocks)}]
            except anthropic.BadRequestError as exc:
                blocked = [d for d in parse_blocked_domains(str(exc.message)) if d not in self.blocked_domains]
                if blocked and attempt < 2:
                    self.blocked_domains.update(blocked)
                    dropped.extend(blocked)
                    continue
                self.last_error = f"bad request: {exc.message}"
            except anthropic.RateLimitError as exc:
                self.last_error = f"rate limited: {exc.message}"
            except anthropic.APIStatusError as exc:
                self.last_error = f"api error {exc.status_code}: {exc.message}"
            except anthropic.APIConnectionError as exc:
                self.last_error = f"connection error: {exc}"
            else:
                evidence = collect_web_evidence(blocks)
                evidence["searches"] = usage["web_search_requests"]
                evidence["fetches"] = usage["web_fetch_requests"]
                meta = {"mode": "live+web", "model": MODEL_ID, "usage": usage, "stop_reason": stop, "dropped_domains": dropped}
                if stop == "pause_turn":
                    meta["note"] = f"still paused after {max_continuations} continuations; using what was retrieved"
                return response_text(blocks), evidence, meta
            break
        return None, None, {"mode": "live-failed", "model": MODEL_ID, "error": self.last_error, "usage": usage, "dropped_domains": dropped}


def load_replay(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)
