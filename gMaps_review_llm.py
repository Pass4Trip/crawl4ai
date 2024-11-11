import asyncio
import json
import os
from playwright.async_api import async_playwright
from crawl4ai.extraction_strategy import LLMExtractionStrategy

# Fonction pour utiliser gpt4o-mini pour obtenir les sélecteurs dynamiquement
async def get_selectors_via_llm(html_content, url):
    # Définir la stratégie d'extraction LLM avec GPT-4 Mini
    llm_strategy = LLMExtractionStrategy(
        provider="openai/gpt4o-mini",  # Utilisation de GPT-4 Mini
        instruction="""Vous recevrez un extrait HTML d'une page Google Maps.
                      Identifiez et retournez les sélecteurs CSS pour extraire:
                      1. Le texte complet de chaque avis
                      2. Le nom de l'auteur de chaque avis
                      3. La date de chaque avis
                      
                      Retournez ces informations au format JSON, par exemple:
                      {
                          "texte_avis": "CSS selector",
                          "nom_auteur": "CSS selector",
                          "date_avis": "CSS selector"
                      }""",
       
    )

    # Utiliser `ix` comme identifiant pour la requête, `url` pour la source, et passer le contenu HTML
    result = await llm_strategy.extract(ix=1, url=url, html=html_content)

    # Vérifier si l'appel LLM a réussi
    if result.success:
        return result.output_text  # JSON sous forme de chaîne de caractères
    else:
        print("Erreur lors de l'extraction avec LLM:", result.error_message)
        return None

# Fonction principale de scraping avec Crawl4AI et gpt4o-mini
async def scrape_google_maps_reviews(location: str):
    search_url = f"https://www.google.com/maps/search/restaurants+{location.replace(' ', '+')}/"
    
    async with async_playwright() as p:
        # Créer un contexte de navigateur unique pour partager les cookies
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # Ouvrir la première page dans ce contexte
        page = await context.new_page()
        
        print("Naviguer vers l'URL de recherche...")
        await page.goto(search_url)
        await page.wait_for_timeout(5000)  # Attendre le chargement initial de la page
        
        # Cliquer sur le bouton "Tout accepter" si présent sur la page principale
        try:
            await page.click('button:has-text("Tout accepter")')
            print("Bouton de consentement cliqué sur la page principale.")
        except Exception as e:
            print(f"Pas de bouton de consentement trouvé ou erreur sur la page principale : {e}")

        # Attendre que les résultats soient visibles
        print("Attente des résultats...")
        try:
            await page.wait_for_selector('.Nv2PK', timeout=15000)
        except Exception as e:
            print(f"Erreur d'attente pour les résultats : {e}")
            await browser.close()
            return

        # Extraire les restaurants
        print("Extraction des résultats...")
        restaurants = await page.query_selector_all('.Nv2PK')
        if not restaurants:
            print("Aucun restaurant trouvé.")
        else:
            for i, restaurant in enumerate(restaurants):
                try:
                    # Extraire le nom, la note et le nombre d'avis
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

                    # Ouvrir la page du restaurant dans un nouvel onglet dans le même contexte
                    href = await restaurant.query_selector('a[href]')
                    if href:
                        detail_url = await href.get_attribute('href')
                        detail_page = await context.new_page()  # Utiliser le même contexte pour ouvrir l'onglet
                        print(f"Ouverture de la page de détails pour : {name.strip()}")
                        await detail_page.goto(detail_url)
                        await detail_page.wait_for_timeout(5000)  # Attendre le chargement de la page de détails

                        # Cliquer sur l'onglet "Avis"
                        try:
                            await detail_page.click('text="Avis"', timeout=10000)  # Cliquez sur "Avis" par le texte
                            print("Onglet 'Avis' cliqué.")
                            await detail_page.wait_for_timeout(5000)  # Attendre que les avis se chargent
                        except Exception as e:
                            print(f"Erreur en cliquant sur l'onglet 'Avis' : {e}")

                        # Extraire le code HTML de la section des avis pour analyse par gpt4o-mini
                        html_content = await detail_page.content()

                        # Obtenir les sélecteurs pour les avis avec gpt4o-mini
                        selectors_json = await get_selectors_via_llm(html_content, detail_url)
                        if selectors_json:
                            print("Sélecteurs reçus du LLM:", selectors_json)
                            selectors = json.loads(selectors_json)  # Charger les sélecteurs en tant qu'objet Python

                            # Utiliser les sélecteurs pour extraire les avis
                            reviews = await detail_page.query_selector_all(selectors["texte_avis"])
                            print("Avis:")
                            for j, review in enumerate(reviews[:10]):
                                review_text = await review.text_content() if review else "Avis non trouvé"
                                print(f"Avis {j + 1}: {review_text.strip()}")
                        else:
                            print("Aucun sélecteur valide reçu du LLM")

                        # Fermer l'onglet de la page de détails
                        await detail_page.close()
                    else:
                        print("Lien de page de détails non trouvé pour ce restaurant.")
                
                except Exception as e:
                    print(f"Erreur lors de l'extraction des informations pour le restaurant {i + 1} : {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_google_maps_reviews("Serris 77700"))
