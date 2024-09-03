import logging
import re
from urllib.parse import urlencode

import feedparser
import httpx

from goodreads_sync.config import Config


class GoodreadsRSS:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.feed_url = Config.goodreads_rss

    def parse_feed(self: "GoodreadsRSS") -> tuple[str, list[dict[str, str]]]:
        """Parse the Goodreads RSS feed and return a list of books added since the last check."""
        parsed_feed = feedparser.parse(self.feed_url)
        collection_title: str = parsed_feed.feed.title
        new_books = []

        for entry in parsed_feed.entries:
            try:
                book_details = self._parse_entry(entry)
                new_books.append(book_details)
            except Exception as e:
                self.logger.error(f"Failed to parse entry: {e}")
        return collection_title, new_books

    def _parse_entry(self, entry) -> dict[str, str]:
        """Extracts and returns book details from a feed entry."""
        try:
            title = re.sub(
                r"\s*\(.*?\)\s*",
                "",
                entry.title,
            ).strip()  # Remove anything in parentheses
            book_details = {
                "title": title,
                "author": entry.author_name,
            }
            return book_details
        except AttributeError as e:
            self.logger.error(f"Failed to parse entry: {e}")
            raise ValueError("Entry does not contain expected fields") from e


class Audiobookshelf:
    def __init__(self: "Audiobookshelf") -> None:
        self.key = Config.abs_key
        self.url = Config.abs_url
        self.missing_books = []

    def get_abs_libraries(
        self: "Audiobookshelf",
    ) -> None:
        """Fetch and return a list of Audiobookshelf library IDs with mediaType 'book'."""
        url = f"{self.url}/api/libraries/"
        headers = {"Authorization": f"Bearer {self.key}"}
        response = httpx.get(url, headers=headers)
        response.raise_for_status()

        libraries = response.json()["libraries"]
        self.lib_ids = [lib["id"] for lib in libraries if lib["mediaType"] == "book"]

    def get_abs_book_id(
        self: "Audiobookshelf",
        book_title: str,
        libid: str,
    ) -> None:
        """Get the Audiobookshelf library item ID for the closest match of a specific book title."""
        query_params = urlencode({"q": book_title})
        url = f"{self.url}/api/libraries/{libid}/search?{query_params}"
        headers = {"Authorization": f"Bearer {self.key}"}
        response = httpx.get(url, headers=headers)
        response.raise_for_status()

        abs_books = response.json()
        normalized_title = self._normalize_title(book_title)

        for book in abs_books.get("book", []):
            abs_title = self._normalize_title(
                book["libraryItem"]["media"]["metadata"]["title"],
            )
            if abs_title == normalized_title:
                return book["libraryItem"]["id"]

        self.missing_books.append(book_title)
        return None

    def _normalize_title(self, title: str) -> str:
        """Normalize the title for a closer match."""
        title = title.lower()
        title = re.sub(r"[^\w\s]", "", title)  # Remove punctuation
        return title.strip()

    def add_tag_to_audiobookshelf_book(
        self: "Audiobookshelf",
        book_id: str,
        tag: str,
    ) -> None:
        """Add a tag to a book in Audiobookshelf."""
        url = f"{self.url}/api/items/{book_id}/media"
        headers = {"Authorization": f"Bearer {self.key}"}
        data = {"tags": [tag]}
        response = httpx.patch(url, json=data, headers=headers)
        response.raise_for_status()

    def create_audiobookshelf_collection(
        self: "Audiobookshelf",
        collection_name: str,
        libid: str,
    ) -> str:
        """Create a new collection in Audiobookshelf and return its ID."""
        collection_id = self._check_collections(collection_name, libid)
        if collection_id:
            self.delete_collection(collection_id)
        url = f"{self.url}/api/collections"
        headers = {"Authorization": f"Bearer {self.key}"}
        data = {"libraryId": libid, "name": collection_name}
        response = httpx.post(url, json=data, headers=headers)
        response.raise_for_status()

        return response.json()["id"]

    def delete_collection(self: "Audiobookshelf", collection_id: str):
        url = f"{self.url}/api/collections/{collection_id}"
        headers = {"Authorization": f"Bearer {self.key}"}
        response = httpx.delete(url, headers=headers)
        response.raise_for_status()

    def _check_collections(
        self: "Audiobookshelf",
        collection_name: str,
        libid: str,
    ) -> str | None:
        """Check if a collection with the given name already exists in the specified library."""
        url = f"{self.url}/api/libraries/{libid}/collections"
        headers = {"Authorization": f"Bearer {self.key}"}
        response = httpx.get(url, headers=headers)
        response.raise_for_status()

        existing_colls = response.json()["results"]

        for collection in existing_colls:
            if collection["name"].lower() == collection_name.lower():
                return collection["id"]

        return None

    def add_books_to_audiobookshelf_collection(
        self: "Audiobookshelf",
        collection_id: str,
        book_id: list[str],
    ) -> None:
        """Add a book to an Audiobookshelf collection."""
        url = f"{self.url}/api/collections/{collection_id}/batch/add"
        headers = {"Authorization": f"Bearer {self.key}"}
        data = {"books": book_id}
        response = httpx.post(url, json=data, headers=headers)
        response.raise_for_status()
