import json
import os
from typing import Dict, Optional

DEFAULT_RULES_PATH = os.path.join("config", "categories_rules.json")


def load_rules(path: Optional[str] = None) -> Dict[str, str]:
    path = path or DEFAULT_RULES_PATH
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def canonical_category(description: str, category: Optional[str] = None, rules: Optional[Dict[str, str]] = None) -> str:
    if category:
        return category
    rules = rules or load_rules()
    desc = (description or "").lower()
    for needle, cat in rules.items():
        if needle.lower() in desc:
            return cat
    return "Altro"