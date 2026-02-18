import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from pathlib import Path

# Base configuration
BASE_URL = "https://cheaptrip.guru"
START_URL = "https://cheaptrip.guru/budgettraveltips/tree/city_descriptions/en/aalborg"

# Where to save files
SAVE_DIR = Path("aalborg_cheaptrip_pages")
SAVE_DIR.mkdir(exist_ok=True)

# Which links we want to follow (relative patterns)
WANTED_PATTERNS = [
    "/budgettraveltips/tree/accommodations/en/aalborg",
    "/budgettraveltips/tree/events_festivals/en/aalborg",
    "/budgettraveltips/tree/city_attractions/en/aalborg",
    "/budgettraveltips/tree/cheap_eats/en/aalborg",
    "/budgettraveltips/tree/children_attractions/en/aalborg",
    "/budgettraveltips/tree/transportations/en/aalborg",
    "/budgettraveltips/tree/routes/en/aalborg",
    # You can add more patterns if needed, e.g.:
    # "/budgettraveltips/tree/city_descriptions/en/",
]

def get_filename_from_url(url: str) -> str:
    path = urlparse(url).path
    if path.endswith('/'):
        path = path.rstrip('/')
    parts = path.split('/')
    if len(parts) >= 2:
        last = parts[-1]
        second_last = parts[-2] if len(parts) >= 3 else ""
        
        if last in ("list", "aalborg"):
            return f"{second_last}_{last}.html"
        return f"{last}.html"
    return "index.html"


def download_page(url: str, session: requests.Session, delay: float = 1.2):
    try:
        print(f"Downloading: {url}")
        response = session.get(url, timeout=12)
        response.raise_for_status()
        
        filename = get_filename_from_url(url)
        save_path = SAVE_DIR / filename
        
        save_path.write_bytes(response.content)
        print(f"  Saved → {save_path}")
        
        time.sleep(delay)  # be polite to the server
        
        return response.text
        
    except Exception as e:
        print(f"  Failed: {url} → {e}")
        return None


def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CheapTrip-Collector/0.1"
    })
    
    # 1. Download starting page
    html = download_page(START_URL, session)
    if not html:
        print("Cannot continue - failed to download starting page")
        return
    
    # 2. Parse and find interesting links
    soup = BeautifulSoup(html, "html.parser")
    
    found_links = []
    
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(BASE_URL, href)
        
        # Skip external links & booking links
        if not full_url.startswith(BASE_URL):
            continue
            
        # Check if matches any of our wanted patterns
        if any(pattern in full_url for pattern in WANTED_PATTERNS):
            if full_url not in found_links:
                found_links.append(full_url)
    
    print(f"\nFound {len(found_links)} interesting pages:")
    for link in found_links:
        print(f"  • {link}")
    
    print("\nStarting download of related pages...\n")
    
    # 3. Download all found pages
    for url in found_links:
        download_page(url, session)
    
    print("\n" + "═"*60)
    print(f"Finished! All downloaded files are in: {SAVE_DIR.resolve()}")
    print("═"*60)


if __name__ == "__main__":
    main()