import os
import yaml
from typing import Dict, Any, List

def validate_agent_card(filepath: str) -> List[str]:
    errors = []
    if not os.path.exists(filepath):
        return [f"File does not exist: {filepath}"]

    try:
        with open(filepath, "r") as f:
            card = yaml.safe_load(f)
    except Exception as e:
        return [f"Failed to parse YAML: {e}"]

    # Required fields
    required = ["agent_id", "role", "version", "capabilities", "endpoint"]
    for field in required:
        if field not in card:
            errors.append(f"Missing required field: {field}")

    # Validation rules
    if "restrictions" not in card:
        errors.append("Missing 'restrictions' section for boundary enforcement.")

    if card.get("agent_id") == "kernel-agent":
        # Kernel must not advertise autonomous sealing
        caps = card.get("capabilities", {})
        for cap, desc in caps.items() if isinstance(caps, dict) else []:
            if "seal" in cap.lower() or "sealing" in cap.lower():
                errors.append("Violation: Kernel agent card must not advertise autonomous sealing capabilities.")

    return errors

if __name__ == "__main__":
    cards_dir = "/root/entropy-integrity/a2a/agent-cards"
    all_ok = True
    for card_file in os.listdir(cards_dir):
        if card_file.endswith(".yaml"):
            path = os.path.join(cards_dir, card_file)
            errs = validate_agent_card(path)
            if errs:
                print(f"❌ Conformance errors in {card_file}:")
                for err in errs:
                    print(f"  - {err}")
                all_ok = False
            else:
                print(f"✅ {card_file} is A2A compliant.")
    
    if not all_ok:
        exit(1)
