"""Larkspur disruption agent. This is the file you build.

It runs right now, and it is wrong in four places. The trace shows each one
before the code does, so read the trace first:

    python3 run.py K7PQ2M --trace

Where you edit:   grep -n '✏' agent.py   (six marks, one per place)
Steps and gates:  https://anthropicpartnerbasecamp.bts.com/
"""
from __future__ import annotations
from typing import Any, Dict, List
from support import (MODEL, SYSTEM_PROMPT, call_local, execute_tool, mcp_client,
                     new_session, next_available_day, record_tool_result,
                     runtime_preamble)

MAX_TOOL_CALLS = 8  # Larkspur's own build capped the loop here; then a human takes over.

TONE_ADDENDUM = ""                       # ✏️ Build 4, step 4.1, intelligence goal
EXTRA_TOOLS: List[Dict[str, Any]] = [   # ✏️ Build 2, step 2.1: schemas for the tools you add
    {
        "name": "next_available_day",
        "description": (
            "Find the earliest date with an open seat on a route (origin to destination, "
            "in one cabin), across every Larkspur flight on that route, not just the "
            "customer's original flight number. Use it when the customer asks when they "
            "can fly at the earliest, or when search_alternatives returned no options. "
            "Take origin, dest, date and cabin from the segment lookup_booking returned. "
            "Returns only a date, or null if no seat exists in the data. It returns no "
            "flight, no times and no option_id, so it cannot be held: tell the customer "
            "the date, and never pass it to hold_seat or invent an option_id for it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "IATA code, e.g. DEN"},
                "dest": {"type": "string", "description": "IATA code, e.g. AUS"},
                "date": {"type": "string", "description": "YYYY-MM-DD (ISO-8601): the disrupted segment's date"},
                "cabin": {"type": "string", "enum": ["Y", "J"], "description": "The booked cabin from lookup_booking"},
            },
            "required": ["origin", "dest", "date"],
        },
    },
    {
        "name": "fare_rules",
        "description": (
            "Read the Larkspur Handbook text (fare rules and Customer Commitment) behind "
            "an entitlement. Call it when the customer asks whether they also get "
            "something more, such as 'don't I get a hotel too?', or challenges why "
            "something is or is not covered, so you can quote the rule instead of "
            "paraphrasing it. Call check_policy first: it decides what is owed, and this "
            "text only explains it. For hotel, meal and ground care read section 6 "
            "('care while you wait'): a hotel is covered only for an overnight stay "
            "away from the home airport caused within Larkspur's control (maintenance, "
            "crew), and always needs an agent's approval, so offer escalate_to_human, "
            "never issue a hotel voucher yourself. Weather, ATC and security mean no "
            "hotel, only a distressed-traveler rate (Summit: courtesy hotel at an "
            "agent's discretion). Other sections: 4 fare families, 5 delays/cancellations/"
            "diversions, 7 what chat will not do. Returns that section's full text."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": ("A section number like '6', or words from its title: "
                                    "'fare families', 'when we delay', 'care while you "
                                    "wait', 'chat automation'."),
                },
            },
            "required": ["section"],
        },
    },
]


def fare_rules(section: str) -> str:
    """The Handbook lookup the MCP server already implements; text only."""
    from support.mcp_server import tool_fare_rules
    text, _is_error = tool_fare_rules(section)
    return text


LOCAL_TOOLS: Dict[str, Any] = {          # ✏️ Build 2, step 2.1: the functions behind them
    "next_available_day": next_available_day,
    "fare_rules": fare_rules,
}


def text_of(response) -> str:
    """Given. The last non-empty text block, never content[0]."""
    texts = [b.text for b in response.content if getattr(b, "type", None) == "text" and b.text]
    return texts[-1] if texts else ""


