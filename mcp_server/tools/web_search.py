from mcp_server.mcp import mcp
from tavily import TavilyClient
from dotenv import load_dotenv
import os

load_dotenv()

tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY"),
)

@mcp.tool()
def search_web(query: str, max_results: int=5) -> str:

    """This is a Web Search tool, you have to use this whenever,
    the user will ask you to search any topic or anything from the Internet,
    It uses Tavily API for accessing Web Search, use it safely and efficiently.
    You have to help users get more detailed information"""

    response = tavily_client.search(
        query=query,
        max_results=max_results
    )

    results = response.get("results",[])
    formatted_results = []

    for result in results:

        title = result.get("title")
        url = result.get("url")
        content = result.get("content")
        formatted_results.append(f"Title: {title}\nURL:{url}\nContent: {content}\n") 

    return "\n".join(formatted_results)