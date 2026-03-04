"""MCP server for NPS data source. Run: python -m app.mcp_servers.nps_mcp (from backend dir)."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from mcp import types
from mcp.server import Server, ServerRequestContext
from mcp.server.stdio import stdio_server

from app.services.nps_service import (
    get_current_nps_score,
    get_detractor_feedback,
    get_nps_trend,
)


async def handle_list_tools(
    ctx: ServerRequestContext, params: types.PaginatedRequestParams | None
) -> types.ListToolsResult:
    return types.ListToolsResult(
        tools=[
            types.Tool(
                name="get_current_nps_score",
                description="Get current NPS score (last 30 days).",
                input_schema={"type": "object", "properties": {}},
            ),
            types.Tool(
                name="get_nps_trend",
                description="Get NPS trend over time (weekly buckets).",
                input_schema={
                    "type": "object",
                    "properties": {
                        "days": {"type": "integer", "description": "Days to look back", "default": 30},
                        "bucket_days": {"type": "integer", "description": "Bucket size in days", "default": 7},
                    },
                },
            ),
            types.Tool(
                name="get_detractor_feedback",
                description="Get feedback from detractors (score <= 6).",
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
        if name == "get_current_nps_score":
            out = get_current_nps_score()
        elif name == "get_nps_trend":
            out = get_nps_trend(days=args.get("days", 30), bucket_days=args.get("bucket_days", 7))
        elif name == "get_detractor_feedback":
            out = get_detractor_feedback(limit=args.get("limit", 50))
        else:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))],
                isError=True,
            )
        text = json.dumps(out) if isinstance(out, (int, float)) else json.dumps(out, default=str)
        return types.CallToolResult(content=[types.TextContent(type="text", text=text)])
    except Exception as e:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps({"error": str(e)}))],
            isError=True,
        )


async def main():
    app = Server(
        "nps-mcp",
        on_list_tools=handle_list_tools,
        on_call_tool=handle_call_tool,
    )
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