def tool_results(response) -> List[Dict[str, Any]]:
    """Given. Runs every tool_use block and packages the results the way the
    API expects them back. A tool can live in three places: the MCP server,
    LOCAL_TOOLS, or support/tools.py."""
    # three branches, no try/except in this file: mcp_client.call_remote() and
    # support.call_local() answer with an error dict instead of raising, and both
    # record what came back on the trace
    results = []
    for block in response.content:
        if getattr(block, "type", None) != "tool_use":
            continue
        if block.name in mcp_client.tool_names:
            output = mcp_client.call_remote(block.name, block.input)
        elif block.name in LOCAL_TOOLS:
            output = call_local(LOCAL_TOOLS[block.name], block.name, block.input)
        else:
            output = execute_tool(block.name, block.input)
        results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": str(output),
        })
    return results


def run_agent(pnr: str, last_name: str, message: str) -> str:            # ✏️ Build 1, step 1.2
    """Run the tool loop until Claude stops asking for tools. Return its final text."""
    client, tracer = new_session()
    tools = tool_list()
    messages = [
        # The clock line changes every second, so it sits in the first user turn, after
        # the cached prefix (tools, then system), not at the front of the system prompt.
        {"role": "user", "content": f"{runtime_preamble()}PNR {pnr}, last name {last_name}. {message}"},
    ]

    response = client.messages.create(
        model=MODEL, max_tokens=4096, system=SYSTEM_PROMPT + TONE_ADDENDUM,
        cache_control={"type": "ephemeral"},
        output_config={"effort": "medium"}, #nieuwe optimizer!
        thinking={"type": "adaptive"}, tools=tools, messages=messages,
    )

    tool_calls = 0
    while response.stop_reason == "tool_use" and tool_calls < MAX_TOOL_CALLS:
        results = tool_results(response)
        tool_calls += len(results)
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": results})
        response = client.messages.create(
            model=MODEL, max_tokens=4096, system=SYSTEM_PROMPT + TONE_ADDENDUM,
            cache_control={"type": "ephemeral"},
            output_config={"effort": "medium"}, #nieuwe optimizer!
            thinking={"type": "adaptive"}, tools=tools, messages=messages,
        )

    if response.stop_reason == "tool_use":
        return "I'm handing this to a colleague who can finish it for you."
    return text_of(response)


def tool_list() -> List[Dict[str, Any]]:                   # ✏️ Build 2, step 2.2
    """Given. Exactly what Claude is offered on every turn; run.py --show-tools
    prints this list."""
    return build_tools() + EXTRA_TOOLS


