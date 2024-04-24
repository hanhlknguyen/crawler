import re
from collections import Counter
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

EXCLUDED_EXTENSIONS = [
    '.css', '.js', '.bmp', '.gif', '.jpe', '.jpeg', '.jpg', '.ico', '.png', '.tif', '.tiff', '.pdf',
    '.mp3', '.mp4', '.avi', '.mov', '.mpeg', '.tar', '.gz', '.zip', '.rar', '.swf', '.flv', '.wma',
    '.wmv'
]

visited_urls = set()
longest_page_url = ''
longest_page_word_count = 0
common_words_counter = Counter()
subdomain_pages = {}
visited_patterns = {}


def scraper(url, resp):
    global visited_urls
    # Skip already visited URLs
    if url in visited_urls:
        return []
    # Skip URLs detected as traps
    if detect_trap(url):
        print(f"Trap detected for URL {url}, skipping...")
        return []
    if is_dead_url(resp) or not has_high_information_content(resp):
        print(f"No information for URL {url}, skipping...")
        return []
    visited_urls.add(url)
    word_count = count_words(resp.raw_response.content)
    record_longest_page(url, word_count)
    process_subdomain(url)

    # Save the information about the longest page and subdomains
    save_longest_page()
    save_longest_page()
    save_subdomain_info()

    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    """
    Extracts links from the content of a given URL.

    Args:
        url (str): The URL of the page from which links are to be extracted.
        resp (Response): The response object containing the URL content.

    Returns:
        list: List of valid absolute URLs extracted from the page content.
    """
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
    """
    Checks whether a given URL is valid for further processing.

    Args:
        url (str): The URL to be validated.

    Returns:
        bool: True if the URL is valid, False otherwise.
    """
    try:
        parsed = urlparse(url)
        url = parsed._replace(fragment="").geturl()
        if parsed.scheme not in set(["http", "https"]):
            return False
        if not re.match(
            r".*\.(ics|cs|informatics|stat)\.uci\.edu.*", parsed.netloc):
            return False
        if any(parsed.path.lower().endswith(ext) for ext in EXCLUDED_EXTENSIONS):
            return False  
        # Remove URL fragments
        url = parsed._replace(fragment="").geturl()
        return True
    except TypeError:
        print("TypeError for URL:", url)
        raise

def count_words(html_content):
    """
    Counts the number of words in the HTML content.

    Args:
        html_content (bytes): The HTML content of a page.

    Returns:
        int: The count of words in the content.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    words = re.findall(r'\b\w+\b', text.lower())
    return len(words)

def record_longest_page(url, word_count):
    """
    Records the information about the longest page encountered.

    Args:
        url (str): The URL of the page.
        word_count (int): The count of words in the page content.
    """
    global longest_page_url, longest_page_word_count
    if word_count > longest_page_word_count:
        longest_page_word_count = word_count
        longest_page_url = url
    
def extract_subdomain(url):
    parsed = urlparse(url)
    return parsed.netloc

def process_subdomain(url):
    subdomain = extract_subdomain(url)
    if subdomain not in subdomain_pages:
        subdomain_pages[subdomain] = set()
    subdomain_pages[subdomain].add(url)


def save_longest_page():
    with open('longest_page.txt', 'w') as file:
        file.write(f"Longest Page: {longest_page_url} with {longest_page_word_count} words\n")

def save_subdomain_info():
    with open('subdomains.txt', 'w') as file:
        for subdomain, urls in subdomain_pages.items():
            file.write(f"{subdomain}: {len(urls)} pages\n")


def normalize_url(url):
    """
    Normalizes a URL by excluding fragments and query parameters.

    Args:
        url (str): The URL to be normalized.

    Returns:
        str: The normalized URL.
    """
    parsed = urlparse(url)
    # Normalize to exclude URL fragments and query parameters
    normalized = parsed._replace(query="", fragment="").geturl()
    return normalized

def get_url_pattern(url):
    """
    Extracts a URL pattern by replacing digits with a placeholder.

    Args:
        url (str): The URL from which the pattern is to be extracted.

    Returns:
        str: The URL pattern.
    """
    parsed = urlparse(url)
    path = parsed.path
    return re.sub(r'\d+', '[digit]', path)
