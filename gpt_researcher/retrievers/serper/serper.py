# Google Serper Retriever

# libraries
import os
import requests
import json


class SerperSearch:
    """
    Google Serper Retriever
    """

    def __init__(self, query, query_domains=None):
        """
        Initializes the SerperSearch object
        Args:
            query (str): The search query string.
            query_domains (list, optional): List of domains to include in the search. Defaults to None.
        """
        self.query = query
        self.query_domains = query_domains or None
        self.api_key = self.get_api_key()

        self.time_range = os.getenv("SERPER_TIME_RANGE", "")
        self.region = os.getenv("SERPER_REGION", "")
        self.language = os.getenv("SERPER_LANGUAGE", "")
        self.location = os.getenv("SERPER_LOCATION", "")

    def get_api_key(self):
        """
        Gets the Serper API key
        Returns:

        """
        try:
            api_key = os.environ["SERPER_API_KEY"]
        except:
            raise Exception(
                "Serper API key not found. Please set the SERPER_API_KEY environment variable. "
                "You can get a key at https://serper.dev/"
            )
        return api_key

    def search(self, max_results=10):
        """
        Searches the query
        Returns:

        """
        print("Searching with query {0}...".format(self.query))
        """Useful for general internet search queries using the Serp API."""

        # Search the query (see https://serper.dev/playground for the format)
        url = "https://google.serper.dev/search"

        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

        data = {
            "q": self.query,
            "num": max_results,
        }

        if self.time_range:
            data["tbs"] = self.time_range

        if self.region:
            data["gl"] = self.region

        if self.language:
            data["hl"] = self.language

        if self.location:
            data["location"] = self.location

        if self.query_domains:
            domain_query = " OR ".join(
                [f"site:{domain}" for domain in self.query_domains]
            )
            data["q"] = f"{data['q']} ({domain_query})"

        
        print("----------------------------")
        print(json.dumps(data))
        print("----------------------------")

        resp = requests.request(
            "POST", url, timeout=10, headers=headers, data=json.dumps(data)
        )

        # Preprocess the results
        if resp is None:
            return
        try:
            search_results = json.loads(resp.text)
        except Exception:
            return
        if search_results is None:
            return

        results = search_results.get("organic", [])
        search_results = []

        # Normalize the results to match the format of the other search APIs
        for result in results:
            # skip youtube results
            if "youtube.com" in result["link"]:
                continue
            search_result = {
                "title": result["title"],
                "href": result["link"],
                "body": result["snippet"],
            }
            search_results.append(search_result)

        return search_results
