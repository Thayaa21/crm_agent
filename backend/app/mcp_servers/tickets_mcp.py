"""MCP server for tickets data source. Run: python -m app.mcp_servers.tickets_mcp (from backend dir)."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from mcp import types
from mcp.server import Server, ServerRequestContext
from mcp.server.stdio import stdio_server

from app.services.tickets_service import (
    get_escalated_tickets,
    get_open_tickets,
    get_ticket_volume_trend,
)


async def handle_list_tools(
    ctx: ServerRequestContext, params: types.PaginatedRequestParams | None
) -> types.ListToolsResult:
    return types.ListToolsResult(
        tools=[
            types.Tool(
                name="get_open_tickets",
                description="Get open support tickets, optionally filtered by priority.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Max number of tickets", "default": 100},
                        "priority": {"type": "string", "description": "Filter by priority (e.g. P0, P1)"},
                    },
                },
            ),
            types.Tool(
                name="get_ticket_volume_trend",
                description="Get ticket volume over time buckets (e.g. last 24h in 2h buckets).",
                input_schema={
                    "type": "object",
                    "properties": {
                        "hours": {"type": "integer", "description": "Time window in hours", "default": 24},
                        "bucket_hours": {"type": "integer", "description": "Bucket size in hours", "default": 2},
                    },
                },
            ),
            types.Tool(
                name="get_escalated_tickets",
                description="Get escalated tickets.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Max number", "default": 50},
                    },
                },
            ),
        ]
    )


async def handle_call_tool(
    ctx: ServerRequestContext, params: types.CallToolRequestParams
) -> types.CallToolResult:
    name = params.name
    args = params.arguments or {}
    try:
        if name == "get_open_tickets":
            out = get_open_tickets(limit=args.get("limit", 100), priority=args.get("priority"))
        elif name == "get_ticket_volume_trend":
            out = get_ticket_volume_trend(hours=args.get("hours", 24), bucket_hours=args.get("bucket_hours", 2))
        elif name == "get_escalated_tickets":
            out = get_escalated_tickets(limit=args.get("limit", 50))
        else:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))],
                isError=True,
            )
        text = json.dumps(out, default=str)
        return types.CallToolResult(content=[types.TextContent(type="text", text=text)])
    except Exception as e:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps({"error": str(e)}))],
            isError=True,
        )


async def main():
    app = Server(
        "tickets-mcp",
        on_list_tools=handle_list_tools,
        on_call_tool=handle_call_tool,
    )
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
