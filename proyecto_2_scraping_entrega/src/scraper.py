import csv
import os
import time
import requests
from bs4 import BeautifulSoup

URL_CATALOGO = "https://books.toscrape.com/catalogue/"
HEADERS = {"User-Agent": "Mozilla/5.0 (proyecto educativo de scraping)"}

def get_soup(url):
    response=requests.get(url,headers=HEADERS)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def get_book_links_from_page(soup):
    links=[]
    for article in soup.find_all("article", class_="product_pod"):
        relative_href = article.h3.a["href"]
        book_url=URL_CATALOGO+relative_href
        links.append(book_url)
    return links

def has_next_page(soup):
    return soup.find("li", class_="next") is not None

def scrape_book_detail(url):
    soup=get_soup(url)
    title=soup.find("div", class_="product_main").h1.get_text(strip=True)
    price = soup.find("p", class_="price_color").get_text(strip=True)
    rating_tag = soup.find("p", class_="star-rating")
    rating = rating_tag["class"][1]
    availability_raw=soup.find("p", class_="instock availability").get_text(strip=True)
    availability = "In Stock" if "In stock" in availability_raw else "Out of Stock"

    breadcrumb_links = soup.select("ul.breadcrumb li a")
    category = breadcrumb_links[2].get_text(strip=True) if len(breadcrumb_links) >= 3 else "Unknown"

    return {
        "Title": title,
        "Price": price,
        "Rating": rating,
        "Availability": availability,
        "Category": category,
    }

def scrape_all_books():
    all_books = []
    page_number = 1
 
    while True:
        page_url = f"{URL_CATALOGO}page-{page_number}.html"
        print(f"Leyendo página {page_number}: {page_url}")
        listing_soup = get_soup(page_url)
 
        book_links = get_book_links_from_page(listing_soup)
        for book_url in book_links:
            all_books.append(scrape_book_detail(book_url))
            time.sleep(0.1)  # pequeña pausa para no saturar el servidor
 
        if not has_next_page(listing_soup):
            break
        page_number += 1
 
    return all_books

def save_to_csv(books, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fieldnames=["Title", "Price", "Rating", "Availability", "Category"]
    with open(output_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(books)

if __name__ == "__main__":

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_csv = os.path.join(script_dir, "..", "data", "libros_extraidos.csv")
 
    books = scrape_all_books()
    save_to_csv(books, output_csv)
 
    print(f"\nListo: se extrajeron {len(books)} libros. Archivo guardado en {output_csv}")



