import re
from collections import Counter
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import hashlib

EXCLUDED_EXTENSIONS = [
    '.css', '.js', '.bmp', '.gif', '.jpe', '.jpeg', '.jpg', '.ico', '.png', '.tif', '.tiff', '.pdf',
    '.mp3', '.mp4', '.avi', '.mov', '.mpeg', '.tar', '.gz', '.zip', '.rar', '.swf', '.flv', '.wma',
    '.wmv'
]

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", 
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", 
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", 
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", 
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", 
    "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", 
    "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", 
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", 
    "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", 
    "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there", 
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", 
    "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", 
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", 
    "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", 
    "your", "yours", "yourself", "yourselves"
}

visited_urls = set()
longest_page_url = ''
longest_page_word_count = 0
common_words_counter = Counter()
subdomain_pages = {}
visited_patterns = {}
visited_hashes = set()


def scraper(url, resp):
    global visited_urls
    # Skip already visited URLs
    if url in visited_urls:
        return []
    
    if detect_trap(url) or is_dead_url(resp) or not has_high_information_content(resp):
        print(f"No information or trap detected for URL {url}, skipping...")
        return []
    
    final_url = handle_redirects(resp)
    visited_urls.add(final_url)

    if detect_similar_content(final_url, resp.raw_response.content):
        return []
    
    word_count = count_words(resp.raw_response.content)
    record_longest_page(final_url, word_count)
    process_subdomain(final_url)

    # Save the information about the longest page and subdomains
    save_longest_page()
    save_subdomain_info()

    links = extract_next_links(final_url, resp)
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
            example_url = next(iter(urls))
            parsed_url = urlparse(example_url)
            scheme = parsed_url.scheme
            netloc = parsed_url.netloc

            formatted_subdomain = f"{scheme}://{netloc}"
            file.write(f"{formatted_subdomain}, {len(urls)}\n")


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


def detect_trap(url):
    pattern = get_url_pattern(normalize_url(url))
    if pattern in visited_patterns:
        visited_patterns[pattern] += 1
    else:
        visited_patterns[pattern] = 1

    # Detect a trap if a pattern is visited too frequently
    if visited_patterns[pattern] > 10:
        return True
    return False

# def find_most_common_words(url, number_of_words=50):
#     """
#     Fetches the URL content, processes the content to find the most common words.

#     Args:
#         url (str): The URL of the page.
#         number_of_words (int): The number of top common words to return.

#     Returns:
#         list: List of tuples with the most common words and their counts.
#     """
#     response = requests.get(url)
#     if response.status_code == 200:
#         word_counts = count_words(response.content)
#         most_common = word_counts.most_common(number_of_words)
#         return most_common
#     else:
#         return []

def is_dead_url(resp):
    """
    Checks if the URL is a dead URL (returns a 200 status but no data).

    Args:
        resp (Response): The response object containing the URL content.

    Returns:
        bool: True if the URL is a dead URL, False otherwise.
    """
    # Check if the response status is 200
    if resp.status == 200:
        # Check if the response contains content
        if resp.raw_response:
            # Check if the content length is zero
            if len(resp.raw_response.content) == 0:
                return True  # Dead URL
        else:
            return True  # Dead URL
    return False  # Not a dead URL

def has_high_information_content(resp):
    """
    Checks if the page contains significant textual information.

    Args:
        resp (Response): The response object containing the URL content.

    Returns:
        bool: True if the page contains significant textual information, False otherwise.
    """
    # Ensure that the response contains content
    if not resp.raw_response:
        return False

    # Extract text content from the HTML
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    text = soup.get_text()

    # Count the number of words
    words = re.findall(r'\b\w+\b', text.lower())
    word_count = len(words)

    if word_count < 100:
        return False
    else:
        return True
    

def handle_redirects(resp):
    """
    Handles HTTP redirects by returning the final URL after all redirects.

    Args:
        resp (Response): The response object from the HTTP request.

    Returns:
        str: The final URL after following all redirects.
    """
    if 300 <= resp.status < 400:
        redirected_url = resp.headers.get('Location', '')
        if redirected_url:
            return urljoin(resp.url, redirected_url)
    return resp.url

def get_content_hash(html_content):
    """
    Generates a hash for the textual content of a web page.

    Args:
        html_content (bytes): The HTML content of a page.

    Returns:
        str: A hash of the text content.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    # Normalize whitespace and lower the case for uniformity
    normalized_text = re.sub(r'\s+', ' ', text).strip().lower()
    return hashlib.md5(normalized_text.encode('utf-8')).hexdigest()

def detect_similar_content(url, html_content):
    """
    Detects if the given page content is similar to any previously encountered page.

    Args:
        url (str): The URL of the page being checked.
        html_content (bytes): The HTML content of the page.

    Returns:
        bool: True if similar content is detected, otherwise False.
    """
    content_hash = get_content_hash(html_content)
    if content_hash in visited_hashes:
        print(f"Similar content detected for URL {url}, skipping...")
        return True
    else:
        visited_hashes.add(content_hash)
        return False
