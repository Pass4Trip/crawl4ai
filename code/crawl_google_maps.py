import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from bs4 import BeautifulSoup
import psycopg2

class_note = "F7nice"
class_type = "DkEaL"
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
class_check_ok = "ZKCDEc"

connection = psycopg2.connect(database="myboun", user="p4t", password="o3CCgX7StraZqvRH5GqrOFLuzt5R6C", host="vps-af24e24d.vps.ovh.net", port=30030)
connection.autocommit = True

cursor = connection.cursor()

cursor.execute("select name, addr_city from public.poi where name != '' and addr_city != '' limit 100;")

records = cursor.fetchall()

restaurants = []

for record in records:
    #print(record[0] + " - " + record[1])
    restaurants.append(record[0] + " - " + record[1])

print(restaurants)

#cursor.execute("DROP TABLE IF EXISTS restaurants.informationscraping;")

cursor.execute("CREATE TABLE IF NOT EXISTS restaurants.informationscraping (id serial PRIMARY KEY, name varchar, adresse varchar, website varchar, phone varchar, note varchar, nbavis varchar, price varchar, type varchar);")

#cursor.execute("DROP TABLE IF EXISTS restaurants.avisscraping;")

cursor.execute("CREATE TABLE IF NOT EXISTS restaurants.avisscraping (id serial PRIMARY KEY, id_restaurant serial, name varchar, stats varchar, rate varchar, time varchar, text varchar);")

#cursor.execute("DROP TABLE IF EXISTS restaurants.categoriescraping;")

cursor.execute("CREATE TABLE IF NOT EXISTS restaurants.categoriescraping (id serial PRIMARY KEY, id_restaurant serial, categorie varchar, nbcited serial);")

#cursor.execute("DROP TABLE IF EXISTS restaurants.aproposscraping;")

cursor.execute("CREATE TABLE IF NOT EXISTS restaurants.aproposscraping (id serial PRIMARY KEY, id_restaurant serial, attribut varchar);")

async def multi_page_commits():
    config = CrawlerRunConfig(
            js_code = """
                document.querySelector('[aria-label="Tout accepter"]').click()
            """,
            wait_for = """js:() => {
                return document.getElementById('searchboxinput') != null
            }""",
            session_id="session",
            wait_for_images=True
        )
    
    browser_cfg = BrowserConfig(
        headless=True,  # Visible for demonstration
    )
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:

        result = await crawler.arun(
            "https://www.google.com/maps",
            config = config
            )
        print("Validation initial")

        for restaurant in restaurants:
            print(restaurant)

            cursor.execute("SELECT name FROM restaurants.informationscraping WHERE name = %s", (restaurant.split(" - ")[0],))

            if cursor.fetchone() == None:
                config2 = CrawlerRunConfig(
                    #wait_for = "js:() => { return document.querySelector('[aria-label=\"" + restaurant.split(" - ")[0] + "\"]') != null; }",
                    wait_for = """js:() => {
                                    setTimeout(() => {
                                        return true;
                                    }, 1000);
                                }""",
                    session_id="session",
                    page_timeout=5000,
                    wait_for_images=True
                )

                result2 = await crawler.arun(
                    "https://www.google.com/maps/search/" + restaurant.replace(" ", "+"),
                    config = config2
                    )
                print("Get presentation")

                soup = BeautifulSoup(result2.html, 'html.parser')
                check = soup.find(class_=class_check_ok)

                #print(check)

                if check != None:
                    extract_presentation(result2.html, restaurant)

                    cursor.execute("select id from restaurants.informationscraping order by id desc limit 1;")

                    id = cursor.fetchone()

                    print("Restaurant : " + str(id[0]))

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
                        session_id="session",
                        page_timeout=10000,
                        wait_for_images=True
                    )

                    result3 = await crawler.arun(
                        "https://www.google.com/maps/search/" + restaurant.replace(" ", "+"),
                        config = config3
                        )
                    print("Get avis")
                    extract_avis(result3.html, id[0])

                    config4 = CrawlerRunConfig(
                        js_code = """
                            document.querySelectorAll('[role="tab"]')[2].click();
                            """,
                        #wait_for = "js:() => { return document.querySelector('[aria-label=\"" + restaurant.split(" - ")[0] + "\"]') != null; }",
                        wait_for = """js:() => {
                                    setTimeout(() => {
                                        return true;
                                    }, 1000);
                                }""",
                        session_id="session",
                        page_timeout=5000,
                        wait_for_images=True
                    )

                    result4 = await crawler.arun(
                        "https://www.google.com/maps/search/" + restaurant.replace(" ", "+"),
                        config = config4
                        )
                    print("Get a propos")
                    extract_apropos(result4.html, id[0])
            else:
                print("Restaurant déjà présent")

