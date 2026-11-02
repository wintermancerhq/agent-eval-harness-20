"""Deterministic pre-execution guardrail for ParcelDesk support tool calls."""
from __future__ import annotations
import re
from typing import Any

MUTATING_TOOLS = {"issue_refund", "reship_replacement", "change_plan_tier"}
HYPOTHETICAL_PATTERNS = re.compile(
    r"\b(what happens if|would i get|if i cancel|if i returned|how much would|can you tell me the policy|where is my package|tracking update)\b",
    re.IGNORECASE,
)
ADDRESS_CHANGE_PATTERNS = re.compile(
    r"\b(moved|new apartment|new address|different address|updated address)\b",
    re.IGNORECASE,
)


def evaluate_baseline_dispatch(turn: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    """Naive type-only dispatcher typical of unguarded tool-calling wrappers."""
    tool = turn.get("tool")
    args = turn.get("arguments") or {}
    if not tool or tool == "none":
        return {"executed_mutating": False, "tool": "none", "arguments": {}, "blocked_reason": None}
    if tool == "lookup_order":
        ok = isinstance(args.get("order_id"), str) and bool(args["order_id"])
        return {"executed_mutating": False, "tool": tool if ok else "error", "arguments": args, "blocked_reason": None}
    if tool == "issue_refund":
        ok = (
            isinstance(args.get("order_id"), str)
            and bool(args["order_id"])
            and type(args.get("amount_cents")) is int
            and args["amount_cents"] > 0
            and isinstance(args.get("reason_code"), str)
            and bool(args["reason_code"])
        )
        return {"executed_mutating": ok, "tool": tool, "arguments": args, "blocked_reason": None if ok else "type_error"}
    if tool == "reship_replacement":
        ok = all(isinstance(args.get(k), str) and args[k] for k in ("order_id", "sku", "shipping_postal_code"))
        return {"executed_mutating": ok, "tool": tool, "arguments": args, "blocked_reason": None if ok else "type_error"}
    if tool == "change_plan_tier":
        ok = all(isinstance(args.get(k), str) and args[k] for k in ("subscription_id", "target_plan", "effective_timing"))
        return {"executed_mutating": ok, "tool": tool, "arguments": args, "blocked_reason": None if ok else "type_error"}
    return {"executed_mutating": False, "tool": tool, "arguments": args, "blocked_reason": "unknown_tool"}


def evaluate_repaired_dispatch(
    turn: dict[str, Any], session: dict[str, Any], user_message: str
) -> dict[str, Any]:
    """Strict schema + context-provenance guardrail executed before any mutating handler."""
    tool = turn.get("tool")
    args = turn.get("arguments") or {}
    customer_id = session["customer_id"]
    owned_orders = {
        o["order_id"]: o for o in session.get("orders", []) if o.get("customer_id") == customer_id
    }
    owned_subs = {
        s["subscription_id"]: s for s in session.get("subscriptions", []) if s.get("customer_id") == customer_id
    }

    def block(reason: str) -> dict[str, Any]:
        return {
            "executed_mutating": False,
            "tool": "ask_clarification",
            "arguments": {"reason": reason},
            "blocked_reason": reason,
        }

    if not tool or tool in ("none", "ask_clarification"):
        return {
            "executed_mutating": False,
            "tool": "ask_clarification" if tool == "ask_clarification" else "none",
            "arguments": args,
            "blocked_reason": None,
        }

    if tool == "lookup_order":
        oid = args.get("order_id", "")
        if oid not in owned_orders:
            return block("unowned_identifier")
        return {"executed_mutating": False, "tool": "lookup_order", "arguments": {"order_id": oid}, "blocked_reason": None}

    if tool not in MUTATING_TOOLS:
        return block("unknown_tool")

    # 1. Explicit action intent check (blocks hypothetical / status-only turns)
    if HYPOTHETICAL_PATTERNS.search(user_message):
        return block("non_mutating_intent")
    quote = args.get("user_intent_quote", "")
    if not isinstance(quote, str) or len(quote.strip()) < 6 or quote.lower() not in user_message.lower():
        return block("missing_intent_quote")

    # 2. Tool-specific provenance checks
    if tool == "issue_refund":
        oid = args.get("order_id", "")
        if oid not in owned_orders:
            return block("unowned_identifier")
        if oid.lower() not in user_message.lower() and len(owned_orders) != 1:
            return block("ambiguous_record")
        order = owned_orders[oid]
        amt = args.get("amount_cents")
        cap = session.get("policy_max_auto_refund_cents", 10000)
        if type(amt) is not int or amt < 100:
            return block("unverified_amount")
        if amt > cap:
            return block("policy_cap_exceeded")

        basis = args.get("amount_basis")
        msg_lower = user_message.lower()
        shipping_only_ask = bool(
            re.search(r"refund\s+(?:only\s+)?(?:the\s+)?(?:\w+\s+)?shipping(?:\s+(?:fee|charge|cost))?\b", msg_lower)
        )
        if shipping_only_ask and "full" not in msg_lower and basis == "full_order":
            return block("unverified_amount")
        allowed_amounts = {
            "full_order": {order["total_cents"]},
            "shipping_only": {order["shipping_cents"]} if order.get("shipping_cents", 0) > 0 else set(),
            "line_item": {it["price_cents"] for it in order.get("items", [])},
            "verified_credit": {order["verified_credit_cents"]} if order.get("verified_credit_cents") else set(),
        }
        if basis not in allowed_amounts or amt not in allowed_amounts[basis]:
            return block("unverified_amount")
        return {"executed_mutating": True, "tool": tool, "arguments": args, "blocked_reason": None}

    if tool == "reship_replacement":
        oid = args.get("order_id", "")
        if oid not in owned_orders:
            return block("unowned_identifier")
        if oid.lower() not in user_message.lower() and len(owned_orders) != 1:
            return block("ambiguous_record")
        order = owned_orders[oid]
        items = order.get("items", [])
        sku = args.get("sku", "")
        matched_items = [it for it in items if it["sku"] == sku]
        if not matched_items:
            return block("missing_parameter")
        if len(items) > 1:
            item_label = matched_items[0]["name"].lower()
            if sku.lower() not in user_message.lower() and item_label not in user_message.lower():
                return block("ambiguous_record")
        postal = args.get("shipping_postal_code", "")
        if ADDRESS_CHANGE_PATTERNS.search(user_message):
            if postal not in user_message:
                return block("missing_parameter")
        elif postal != order.get("postal_code"):
            return block("missing_parameter")
        return {"executed_mutating": True, "tool": tool, "arguments": args, "blocked_reason": None}

    if tool == "change_plan_tier":
        sid = args.get("subscription_id", "")
        if sid not in owned_subs:
            return block("unowned_identifier")
        if sid.lower() not in user_message.lower() and len(owned_subs) != 1:
            return block("ambiguous_record")
        timing = args.get("effective_timing")
        msg_lower = user_message.lower()
        if timing == "immediate" and not re.search(r"\b(now|immediately|today|right away)\b", msg_lower):
            return block("missing_parameter")
        if timing == "period_end" and not re.search(r"\b(renewal|period end|end of|next cycle|billing cycle)\b", msg_lower):
            return block("missing_parameter")
        if timing not in ("immediate", "period_end"):
            return block("missing_parameter")
        return {"executed_mutating": True, "tool": tool, "arguments": args, "blocked_reason": None}

    return block("unknown_tool")


def _self_test() -> None:
    sample_session = {
        "customer_id": "CUST-10",
        "policy_max_auto_refund_cents": 10000,
        "orders": [
            {
                "order_id": "ORD-1001",
                "customer_id": "CUST-10",
                "total_cents": 4800,
                "shipping_cents": 900,
                "verified_credit_cents": None,
                "postal_code": "46204",
                "items": [{"sku": "MUG-BLUE", "name": "Stoneware Mug", "price_cents": 3900}],
            }
        ],
        "subscriptions": [],
    }
    bad_turn = {
        "tool": "issue_refund",
        "arguments": {"order_id": "ORD-1001", "amount_cents": 25, "reason_code": "billing_credit"},
    }
    assert evaluate_baseline_dispatch(bad_turn, sample_session)["executed_mutating"] is True
    assert evaluate_repaired_dispatch(bad_turn, sample_session, "Apply my $25 promo code")["executed_mutating"] is False
    good_turn = {
        "tool": "issue_refund",
        "arguments": {
            "order_id": "ORD-1001",
            "amount_cents": 900,
            "amount_basis": "shipping_only",
            "reason_code": "late_shipping",
            "user_intent_quote": "refund the $9 shipping on ORD-1001",
        },
    }
    res = evaluate_repaired_dispatch(good_turn, sample_session, "Please refund the $9 shipping on ORD-1001.")
    assert res["executed_mutating"] is True and res["blocked_reason"] is None
    full_box_turn = {
        "tool": "issue_refund",
        "arguments": {
            "order_id": "ORD-1001",
            "amount_cents": 4800,
            "amount_basis": "full_order",
            "reason_code": "damaged_item",
            "user_intent_quote": "refund ORD-1001",
        },
    }
    res_box = evaluate_repaired_dispatch(full_box_turn, sample_session, "The mug broke inside the shipping box, please refund ORD-1001.")
    assert res_box["executed_mutating"] is True and res_box["blocked_reason"] is None


if __name__ == "__main__":
    _self_test()
    print("guardrail self-test passed")
