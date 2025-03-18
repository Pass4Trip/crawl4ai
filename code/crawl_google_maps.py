import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from bs4 import BeautifulSoup

class_note = "F7nice"
class_info = "Io6YTe"
class_categories = "e2moi"
class_avis = "jJc9Ad"
class_avis_name = "d4r55"
class_avis_stats = "RfnDt"
class_avis_rate = "kvMYJc"
class_avis_time = "rsqaWe"
class_avis_text = "wiI7pd"
class_propos = "iP2t7d"
class_propos_propo = "iL3Qke"
class_propos_list = "ZQ6we"

async def multi_page_commits():
    config = CrawlerRunConfig(
            js_code = """
                document.querySelector('[aria-label="Tout accepter"]').click()
            """,
            wait_for = """js:() => {
                return document.getElementById('searchboxinput') != null
            }""",
            # js_only=True,
            session_id="session",
            wait_for_images=True
            # cache_mode=CacheMode.BYPASS
        )
    
    browser_cfg = BrowserConfig(
        headless=False,  # Visible for demonstration
        # verbose=True
    )
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:

        result = await crawler.arun(
            "https://www.google.com/maps",
            config = config
            )
        #print(result.html)
        print("First OK")

        config2 = CrawlerRunConfig(
            # js_code = ["document.getElementById('searchboxinput').value = 'Plan Pizza - Saint-Étienne';",
            #            "document.getElementById('searchbox-searchbutton').click();"],
            wait_for = """js:() => {
                        return document.querySelector('[aria-label="Plan Pizza - Saint-Étienne"]') != null;
                    }""",
            #js_only=True,
            session_id="session",
            wait_for_images=True
            # cache_mode=CacheMode.BYPASS
        )

        result2 = await crawler.arun(
            "https://www.google.com/maps/search/Plan+Pizza+-+Saint+Etienne",
            config = config2
            )
        #print(result2.markdown)
        print("Second OK")

        extract_presentation(result2.html)

        # document.querySelector('[aria-label="Plan Pizza - Saint-Étienne - Avis"]').click();

        config3 = CrawlerRunConfig(
            js_code = """
                document.querySelectorAll('[role="tab"]')[1].click();
                for (let pas = 0; pas < 2; pas++) {
                    setTimeout(() => {
                        document.getElementsByClassName("m6QErb DxyBCb kA9KIf dS8AEf XiKgde ")[0].scrollTop += 20000;
                    }, pas * 2000);
                }
                """,
            wait_for = """js:() => {
                         setTimeout(() => {
                            return true;
                         }, 4000);
                     }""",
            #js_only=True,
            session_id="session",
            wait_for_images=True,
            # cache_mode=CacheMode.BYPASS
        )

        result3 = await crawler.arun(
            "https://www.google.com/maps/search/Plan+Pizza+-+Saint+Etienne",
            config = config3
            )
        #print(result3.markdown)
        print("Troisieme OK")
        extract_avis(result3.html)

        config4 = CrawlerRunConfig(
            js_code = """
                document.querySelectorAll('[role="tab"]')[2].click();
                """,
            wait_for = """js:() => {
                         return document.querySelector('[aria-label="Plan Pizza - Saint-Étienne"]') != null;
                     }""",
            #js_only=True,
            session_id="session",
            wait_for_images=True,
            # cache_mode=CacheMode.BYPASS
        )

        result4 = await crawler.arun(
            "https://www.google.com/maps/search/Plan+Pizza+-+Saint+Etienne",
            config = config4
            )
        print("Quatrieme OK")
        #print(result4.markdown)
        extract_apropos(result4.html)

def extract_apropos(html):
    soup = BeautifulSoup(html, 'html.parser')
    all_propos = soup.find_all(class_=class_propos)

    for propos in all_propos:
        propo = propos.find(class_=class_propos_propo)

        attributs = propos.select('[aria-label]')

        print(propo)

        for attribut in attributs:
            print(attribut)

    #print(all_propos)

def extract_avis(html):
    soup = BeautifulSoup(html, 'html.parser')
    all_categories = soup.find_all(class_=class_categories)

    for categorie in all_categories:
        print(categorie.text)

    all_avis = soup.find_all(class_=class_avis)

    for avis in all_avis:
        name = avis.find(class_=class_avis_name)

        stats = avis.find(class_=class_avis_stats)

        rate = avis.find(class_=class_avis_rate)['aria-label']

        time = avis.find(class_=class_avis_time)

        text = avis.find(class_=class_avis_text)

        print(text)
    print(len(all_avis))


def extract_presentation(html):
    soup = BeautifulSoup(html, 'html.parser')
    note_all = soup.find(class_=class_note)

    note = note_all.find('span', attrs={"aria-hidden": "true"})
    nb_avis = note_all.select('[aria-label$="avis"]')

    price = soup.find('span', string=lambda text: text and text.strip().endswith('€'))

    info = soup.find_all(class_=class_info)

    adresse = info[0]

    website = info[5]

    phone = info[6]


    print(adresse)
    print(website)
    print(phone)
        

async def main():
    await multi_page_commits()

if __name__ == "__main__":
    asyncio.run(main())