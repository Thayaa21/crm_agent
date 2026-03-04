"""MCP server for reviews data source. Run: python -m app.mcp_servers.reviews_mcp (from backend dir)."""
import asyncio
import json
import sys
from pathlib import Path

# Ensure backend is on path when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from mcp import types
from mcp.server import Server, ServerRequestContext
from mcp.server.stdio import stdio_server

from app.services.reviews_service import (
    get_recent_reviews,
    get_reviews_by_product,
    get_sentiment_trend,
)


async def handle_list_tools(
    ctx: ServerRequestContext, params: types.PaginatedRequestParams | None
) -> types.ListToolsResult:
    return types.ListToolsResult(
        tools=[
            types.Tool(
                name="get_recent_reviews",
                description="Get most recent customer reviews. Use limit and optional hours to filter.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Max number of reviews", "default": 50},
                        "hours": {"type": "integer", "description": "Only reviews from last N hours", "default": None},
                    },
                },
            ),
            types.Tool(
                name="get_sentiment_trend",
                description="Get average sentiment trend over time buckets (e.g. last 24h in 4h buckets).",
                input_schema={
                    "type": "object",
                    "properties": {
                        "hours": {"type": "integer", "description": "Time window in hours", "default": 24},
                        "bucket_hours": {"type": "integer", "description": "Bucket size in hours", "default": 4},
                    },
                },
            ),
            types.Tool(
                name="get_reviews_by_product",
                description="Get reviews filtered by product_id or product_name.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "string", "description": "Product ID filter"},
                        "product_name": {"type": "string", "description": "Product name filter"},
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
        if name == "get_recent_reviews":
            out = get_recent_reviews(limit=args.get("limit", 50), hours=args.get("hours"))
        elif name == "get_sentiment_trend":
            out = get_sentiment_trend(hours=args.get("hours", 24), bucket_hours=args.get("bucket_hours", 4))
        elif name == "get_reviews_by_product":
            out = get_reviews_by_product(product_id=args.get("product_id"), product_name=args.get("product_name"))
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
        "reviews-mcp",
        on_list_tools=handle_list_tools,
        on_call_tool=handle_call_tool,
    )
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
