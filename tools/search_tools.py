# tools/search_tools.py
from langchain_core.tools import tool
import os
from dotenv import load_dotenv
load_dotenv()

@tool
def web_search(query: str) -> str:
    """Search the web for information not available in internal documents."""
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
        result = client.search(query=query, max_results=3)
        results = result.get('results', [])
        if not results:
            return 'No results found.'
        lines = []
        for r in results:
            lines.append(f"- {r['title']}: {r['content'][:200]}")
        return '\n'.join(lines)
    except Exception as e:
        return f'Search error: {e}'