"""Functions module for goodreads-sync."""

import json
import logging
from datetime import datetime

import feedparser
import httpx

from goodreads_sync.config import Config

BASE_MAM_URL = "https://www.myanonamouse.net"
DOWNLOAD_APPEND = "/tor/download.php/"


class MyAnonamouseAPI:
    def __init__(self):
        self.base_url = BASE_MAM_URL
        self.download_append = DOWNLOAD_APPEND
        self.mam_id = Config.mam_id
        self.session = httpx.Client(cookies={"mam_id": self.mam_id})
        self.logger = logging.getLogger(__name__)

    def search_mam(self: "MyAnonamouseAPI", text: str) -> list[str]:
        """Search MyAnonamouse for torrents matching the query and return download links."""
        search_payload = {
            "tor": {
                "text": text,
                "srchIn": {
                    "title": "true",
                    "author": "true",
                    "narrator": "true",
                },
                "searchType": "all",
                "searchIn": "torrents",
                "cat": ["0"],
                "browseFlagsHideVsShow": "0",
                "startDate": "",
                "endDate": "",
                "hash": "",
                "sortType": "default",
                "startNumber": "0",
            },
            "thumbnail": "true",
            "dlLink": "",
        }

        try:
            response = self.session.post(
                f"{self.base_url}/tor/js/loadSearchJSONbasic.php",
                json=search_payload,
            )
            response.raise_for_status()

            data = response.json()
            download_links = [
                f"{self.base_url}{self.download_append}{item['dl']}"
                for item in data.get("data", [])
            ]
            self.logger.debug(
                f"Found {len(download_links)} torrents for query '{text}'.",
            )

            return download_links

        except httpx.HTTPStatusError as http_err:
            self.logger.error(f"HTTP error occurred: {http_err}")
        except Exception as err:
            self.logger.error(f"Other error occurred: {err}")

        return []


class GoodreadsRSS:
    def __init__(self, state_file: str = "state.json"):
        self.logger = logging.getLogger(__name__)
        self.state_file = state_file
        self.last_run = self._load_last_run()

    def parse_feed(self: "GoodreadsRSS", feed_url: str) -> list[dict[str, str]]:
        """Parse the Goodreads RSS feed and return a list of books added since the last check."""
        parsed_feed = feedparser.parse(feed_url)
        new_books = []

        for entry in parsed_feed.entries:
            add_date = self._parse_add_date(entry)
            if add_date > self.last_run:
                try:
                    book_details = self._parse_entry(entry)
                    new_books.append(book_details)
                except Exception as e:
                    self.logger.error(f"Failed to parse entry: {e}")

        self._update_last_run()
        return new_books

    def _parse_entry(self: "GoodreadsRSS", entry) -> dict[str, str]:
        """Extracts and returns book details from a feed entry."""
        try:
            # Assuming the entry has 'title' and 'author' fields
            book_details = {
                "title": entry.title,
                "author": entry.author_name,
                "add_date": self._parse_add_date(entry),
            }
            return book_details
        except AttributeError as e:
            self.logger.error(f"Failed to parse entry: {e}")
            raise ValueError("Entry does not contain expected fields") from e

    def _parse_add_date(self: "GoodreadsRSS", entry) -> datetime:
        """Extracts and returns the add date from a feed entry."""
        return datetime(*entry.published_parsed[:6])

    def _load_last_run(self: "GoodreadsRSS") -> datetime:
        """Load the last run date from the state file."""
        try:
            with open(self.state_file) as f:
                state = json.load(f)
                last_run = datetime.fromisoformat(state.get("last_run"))
                return last_run
        except (FileNotFoundError, json.JSONDecodeError):
            return datetime.min  # Default to the earliest possible date if the file doesn't exist or is corrupt

    def _update_last_run(self: "GoodreadsRSS"):
        """Update the last run date in the state file to the current date."""
        with open(self.state_file, "w") as f:
            state = {"last_run": datetime.now().isoformat()}
            json.dump(state, f, indent=4)
