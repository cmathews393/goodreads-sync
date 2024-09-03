"""Config module for goodreads sync."""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Setup config options."""

    mam_id: str = os.getenv("MAM_ID", "Missing MAM ID")
    goodreads_rss = os.getenv("GOODREADS_RSS", "Missing Goodreads RSS")
    qbittorrent_url = os.getenv("QBITTORRENT_URL", "Missing QBit URL")
    abs_key = os.getenv("ABS_KEY", "No ABS Key")
    abs_url = os.getenv("ABS_URL", "No ABS URL")
