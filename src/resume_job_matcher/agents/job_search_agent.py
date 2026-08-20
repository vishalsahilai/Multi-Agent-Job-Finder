import time
import random
import logging
from typing import Optional
from urllib.parse import urljoin, urlparse
 
import requests
from bs4 import BeautifulSoup
 
logger = logging.getLogger(__name__)

#  HTTP Config
 
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
 
REQUEST_TIMEOUT = 15       # seconds
DELAY_MIN = 1.5            # min delay between requests
DELAY_MAX = 3.5            # max delay between requests
 