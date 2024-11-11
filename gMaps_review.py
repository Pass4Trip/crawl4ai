import asyncio
from playwright.async_api import async_playwright

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

                        # Scroller pour charger tous les avis
                        print("Défilement pour charger les avis visibles...")
                        for _ in range(5):  # Augmentez le nombre si nécessaire
                            await detail_page.evaluate("window.scrollBy(0, window.innerHeight);")
                            await detail_page.wait_for_timeout(1000)

                        # Extraire les avis en utilisant un sélecteur plus précis
                        reviews = await detail_page.query_selector_all('.jftiEf')  # Classe pour chaque conteneur d'avis
                        print("Avis:")
                        if reviews:
                            for j, review in enumerate(reviews[:10]):
                                # Extraire le texte complet de l'avis
                                review_text_element = await review.query_selector('.review-full-text') or await review.query_selector('.wiI7pd')  # Alternative pour le texte de l'avis
                                review_text = await review_text_element.text_content() if review_text_element else "N/A"
                                
                                # Extraire le nom de l'auteur
                                author_element = await review.query_selector('.d4r55')
                                author = await author_element.text_content() if author_element else "Anonyme"
                                
                                # Extraire la date de publication
                                date_element = await review.query_selector('.rsqaWe')
                                date = await date_element.text_content() if date_element else "Date inconnue"
                                
                                print(f"Avis {j + 1} par {author} ({date}): {review_text.strip()}")
                        else:
                            print("Aucun avis trouvé.")
                        print("-" * 50)
                        
                        # Fermer l'onglet de la page de détails
                        await detail_page.close()
                    else:
                        print("Lien de page de détails non trouvé pour ce restaurant.")
                
                except Exception as e:
                    print(f"Erreur lors de l'extraction des informations pour le restaurant {i + 1} : {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_google_maps_reviews("Serris 77700"))
