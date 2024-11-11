import asyncio
from crawl4ai import AsyncWebCrawler

async def scrape_google_maps_search(query: str, location: str):
    search_url = f"https://www.google.com/search?q={query}+{location.replace(' ', '+')}"
    
    async with AsyncWebCrawler(verbose=True, browser_type="chromium", headless=True) as crawler:
        # Recherche Google pour des restaurants autour de Serris
        result = await crawler.arun(
            url=search_url,
            wait_for="css:.tF2Cxc",  # Attendre que les résultats de recherche soient visibles
            process_iframes=True,  # Gérer les iframes si nécessaire
            simulate_user=True,  # Simuler le comportement humain
            magic=True  # Activer toutes les fonctionnalités anti-détection
        )
        
        if result.success:
            print("Contenu extrait :")
            print(result.markdown)
        else:
            print(f"Erreur : {result.error_message}")

if __name__ == "__main__":
    asyncio.run(scrape_google_maps_search("restaurants", "Serris 77700"))
