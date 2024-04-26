from threading import Thread
from urllib.parse import urlparse
from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        self.last_request_time = {}
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break

            domain = urlparse(tbd_url).netloc
            self.respect_politeness(domain)
            resp = download(tbd_url, self.config, self.logger)
            if resp and resp.status == 200:
                self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
                scraped_urls = scraper.scraper(tbd_url, resp)
                for scraped_url in scraped_urls:
                    self.frontier.add_url(scraped_url)
                self.frontier.mark_url_complete(tbd_url)
            else:
                self.logger.error(f"Failed to download or process URL {tbd_url}, status might be <{getattr(resp, 'status', 'None')}>.")
            time.sleep(self.config.time_delay)
        
    def respect_politeness(self, domain):
        """Ensure there is sufficient delay between requests to the same domain."""
        if domain in self.last_request_time:
            elapsed_time = time.time() - self.last_request_time[domain]
            if elapsed_time < self.config.time_delay:
                time.sleep(self.config.time_delay - elapsed_time)
        self.last_request_time[domain] = time.time()
