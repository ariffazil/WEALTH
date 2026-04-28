#!/bin/bash
cd /app
exec python -c "from internal.monolith import mcp; mcp.run(transport='sse', show_banner=False)"
