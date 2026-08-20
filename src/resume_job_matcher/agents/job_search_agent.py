import time
import random
import logging
from typing import Optional
from urllib.parse import urljoin, urlparse
 
import requests
from bs4 import BeautifulSoup
 
logger = logging.getLogger(__name__)