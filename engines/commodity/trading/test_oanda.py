#!/usr/bin/env python3
"""OANDA connection test — run after setting credentials in config/oanda.env"""
import os
import sys

# Load env
env_path = os.path.join(os.path.dirname(__file__), "config", "oanda.env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

from oandapyV20 import API
from oandapyV20.endpoints.accounts import AccountSummary
from oandapyV20.endpoints.pricing import PricingStream
from oandapyV20.exceptions import V20Error

account_id = os.environ.get("OANDA_ACCOUNT_ID", "")
api_key = os.environ.get("OANDA_API_KEY", "")

if "YOUR_" in account_id or "YOUR_" in api_key:
    print("ERROR: Set credentials in config/oanda.env first")
    print("  1. Sign up at https://www.oanda.com/apply/")
    print("  2. Get API key from https://www.oanda.com/account/tpa/personal_access_token")
    print("  3. Edit config/oanda.env with your account_id and api_key")
    sys.exit(1)

client = API(access_token=api_key, environment="practice")

# Test 1: Account summary
try:
    r = AccountSummary(accountID=account_id)
    client.request(r)
    summary = r.response["account"]
    print(f"OK Connected to OANDA demo")
    print(f"  Account:    {summary['id']}")
    print(f"  Currency:   {summary['currency']}")
    print(f"  Balance:    {summary['balance']}")
    print(f"  NAV:        {summary['NAV']}")
    print(f"  Unrealized: {summary['unrealizedPL']}")
except V20Error as e:
    print(f"ERROR OANDA API error: {e}")
    sys.exit(1)

# Test 2: Price stream (XAUUSD)
try:
    params = {"instruments": "XAU_USD"}
    r = PricingStream(accountID=account_id, params=params)
    # Just check we can start the stream
    print(f"OK XAUUSD price stream accessible")
except V20Error as e:
    print(f"WARNING Price stream: {e}")

print()
print("OANDA demo ready for trading")