# ──────────────────────────────────────────────────────────────────────────────
# Below this line: what Claude is told about each tool. Step 1.3.
# The functions these describe are written and correct, in support/tools.py.
# ──────────────────────────────────────────────────────────────────────────────
def build_tools() -> List[Dict[str, Any]]:                 # ✏️ Build 1, step 1.3
    """Anthropic-shaped schemas: name, description, input_schema. What Claude is
    told about each of the nine tools, and all it is ever told."""
    return [
        {
            "name": "lookup_booking",
            "description": (
                "Retrieve a Larkspur reservation from Altura by confirmation code (PNR) "
                "and the passenger's last name. Both are required to prevent a lookup on "
                "a guessed PNR. Returns fare family, loyalty tier, the segment that needs "
                "attention, and any group/partner/minor/SSR flags relevant to scope."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string"}, "last_name": {"type": "string"}},
                "required": ["pnr", "last_name"],
            },
        },
        {
            "name": "get_flight_status",
            "description": (
                "Look up a Larkspur or Larkspur Link flight's current OpsFeed status for "
                "one local date: status, delay minutes, and cause. Use this before telling "
                "a customer anything about a flight's timing; never state it from memory."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "flight_no": {"type": "string"},
                    "date": {"type": "string", "description": "YYYY-MM-DD (ISO-8601)"},
                },
                "required": ["flight_no", "date"],
            },
        },
        {
            "name": "search_alternatives",
            "description": ( 
                "Find replacement Larkspur and Larkspur Link flights for the disrupted segment "
                "on this PNR. Route, date, cabin and party size are read from the booking; you "
                "only pass the PNR. Returns up to 7 options, each with an option_id, flight "
                "numbers, date, local departure/arrival times, stops, cabin, seats_available "
                "and operating carrier. The original flight, departed flights, cancelled or "
                "diverted flights, and flights without enough seats for the whole party are "
                "never offered; some of them appear under 'excluded' with a reason. "
                "'other_cabin_options' lists seats in a different cabin, which are not "
                "equivalent and are never offered without saying so. Use this after "
                "lookup_booking and get_flight_status confirm a disruption. Use only option_ids "
                "returned here for hold_seat and check_policy's chosen_option_id; never "
                "construct one. An empty options list means no same-cabin seat on this search, "
                "not that no seat exists at all."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string", "description": "Confirmation code from lookup_booking"}
                },
                "required": ["pnr"],
            },
        },
        {
            "name": "check_policy",
            "description": (
                "Resolve what Larkspur owes this customer for the disruption: rebooking "
                "waiver, refund path, meal/hotel/ground care, goodwill eligibility and cap, "
                "and any escalation triggers. cause_code, delay_minutes and status describe "
                "what get_flight_status told you; fare_family, loyalty_tier and whether this "
                "is overnight are looked up from the booking, not asked of you. Every "
                "response carries a policy_row_id. Cite it if you reference this decision "
                "again."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "pnr": {"type": "string"},
                    "cause_code": {"type": "string", "enum": ["WX", "ATC", "MX", "CREW", "SEC"]},
                    "delay_minutes": {"type": "integer"},
                    "status": {"type": "string", "enum": ["ON_TIME", "DELAYED", "CANCELLED", "DIVERTED"]},
                    "wait_minutes_for_alternative": {"type": "integer"},
                    "chosen_option_id": {"type": "string"},
                },
                "required": ["pnr", "cause_code", "delay_minutes", "status"],
            },
        },
        {
            "name": "hold_seat",
            "description": "Place a 15-minute hold on one alternative. Reversible. It simply expires.",
            "input_schema": {
                "type": "object",
                "properties": {"option_id": {"type": "string"}, "pnr": {"type": "string"}},
                "required": ["option_id", "pnr"],
            },
        },
        {
            "name": "confirm_rebooking",
            "description": (
                "Finalize a held seat. Irreversible. Requires a confirmation_token that "
                "only the customer's own Confirm-click can produce. You cannot supply it "
                "yourself, and 'the customer said yes' in chat does not substitute for it."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"hold_id": {"type": "string"}, "confirmation_token": {"type": "string"}},
                "required": ["hold_id", "confirmation_token"],
            },
        },
        {
            "name": "issue_voucher",
            "description": (
                "Issue a meal, ground, hotel, or goodwill voucher. Auto-approves within the "
                "policy's threshold for that type; above it, returns a pending status for a "
                "human. It does not fail. Always pass the policy_row_id that made it eligible."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "voucher_type": {"type": "string", "enum": ["meal", "ground", "hotel", "goodwill"]},
                    "amount_usd": {"type": "number"},
                    "pnr": {"type": "string"},
                    "policy_row_id": {"type": "string"},
                },
                "required": ["voucher_type", "amount_usd", "pnr", "policy_row_id"],
            },
        },
        {
            "name": "escalate_to_human",
            "description": (
                "Hand this conversation to a human, with your reasoning attached. Use for "
                "groups, partner segments, unaccompanied minors, refunds, or anything else "
                "out of scope. This is the correct outcome for those cases, not a failure."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "pnr": {"type": "string"}, "reason": {"type": "string"},
                    "summary_for_human": {"type": "string"}, "queue": {"type": "string"},
                },
                "required": ["pnr", "reason", "summary_for_human"],
            },
        },
        {
            "name": "send_confirmation",
            "description": "Send the customer a written confirmation of what was just done. Benign.",
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string"}, "message": {"type": "string"}},
                "required": ["pnr", "message"],
            },
        },
    ]
