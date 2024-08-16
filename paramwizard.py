import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque
import os
from colorama import Fore, init

# Initialize Colorama
init(autoreset=True)

def print_banner():
    banner = r"""

__________                             __      __.__                         .___
\______   \_____ ____________    _____/  \    /  \__|____________ _______  __| _/
 |     ___/\__  \\_  __ \__  \  /     \   \/\/   /  \___   /\__  \\_  __ \/ __ | 
 |    |     / __ \|  | \// __ \|  Y Y  \        /|  |/    /  / __ \|  | \/ /_/ | 
 |____|    (____  /__|  (____  /__|_|  /\__/\  / |__/_____ \(____  /__|  \____ | 
                \/           \/      \/      \/           \/     \/           \/ 

         [  ͙͘͡★  ] ParamWizard v1.0 created by iamunixtz [  ͙͘͡★  ] 

    """
    print(Fore.GREEN + banner)

def ensure_scheme(url):
    if not urlparse(url).scheme:
        return 'http://' + url
    return url

def is_within_domain(url, domain):
    return urlparse(url).netloc.endswith(domain)

def get_links(url, domain, timeout):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            full_url = urljoin(url, href)
            if is_within_domain(full_url, domain):
                links.add(full_url)
        return links
    except requests.RequestException as e:
        print(Fore.RED + f"×͜× Error with {url}: {e}")
        return set()

def extract_parameters(url):
    params = []
    parsed_url = urlparse(url)
    if parsed_url.query:
        params.append(url)
    return params

def crawl_url(url, domain, timeout, verbose):
    if verbose:
        print(Fore.RED + f"➤ [Target] {url}")
    links = get_links(url, domain, timeout)
    params = extract_parameters(url)
    return links, params

def main():
    parser = argparse.ArgumentParser(description="ParamWizard - Extract URLs with Parameters")
    parser.add_argument('-u', '--url', required=True, help="Base URL to start crawling")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose logging")
    parser.add_argument('-t', '--threads', type=int, default=3, help="Number of threads to use for crawling (default: 3)")
    parser.add_argument('--time-sec', type=int, default=30, help="Timeout in seconds for HTTP requests (default: 30)")
    args = parser.parse_args()

    print_banner()

    base_url = ensure_scheme(args.url)
    domain = urlparse(base_url).netloc
    urls_to_process = deque([base_url])
    urls_with_params = set()
    processed_urls = 0

    seen_urls = set() 

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = []
        while urls_to_process or futures:
            while urls_to_process:
                url = urls_to_process.popleft()
                if url not in seen_urls:
                    seen_urls.add(url)
                    future = executor.submit(crawl_url, url, domain, args.time_sec, args.verbose)
                    futures.append(future)

            for future in as_completed(futures):
                links, params = future.result()
                for link in links:
                    if link not in seen_urls:
                        urls_to_process.append(link)
                urls_with_params.update(params)
                processed_urls += 1

                # Write URLs with parameters to file incrementally
                with open('paramwizard.txt', 'a') as f:
                    for param in params:
                        f.write(param + '\n')

                # Log target URLs and errors on separate lines
                if args.verbose:
                    print(Fore.RED + f"➤ [Target] {url}")

            futures = [f for f in futures if not f.done()]

    # Final output
    print(f"\n[+] Number of URLs processed: {processed_urls}")
    print(f"[+] Number of URLs with parameters extracted: {len(urls_with_params)}")
    print(f"[+] Results written to paramwizard.txt")

if __name__ == "__main__":
    main()
