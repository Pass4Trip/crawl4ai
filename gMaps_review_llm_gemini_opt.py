import asyncio
import json
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
            await page.wait_for_selector('.Nv2PK', timeout=15000)  # Classe CSS pour les résultats de recherche
        except Exception as e:
            print(f"Erreur d'attente pour les résultats : {e}")
            await browser.close()
            return

        print("Extraction des résultats...")
        restaurants = await page.query_selector_all('.Nv2PK')

        if not restaurants:
            print("Aucun restaurant trouvé.")
            await browser.close()
            return

        # Extraction unique des sélecteurs avec LLM
        print("Extraction des sélecteurs avec LLM...")

        extraction_strategy = LLMExtractionStrategy(
            provider="openai/gpt-4-mini",
            api_token=os.getenv("OPENAI_API_KEY"),
            instruction="""Vous recevrez un extrait HTML d'une page Google Maps avec des résultats de recherche de restaurants.
                            Identifiez et retournez les sélecteurs CSS pour extraire :
                            1. Le nom du restaurant
                            2. La note du restaurant
                            3. Le nombre d'avis du restaurant
                            4. L'URL de la page de détails du restaurant
                            5. Sur la page de détails, le texte complet de chaque avis
                            6. Sur la page de détails, le nom de l'auteur de chaque avis
                            7. Sur la page de détails, la date de chaque avis
                            Retournez ces informations au format JSON, par exemple :
                            {
                              "nom_restaurant": "CSS selector",
                              "note_restaurant": "CSS selector",
                              "nombre_avis_restaurant": "CSS selector",
                              "url_page_details_restaurant": "CSS selector",
                              "texte_avis": "CSS selector",
                              "nom_auteur": "CSS selector",
                              "date_avis": "CSS selector"
                            }"""
        )

        # Utiliser le premier restaurant pour extraire les sélecteurs
        first_restaurant_url = await (await restaurants[0].query_selector('a[href]')).get_attribute('href')

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url=first_restaurant_url,
                extraction_strategy=extraction_strategy
            )
            
        # Vérifier si l'appel au LLM a réussi et extraire les sélecteurs
        if result.success:
            selectors = json.loads(result.extracted_content)
            print("Sélecteurs extraits :", selectors)
        else:
            print("Erreur lors de l'extraction des sélecteurs avec LLM :", result.error_message)
            await browser.close()
            return

        for i, restaurant in enumerate(restaurants):
            try:
                # Extraire le nom, la note et le nombre d'avis en utilisant les sélecteurs
                name_element = await restaurant.query_selector(selectors["nom_restaurant"])
                name = await name_element.text_content() if name_element else "N/A"

                rating_element = await restaurant.query_selector(selectors["note_restaurant"])
                rating = await rating_element.text_content() if rating_element else "N/A"

                review_count_element = await restaurant.query_selector(selectors["nombre_avis_restaurant"])
                review_count = await review_count_element.text_content() if review_count_element else "N/A"

                print(f"\nRestaurant {i + 1}:")
                print(f"Nom : {name.strip()}")
                print(f"Note : {rating.strip()}")
                print(f"Nombre d'avis : {review_count.strip()}")

                # --- Extraction des avis ---
                
                href = await restaurant.query_selector(selectors["url_page_details_restaurant"])  # Utiliser le sélecteur pour l'URL
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
                        continue  # Passer au restaurant suivant en cas d'erreur

                    print("Défilement pour charger les avis visibles...")
                    while True:
                        last_review_count = len(await detail_page.query_selector_all('.jftiEf'))
                        await detail_page.evaluate("window.scrollBy(0, window.innerHeight);")
                        await detail_page.wait_for_timeout(1000)
                        new_review_count = len(await detail_page.query_selector_all('.jftiEf'))
                        if new_review_count == last_review_count:
                            break

                    try:
                        reviews = await detail_page.query_selector_all(selectors["texte_avis"])
                        print("Avis :")
                        if reviews:
                            for j, review in enumerate(reviews[:10]):
                                review_text = await review.text_content() if review else "Avis non trouvé"
                                author_element = await reviews[j].query_selector(selectors["nom_auteur"])
                                author = await author_element.text_content() if author_element else "Anonyme"
                                date_element = await reviews[j].query_selector(selectors["date_avis"])
                                date = await date_element.text_content() if date_element else "Date inconnue"
                                print(f"Avis {j + 1} par {author} ({date}): {review_text.strip()}")
                        else:
                            print("Aucun avis trouvé.")
                        print("-" * 50)
                    except Exception as e:
                        print(f"Erreur lors de l'extraction des avis pour {name.strip()} : {e}")

                    await detail_page.close()
                else:
                    print("Lien de page de détails non trouvé pour ce restaurant.")

            except Exception as e:
                print(f"Erreur lors du traitement du restaurant {i + 1} : {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_google_maps_reviews("Serris 77700"))