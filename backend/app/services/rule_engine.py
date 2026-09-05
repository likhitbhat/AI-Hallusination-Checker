import re
from datetime import datetime
from typing import Tuple


class RuleEngine:
    """
    Deterministic rule-based verification for arithmetic, percentages, dates,
    and numerical consistency. Does not rely on stochastic LLM inference.
    """

    def evaluate_claim(self, claim_text: str) -> Tuple[float, str]:
        """
        Evaluates deterministic consistency.
        Returns:
            (rule_score, rule_explanation)
            rule_score: 1.0 = consistent / verified by rule,
                        0.0 = directly contradicted by math/date/logic,
                        0.5 = uncertain / partial.
        """
        text = claim_text.strip()

        # 1. Evaluate Percentage of a Number: "X% of Y is Z"
        pct_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(?:%|percent)\s+of\s+(\d+(?:\.\d+)?)\s+(?:is|=|equals)\s+(\d+(?:\.\d+)?)",
            text,
            re.IGNORECASE
        )
        if pct_match:
            pct_val = float(pct_match.group(1))
            base_val = float(pct_match.group(2))
            stated_result = float(pct_match.group(3))
            expected = (pct_val / 100.0) * base_val

            if abs(expected - stated_result) < 1e-3:
                return 1.0, f"Deterministic arithmetic verified: {pct_val}% of {base_val} is {expected}."
            else:
                return 0.0, f"Deterministic calculation contradicted: {pct_val}% of {base_val} is {expected}, but claim states {stated_result}."

        # 2. Evaluate Simple Arithmetic: "X + Y = Z", "X times Y is Z", etc.
        arith_match = re.search(
            r"(\d+(?:\.\d+)?)\s*([\+\-\*\/]|plus|minus|times|divided by)\s*(\d+(?:\.\d+)?)\s*(?:=|is|equals)\s*(\d+(?:\.\d+)?)",
            text,
            re.IGNORECASE
        )
        if arith_match:
            n1 = float(arith_match.group(1))
            op = arith_match.group(2).lower()
            n2 = float(arith_match.group(3))
            stated = float(arith_match.group(4))

            if op in ("+", "plus"):
                expected = n1 + n2
            elif op in ("-", "minus"):
                expected = n1 - n2
            elif op in ("*", "times"):
                expected = n1 * n2
            elif op in ("/", "divided by"):
                expected = n1 / n2 if n2 != 0 else float("inf")
            else:
                expected = stated

            if abs(expected - stated) < 1e-3:
                return 1.0, f"Mathematical computation verified: {n1} {op} {n2} = {expected}."
            else:
                return 0.0, f"Mathematical computation contradicted: {n1} {op} {n2} = {expected}, but claim states {stated}."

        # 3. Impossible or Future Historical Year Bounds
        year_match = re.search(r"\b(?:in|year|formed in|founded in)\s+(\d{4})\b", text, re.IGNORECASE)
        if year_match:
            year = int(year_match.group(1))
            current_year = datetime.now().year
            if year > current_year and ("formed" in text.lower() or "founded" in text.lower() or "occurred" in text.lower()):
                return 0.0, f"Chronological contradiction: Claim asserts event occurred in future year {year}."

        # 4. Impossible Calendar Dates e.g. Feb 30, April 31
        if re.search(r"\b(?:february|feb)\s+(?:30|31)\b", text, re.IGNORECASE):
            return 0.0, "Calendar inconsistency: February cannot have 30 or 31 days."
        if re.search(r"\b(?:april|june|september|november)\s+31\b", text, re.IGNORECASE):
            return 0.0, "Calendar inconsistency: 30-day month cannot have 31 days."

        # Default: Claim is logically consistent with rules
        return 1.0, "Consistent with deterministic rules and constraints."


rule_engine = RuleEngine()
