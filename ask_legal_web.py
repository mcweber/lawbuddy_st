#------------------------------------
# Module ask_legal_web
# 22.12.2024
# -----------------------------------

import os
from dotenv import load_dotenv
from tavily import TavilyClient

# Define sources --------------------------------------------------------------
STATUTES = [
    "www.gesetze-im-internet.de",
]

JURISDICTION = [
    "openjur.de",
    "www.rechtsprechung-im-internet.de"
]

COMMENTS = [
    ""
]

# Define class LegalWebSearch ------------------------------------------------
class LegalWebSearch:
    def __init__(self):
        load_dotenv()
        self.tavilyClient = TavilyClient(api_key=os.environ['TAVILY_API_KEY_PRIVAT'])

    def search_statutes(self, query: str = "", score: float = 0.5, limit: int = 10) -> str:
        context = self.tavilyClient.get_search_context(
            query=query,
            include_domains=STATUTES,
            max_results=limit,
            )
        return context

    def search_jurisdiction(self, query: str = "", score: float = 0.5, limit: int = 10) -> str:
        context = self.tavilyClient.get_search_context(
            query=query,
            include_domains=JURISDICTION,
            max_results=limit,
            )
        return context

    def search_comments(self, query: str = "", score: float = 0.5, limit: int = 10) -> str:
        context = self.tavilyClient.get_search_context(
            query=query,
            include_domains=COMMENTS,
            max_results=limit,
            )
        return context


    # def search(self, query: str = "", score: float = 0.5, limit: int = 10) -> list:
    #     results: list = []
    #     try:
    #         results_list = self.tavilyClient.search(
    #             query=query,
    #             topic="news",
    #             max_results=limit,
    #             )
    #     except:
    #         return results
    #     for result in results_list['results']:
    #         if result['score'] > score:
    #             results.append(result)
    #     return results
    
    

    # @staticmethod
    # def print_results(cursor: list) -> None:
    #     if not cursor:
    #         print("Keine Artikel gefunden.")
    #     for item in cursor:
    #         print(f"[{str(item['datum'])[:10]}] {item['titel'][:70]}")
