import re
from collections import defaultdict
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    if resp.status != 200 or not resp.raw_response:
        return[]
    
    # Parse the content to extract links
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    links = []
    for link in soup.find_all('a', href = True):
        # Resolve relative links into absolute URLs
        absolute_link = urljoin(resp.raw_response.url, link['href'])
        absolute_link = urlparse(absolute_link)._replace(fragment="").geturl()
        if is_valid(absolute_link): 
            links.append(absolute_link)
    return links

def is_valid(url):
    try:
        parsed = urlparse(url)
        url = parsed._replace(fragment="").geturl()
        if parsed.scheme not in set(["http", "https"]):
            return False
        if not re.match(
            r".*\.(ics|cs|informatics|stat)\.uci\.edu.*", parsed.netloc):
            return False
        if re.search(r".*\.(css|js|bmp|gif|jpeg|jpg|ico|png|tiff|pdf"
                     r"|mp3|mp4|avi|mov|mpeg|tar|gz|zip|rar)$", parsed.path.lower()):
            return False
        # Remove URL fragments
        if parsed.fragment:
            return False
        return True
    except TypeError:
        print("TypeError for URL:", url)
        raise