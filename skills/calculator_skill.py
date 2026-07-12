"""Safe calculator skill for evaluating arithmetic expressions."""

from __future__ import annotations

import ast
import logging
import operator
import re
from typing import Optional

logger = logging.getLogger(__name__)

_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
}

_ALLOWED_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class CalculatorSkill:
    """Evaluate simple arithmetic expressions safely."""

    def execute(self, text: str) -> Optional[str]:
        """Return a calculation result for the provided expression."""
        logger.info("CalculatorSkill executed with text: %s", text)
        expression = self._extract_expression(text)
        if not expression:
            return None

        if text.lower().startswith("what is"):
            expression = text.replace("what is", "", 1).strip()

        if text.lower().startswith("calculate"):
            expression = text.replace("calculate", "", 1).strip()

        if expression.lower().startswith("what is"):
            expression = expression.replace("what is", "", 1).strip()

        if expression.lower().startswith("calculate"):
            expression = expression.replace("calculate", "", 1).strip()

        if re.search(r"\bof\b", expression.lower()):
            return self._handle_percentage(expression)

        try:
            value = self._eval_expression(expression)
        except (ValueError, SyntaxError, ZeroDivisionError) as exc:
            logger.warning("Calculator evaluation failed: %s", exc)
            return "I could not calculate that."

        return str(value)

    def _extract_expression(self, text: str) -> Optional[str]:
        """Extract a calculator expression from the input text."""
        cleaned = text.strip().lower()
        if not cleaned:
            return None

        if cleaned.startswith("calculate"):
            cleaned = cleaned.replace("calculate", "", 1).strip()

        if not cleaned:
            return None

        if any(char in cleaned for char in ["+", "-", "*", "/", "%", "(", ")", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]):
            return cleaned
        return None

    def _handle_percentage(self, expression: str) -> str:
        """Handle percentage expressions like 20% of 500."""
        match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)", expression, flags=re.IGNORECASE)
        if not match:
            return "I could not calculate that."

        percent = float(match.group(1))
        total = float(match.group(2))
        return str((percent / 100) * total)

    def _eval_expression(self, expression: str) -> float:
        """Safely evaluate an arithmetic expression using AST."""
        tree = ast.parse(expression, mode="eval")
        return self._eval_node(tree.body)

    def _eval_node(self, node: ast.AST) -> float:
        """Evaluate an AST node recursively."""
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)

        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return _ALLOWED_BINOPS[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
            operand = self._eval_node(node.operand)
            return _ALLOWED_UNARYOPS[type(node.op)](operand)

        if isinstance(node, ast.Expression):
            return self._eval_node(node.body)

        raise ValueError("Unsupported expression")
