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


def scraper(url, resp):
    global visited_urls
    if url in visited_urls:
        return []
    visited_urls.add(url)
    word_count = count_words(resp.raw_response.content)
    record_longest_page(url, word_count)
    process_subdomain(url)

    save_longest_page()
    save_subdomain_info()

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
        if any(parsed.path.lower().endswith(ext) for ext in EXCLUDED_EXTENSIONS):
            return False  
        # Remove URL fragments
        url = parsed._replace(fragment="").geturl()
        return True
    except TypeError:
        print("TypeError for URL:", url)
        raise

def count_words(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    words = re.findall(r'\b\w+\b', text.lower())
    return len(words)

def record_longest_page(url, word_count):
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

