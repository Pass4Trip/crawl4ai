import asyncio
import os

from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright

class Review(BaseModel):
    text: str = Field(..., description="Texte de l'avis")
    author: str = Field(..., description="Auteur de l'avis")
    date: str = Field(..., description="Date de l'avis")

async def scrape_google_maps_reviews(location: str):
    search_url = f"https://www.google.com/maps/search/restaurants+{location.replace(' ', '+')}/"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("Naviguer vers l'URL de recherche...")
        await page.goto(search_url)
        await page.wait_for_timeout(5000)

        try:
            await page.click('button:has-text("Tout accepter")')
            print("Bouton de consentement cliqué sur la page principale.")
        except Exception as e:
            print(f"Pas de bouton de consentement trouvé ou erreur sur la page principale : {e}")

        print("Attente des résultats...")
        try:
            await page.wait_for_selector('.Nv2PK', timeout=15000)
        except Exception as e:
            print(f"Erreur d'attente pour les résultats : {e}")
            await browser.close()
            return

        print("Extraction des résultats...")
        restaurants = await page.query_selector_all('.Nv2PK')
        if not restaurants:
            print("Aucun restaurant trouvé.")
        else:
            for i, restaurant in enumerate(restaurants):
                try:
                    name_element = await restaurant.query_selector('.qBF1Pd')
                    name = await name_element.text_content() if name_element else "N/A"

                    rating_element = await restaurant.query_selector('.MW4etd')
                    rating = await rating_element.text_content() if rating_element else "N/A"

                    review_count_element = await restaurant.query_selector('.UY7F9')
                    review_count = await review_count_element.text_content() if review_count_element else "N/A"

                    print(f"\nRestaurant {i + 1}:")
                    print(f"Nom : {name.strip()}")
                    print(f"Note : {rating.strip()}")
                    print(f"Nombre d'avis : {review_count.strip()}")

                    href = await restaurant.query_selector('a[href]')
                    if href:
                        detail_url = await href.get_attribute('href')
                        detail_page = await context.new_page()
                        print(f"Ouverture de la page de détails pour : {name.strip()}")
                        await detail_page.goto(detail_url)
                        await detail_page.wait_for_timeout(5000)

                        try:
                            await detail_page.click('text="Avis"', timeout=10000)
                            print("Onglet 'Avis' cliqué.")
                            await detail_page.wait_for_timeout(5000)
                        except Exception as e:
                            print(f"Erreur en cliquant sur l'onglet 'Avis' : {e}")

                        print("Défilement pour charger les avis visibles...")
                        while True:
                            last_review_count = len(await detail_page.query_selector_all('.jftiEf'))
                            await detail_page.evaluate("window.scrollBy(0, window.innerHeight);")
                            await detail_page.wait_for_timeout(1000)
                            new_review_count = len(await detail_page.query_selector_all('.jftiEf'))
                            if new_review_count == last_review_count:
                                break

                        # Configuration de la stratégie LLM avec GPT-4 Mini
                        extraction_strategy = LLMExtractionStrategy(
                            provider="openai/gpt-4o-mini",  # Utilisation de GPT-4 Mini
                            api_token=os.getenv("OPENAI_API_KEY"),  # Utilisation de la clé API OpenAI
                            instruction="Extraire le texte, l'auteur et la date de chaque avis Google Maps sur la page. "
                                        "Ignorer les sections comme \"Avis des internautes\" et ne pas les inclure dans les résultats. "
                                        "Fournir uniquement les avis réels laissés par les utilisateurs.",
                            schema=Review.schema()
                        )

                        async with AsyncWebCrawler() as crawler:
                            result = await crawler.arun(
                                url=detail_url,
                                extraction_strategy=extraction_strategy
                            )
                            print(result.extracted_content)

                        # Fermer l'onglet de la page de détails
                        await detail_page.close()
                    else:
                        print("Lien de page de détails non trouvé pour ce restaurant.")

                except Exception as e:
                    print(f"Erreur lors de l'extraction des informations pour le restaurant {i + 1} : {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_google_maps_reviews("Serris 77700"))