def extract_apropos(html, id_restaurant):
    soup = BeautifulSoup(html, 'html.parser')
    all_propos = soup.find_all(class_=class_propos)

    for propos in all_propos:
        #propo = propos.find(class_=class_propos_propo)

        attributs = propos.select('[aria-label]')

        for attribut in attributs:
            cursor.execute("INSERT INTO restaurants.aproposscraping (id_restaurant, attribut) VALUES (%s, %s)", (id_restaurant, attribut.text))

    print("A propos inserted")

    #print(all_propos)

def extract_avis(html, id_restaurant):
    soup = BeautifulSoup(html, 'html.parser')
    all_categories = soup.find_all(class_=class_categories)

    for categorie in all_categories:
        if categorie.text != "Tout" and "+" not in categorie.text:
            try:
                int(categorie.text.split(" ")[1])
                cursor.execute("INSERT INTO restaurants.categoriescraping (id_restaurant, categorie, nbcited) VALUES (%s, %s, %s)", (id_restaurant, categorie.text.split(" ")[0], categorie.text.split(" ")[1]))
            except:
                print("Error cast")

    all_avis = soup.find_all(class_=class_avis)

    for avis in all_avis:
        name = avis.find(class_=class_avis_name)

        if name == None:
            name = ""
        else:
            name = name.text

        stats = avis.find(class_=class_avis_stats)

        if stats == None:
            stats = ""
        else:
            stats = stats.text

        rate = avis.find(class_=class_avis_rate)

        if rate == None:
            rate = ""
        else:
            rate = rate['aria-label']

        time = avis.find(class_=class_avis_time)

        if time == None:
            time = ""
        else:
            time = time.text

        text = avis.find(class_=class_avis_text)

        if text == None:
            text = ""
        else:
            text = text.text

        cursor.execute("INSERT INTO restaurants.avisscraping (id_restaurant, name, stats, rate, time, text) VALUES (%s, %s, %s, %s, %s, %s)", (id_restaurant, name, stats, rate, time, text))
    print(len(all_avis))
    print("Avis inserted")


def extract_presentation(html, restaurant_name):
    soup = BeautifulSoup(html, 'html.parser')
    note_all = soup.find(class_=class_note)

    note = ""
    nb_avis = ""
    if note_all != None:
        note = note_all.find('span', attrs={"aria-hidden": "true"})
        nb_avis = note_all.select('[aria-label$="avis"]')[0]

    if note == None:
        note = ""
    else:
        note = note.text
    if nb_avis == None:
        nb_avis = ""
    else:
        nb_avis = nb_avis.text

    price = soup.find('span', string=lambda text: text and text.strip().endswith('€'))

    if price == None:
        price = ""
    else:
        price = price.text

    type = soup.find(class_=class_type)

    if type == None:
        type = ""
    else:
        type = type.text

    info = soup.find_all(class_=class_info)

    adresse = ""
    website = ""
    phone = ""
    if info != None:
        if len(info) > 0:
            adresse = info[0].text
        if len(info) > 5:
            website = info[5].text
        if len(info) > 6:
            phone = info[6].text

    cursor.execute("INSERT INTO restaurants.informationscraping (name, adresse, website, phone, note, nbavis, price, type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (restaurant_name.split(" - ")[0], adresse, website, phone, note, nb_avis, price, type))

    print("Add presentation")
        

async def main():
    print("Start")
    await multi_page_commits()

if __name__ == "__main__":
    asyncio.run(main())