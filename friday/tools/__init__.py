from friday.tools import deep, system, weather, web


def register_all(mcp):
    system.register(mcp)
    weather.register(mcp)
    web.register(mcp)
    deep.register(mcp)