from tools.price_tool import PriceTool
from tools.fundamentals_tool import FundamentalsTool
from tools.news_tool import NewsTool
from tools.watchlist_read import WatchlistReadTool
from tools.watchlist_write import WatchlistWriteTool


class ToolRegistry:
    def __init__(self):
        self._tools = {}
        for tool_cls in [
            PriceTool,
            FundamentalsTool,
            NewsTool,
            WatchlistReadTool,
            WatchlistWriteTool,
        ]:
            instance = tool_cls()
            self._tools[instance.name] = instance

    def get(self, name: str):
        tool = self._tools.get(name)
        if not tool:
            raise KeyError(f"Tool '{name}' not found. Available: {list(self._tools)}")
        return tool

    def schemas(self) -> list[dict]:
        return [t.schema() for t in self._tools.values()]

    def all(self) -> dict:
        return self._tools
_registry = None

def get_registry():
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry.all()

