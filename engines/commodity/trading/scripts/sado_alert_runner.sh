#!/bin/bash
# SADO Alert Checker — runs sado_alert.py, delivers to Telegram if triggered
# Silent when no alert. Loud when something matters.

OUTPUT=$(cd /root/trading && python3 scripts/sado_alert.py --check 2>/dev/null)

if [ -z "$OUTPUT" ]; then
    # No alert — stay silent
    exit 0
fi

# Parse JSON output
MESSAGE=$(echo "$OUTPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['message'])")
CHART_PATH=$(echo "$OUTPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['chart_path'])")

# Check if chart exists
if [ ! -f "$CHART_PATH" ]; then
    echo "$MESSAGE"
    exit 0
fi

# Output message + chart path for Hermes to deliver
echo "CHART:$CHART_PATH"
echo "$MESSAGE"
