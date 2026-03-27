#!/usr/bin/env python3
"""
Auto-update agent MEMORY.md with learned trading rules.
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
RULES_FILE = DATA_DIR / "learned_rules.json"


def load_rules():
    if not RULES_FILE.exists():
        return None
    with open(RULES_FILE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def generate_memory_section(rules_data):
    if not rules_data or not rules_data.get("rules"):
        return None

    rules = rules_data["rules"]
    generated_at = rules_data.get("generated_at", datetime.now().isoformat())
    prefer_rules = [rule for rule in rules if rule["type"] == "PREFER"]
    avoid_rules = [rule for rule in rules if rule["type"] == "AVOID"]

    section = f"""

---

## LEARNED RULES (Auto-Generated)

*Last updated: {datetime.fromisoformat(generated_at).strftime('%Y-%m-%d %H:%M')}*
*Based on {rules_data.get('total_rules', len(rules))} patterns from trade history*

### PREFER (High Win Rate Patterns)

"""

    if prefer_rules:
        for rule in prefer_rules:
            confidence = "HIGH" if rule["confidence"] == "HIGH" else "MEDIUM"
            section += f"- **{rule['rule']}** ({rule['evidence']}) [{confidence}]\n"
    else:
        section += "- *No high-confidence PREFER rules yet*\n"

    section += "\n### AVOID (Low Win Rate Patterns)\n\n"

    if avoid_rules:
        for rule in avoid_rules:
            confidence = "HIGH" if rule["confidence"] == "HIGH" else "MEDIUM"
            section += f"- **{rule['rule']}** ({rule['evidence']}) [{confidence}]\n"
    else:
        section += "- *No high-confidence AVOID rules yet*\n"

    section += """
### How to Use These Rules

1. **Before opening a trade:** Check if any AVOID rules apply
2. **When conditions match PREFER:** Consider the setup more seriously
3. **Confidence levels:** HIGH = 10+ trades, MEDIUM = 5-9 trades

> These rules are learned from YOUR trading history. They reflect your actual performance, not theoretical strategies.

"""

    return section


def update_memory_file(memory_path, dry_run=False):
    rules_data = load_rules()
    if not rules_data:
        print("No learned rules found. Run generate_rules.py first.")
        return False

    new_section = generate_memory_section(rules_data)
    if not new_section:
        print("Could not generate rules section.")
        return False

    memory_path = Path(memory_path)
    if not memory_path.exists():
        print(f"Memory file not found: {memory_path}")
        return False

    with open(memory_path, "r", encoding="utf-8") as handle:
        content = handle.read()

    pattern = r"\n---\n\n## LEARNED RULES \(Auto-Generated\).*?(?=\n---\n|\n## |\Z)"
    content = re.sub(pattern, "", content, flags=re.DOTALL).rstrip()
    new_content = content + new_section

    if dry_run:
        print("DRY RUN - Would add this section:\n")
        print("=" * 50)
        print(new_section)
        print("=" * 50)
        return True

    with open(memory_path, "w", encoding="utf-8") as handle:
        handle.write(new_content)

    print(f"Updated: {memory_path}")
    print(f"Added {len(rules_data['rules'])} learned rules")
    return True


def main():
    parser = argparse.ArgumentParser(description="Update MEMORY.md with learned rules")
    parser.add_argument("--memory-path", required=True, help="Path to MEMORY.md")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    success = update_memory_file(args.memory_path, args.dry_run)
    if success and not args.dry_run:
        print("\nAgent memory updated with learned trading rules.")
        print("The agent will now consider these patterns in future trades.")


if __name__ == "__main__":
    main()
