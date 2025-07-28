from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time
import os
import json

options = Options()
options.add_argument("Accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7")
options.add_argument("User-Agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)

urls = [
    "https://www.ecb.europa.eu/euro/coins/html/ad.en.html", # Andorra
    "https://www.ecb.europa.eu/euro/coins/html/at.en.html", # Austria
    "https://www.ecb.europa.eu/euro/coins/html/be.en.html", # Belgium
    "https://www.ecb.europa.eu/euro/coins/html/hr.en.html", # Croatia
    "https://www.ecb.europa.eu/euro/coins/html/cy.en.html", # Cyprus
    "https://www.ecb.europa.eu/euro/coins/html/et.en.html", # Estonia
    "https://www.ecb.europa.eu/euro/coins/html/fi.en.html", # Finland
    "https://www.ecb.europa.eu/euro/coins/html/fr.en.html", # France
    "https://www.ecb.europa.eu/euro/coins/html/de.en.html", # Germany
    "https://www.ecb.europa.eu/euro/coins/html/gr.en.html", # Greece
    "https://www.ecb.europa.eu/euro/coins/html/ie.en.html", # Ireland
    "https://www.ecb.europa.eu/euro/coins/html/it.en.html", # Italy
    "https://www.ecb.europa.eu/euro/coins/html/lv.en.html", # Latvia
    "https://www.ecb.europa.eu/euro/coins/html/lt.en.html", # Lithuania
    "https://www.ecb.europa.eu/euro/coins/html/lu.en.html", # Luxembourg
    "https://www.ecb.europa.eu/euro/coins/html/mt.en.html", # Malta
    "https://www.ecb.europa.eu/euro/coins/html/mo.en.html", # Monaco
    "https://www.ecb.europa.eu/euro/coins/html/nl.en.html", # Netherlands
    "https://www.ecb.europa.eu/euro/coins/html/pt.en.html", # Portugal
    "https://www.ecb.europa.eu/euro/coins/html/sm.en.html", # San Marino
    "https://www.ecb.europa.eu/euro/coins/html/sk.en.html", # Slovakia
    "https://www.ecb.europa.eu/euro/coins/html/sl.en.html", # Slovenia
    "https://www.ecb.europa.eu/euro/coins/html/es.en.html", # Spain
    "https://www.ecb.europa.eu/euro/coins/html/va.en.html", # Vatican City
]


country = "Andorra"
url = urls[0]

print("Country: ", country , "Loading URL: ", url)
driver.get(url)

time.sleep(10)

"""
<div class="boxes -grey">
   <div class="box">
      <div class="coins loaded" data-image="/euro/coins/shared/img/coin_bg.jpg" style="background-image: url(&quot;/euro/coins/shared/img/coin_bg.jpg&quot;);">
         <picture class="coin-cropper"><img src="/euro/coins/common/shared/img/ad/ad_2euro.jpg" loading="lazy"></picture>
      </div>
      <div class="content-box">
         <h3>€2</h3>
         <p></p>
         <p>The €2 coin shows the coat of arms of Andorra with the motto "virtus unita fortior" (virtue united is stronger). Edge-lettering of the €2 coin: 2 **, repeated six times.</p>
         <p></p>
      </div>
   </div>
</div>
"""
coins = driver.find_elements(By.XPATH, '//div[@class="box"]')
print("Coins: ", len(coins))
output = {}
for coin in coins:
    value = coin.find_element(By.XPATH, './/h3').text
    description = coin.find_element(By.XPATH, './/p').text
    image = coin.find_element(By.XPATH, './/img').get_attribute('src')
    print(value)

    images = []
    items = coin.find_elements(By.CSS_SELECTOR, '.coin-cropper')
    for item in items:
        img = item.find_element(By.TAG_NAME, 'img')
        print(img.get_attribute('src'))
        images.append(img.get_attribute('src'))

    # print(images)

    coin_json = {
        "value": value,
        "description": description,
        "image": image,
        "images": images
    }
    if country not in output:
        output[country] = []
    output[country].append(coin_json)

driver.quit()


dir = "tmp"
if not os.path.exists(dir):
    os.makedirs(dir)

filename = f"{dir}/re_catalog.json"

# load
print("Loading", filename)
data = {}
if os.path.exists(filename):
    print("File exists, loading data")
    with open(filename, 'r') as f:
        data = f.read()
        data = json.loads(data)
else:
    print("File does not exist, creating new data structure")
    data = {}   

data.update(output)

# save 
with open(filename, 'w') as f:
    f.write(json.dumps(data, indent=4))

print('Saved', filename)
