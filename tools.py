import robin_stocks.robinhood as rh

def get_portfolio_summary() -> dict:
    """Returns cash, equity, and total portfolio value."""
    profile = rh.profiles.load_portfolio_profile()
    return {
        "equity": profile.get("equity"),
        "extended_hours_equity": profile.get("extended_hours_equity"),
        "market_value": profile.get("market_value"),
        "excess_margin": profile.get("excess_margin"),
    }

def get_positions() -> list[dict]:
    """Returns all open stock positions."""
    positions = rh.get_open_stock_positions()
    result = []
    for p in positions:
        instrument = rh.get_instrument_by_url(p["instrument"])
        result.append({
            "symbol": instrument["symbol"],
            "quantity": p["quantity"],
            "average_buy_price": p["average_buy_price"],
        })
    return result

def get_quote(symbol: str) -> dict:
    """Returns current quote for a ticker symbol."""
    q = rh.get_latest_price(symbol)
    return {"symbol": symbol.upper(), "price": q[0] if q else None}

def buy_stock(symbol: str, quantity: float) -> dict:
    """Places a market buy order."""
    order = rh.order_buy_market(symbol, quantity)
    return {"order_id": order.get("id"), "state": order.get("state"), "symbol": symbol}

def sell_stock(symbol: str, quantity: float) -> dict:
    """Places a market sell order."""
    order = rh.order_sell_market(symbol, quantity)
    return {"order_id": order.get("id"), "state": order.get("state"), "symbol": symbol}

def get_open_orders() -> list[dict]:
    """Returns all open (pending) orders."""
    orders = rh.get_all_open_stock_orders()
    return [
        {
            "id": o.get("id"),
            "symbol": rh.get_instrument_by_url(o["instrument"])["symbol"],
            "side": o.get("side"),
            "quantity": o.get("quantity"),
            "state": o.get("state"),
        }
        for o in orders
    ]

def cancel_order(order_id: str) -> dict:
    """Cancels an open order by ID."""
    result = rh.cancel_stock_order(order_id)
    return {"cancelled": result is not None, "order_id": order_id}

TOOL_DEFINITIONS = [
    {
        "name": "get_portfolio_summary",
        "description": "Get current portfolio value, equity, and cash.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_positions",
        "description": "Get all open stock positions with symbol, quantity, and average buy price.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_quote",
        "description": "Get the current market price for a stock symbol.",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string", "description": "Ticker symbol, e.g. AAPL"}},
            "required": ["symbol"],
        },
    },
    {
        "name": "buy_stock",
        "description": "Place a market buy order for a stock.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Ticker symbol"},
                "quantity": {"type": "number", "description": "Number of shares (fractional allowed)"},
            },
            "required": ["symbol", "quantity"],
        },
    },
    {
        "name": "sell_stock",
        "description": "Place a market sell order for a stock.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Ticker symbol"},
                "quantity": {"type": "number", "description": "Number of shares (fractional allowed)"},
            },
            "required": ["symbol", "quantity"],
        },
    },
    {
        "name": "get_open_orders",
        "description": "List all pending open orders.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "cancel_order",
        "description": "Cancel a pending order by its order ID.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "The order ID to cancel"}},
            "required": ["order_id"],
        },
    },
]

TOOL_HANDLERS = {
    "get_portfolio_summary": lambda args: get_portfolio_summary(),
    "get_positions": lambda args: get_positions(),
    "get_quote": lambda args: get_quote(args["symbol"]),
    "buy_stock": lambda args: buy_stock(args["symbol"], args["quantity"]),
    "sell_stock": lambda args: sell_stock(args["symbol"], args["quantity"]),
    "get_open_orders": lambda args: get_open_orders(),
    "cancel_order": lambda args: cancel_order(args["order_id"]),
}
