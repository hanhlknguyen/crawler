import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    # Checks if the response status is OK to proceed
    if resp.status != 200 or not resp.raw_response:
        return[]
    
    # Parse the content to extract links
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    links = []
    for link in soup.find_all('a', href = True):
        # Resolve relative links into absolute URLs
        absolute_link = urljoin(resp.raw_response.url, link['href'])
        links.append(absolute_link)
    return links

def is_valid(url):
    try:
        parsed = urlparse(url)
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