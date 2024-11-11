import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://www.leblogduhacker.fr/")
        print(result.markdown[:500])  # Affiche les 500 premiers caractères du contenu extrait

if __name__ == "__main__":
    asyncio.run(main())
