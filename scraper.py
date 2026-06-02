"""
Scraper de notas de prensa - AICA (Asociación de Empresarios de Alcobendas)
Extrae título y texto completo de cada nota de prensa y lo guarda en un CSV.
"""

import csv
import time
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.empresariosdealcobendas.com"
LISTING_URL = f"{BASE_URL}/blog/prensa"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}


def fetch_page(url):
    """Fetch a URL and return a BeautifulSoup object."""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def get_press_release_links(soup):
    """
    Extract all press release links from the listing page.
    Each item is an <a> with href + <h2> title inside a grid.
    """
    links = []
    # The grid container that holds all press release cards
    grid = soup.select_one("div.grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-3")
    if not grid:
        raise ValueError("No se encontró el grid de notas de prensa en la página")

    for a_tag in grid.find_all("a", href=True):
        href = a_tag["href"]
        # Normalize URL: some have ?hsLang=es-es, some don't
        if "?" in href:
            href = href.split("?")[0]
        # Make absolute
        if href.startswith("/"):
            href = BASE_URL + href

        h2 = a_tag.find("h2")
        if h2:
            title = h2.get_text(strip=True)
            links.append((title, href))

    return links


def get_article_text(soup):
    """
    Extract the full body text from an individual press release page.
    The content is inside <span id="hs_cos_wrapper_post_body">.
    """
    body_span = soup.select_one("span#hs_cos_wrapper_post_body")
    if body_span:
        # Get all text, paragraphs separated by newlines
        paragraphs = body_span.find_all("p")
        text_parts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts)

    # Fallback: try the blog-post__body div
    body_div = soup.select_one("div.blog-post__body")
    if body_div:
        paragraphs = body_div.find_all("p")
        text_parts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts)

    return ""


def scrape_all():
    """Main scraping routine."""
    print("[INFO] Obteniendo listado de notas de prensa...")
    listing_soup = fetch_page(LISTING_URL)
    links = get_press_release_links(listing_soup)

    print(f"[OK] Encontradas {len(links)} notas de prensa\n")

    results = []
    for i, (title, url) in enumerate(links, 1):
        print(f"  [{i}/{len(links)}] {title[:70]}...")
        try:
            article_soup = fetch_page(url)
            text = get_article_text(article_soup)
            results.append({"Titulo": title, "Texto": text})
            print(f"    -> {len(text)} caracteres extraidos")
        except Exception as e:
            print(f"    [ERROR] {e}")
            results.append({"Titulo": title, "Texto": ""})
        # Small delay to be polite
        time.sleep(1)

    return results


def save_to_csv(results, filename="notas_de_prensa.csv"):
    """Save results to a CSV file."""
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["Titulo", "Texto"])
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[OK] CSV guardado: {filename}")


if __name__ == "__main__":
    print("=" * 60)
    print("  Scraper de Notas de Prensa - AICA")
    print("=" * 60)
    data = scrape_all()
    save_to_csv(data)
    print("\n[OK] Listo!")
