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
    "https://www.ecb.europa.eu/euro/coins/comm/html/comm_2004.en.html",
]

# https://www.ecb.europa.eu/euro/coins/comm/html/comm_2024.en.html
year = "2024"
url = "https://www.ecb.europa.eu/euro/coins/comm/html/comm_" + year + ".en.html"

print("Year: ", year , "Loading URL: ", url)
driver.get(url)

time.sleep(10)

"""
    <div class="boxes -grey">
        <div class="box">
        <div data-image="/euro/coins/shared/img/coin_bg.jpg" class="coins loaded" style="background-image: url(&quot;/euro/coins/shared/img/coin_bg.jpg&quot;);">
            <picture class="coin-cropper -attribution">
                <source srcset="comm_2004/comm_2004_va.webp" type="image/webp">
                <source srcset="comm_2004/comm_2004_va.jpg" type="image/jpeg">
                <img src="comm_2004/comm_2004_va.jpg" loading="lazy">
                <span class="attribution"><span class="attribution-details">© Martin Münd/ECB</span>
                <button aria-label="Photographer"></button>
                </span>
            </picture>
        </div>
        <div class="content-box">
            <h3>Vatican City</h3>
            <div>
                <p><strong>Feature:</strong>75th anniversary of the founding of the Vatican City State </p>
                <p><strong>Description:</strong> The inner part shows a schematic representation of the perimeter walls of the Vatican City with St Peter's Basilica in the foreground. Also in the inner part are the inscriptions '75 <sup>o</sup> ANNO DELLO STATO'
                    and '1929-2004' as well as, in smaller letters, the name of the designer 'VEROI' and the initials of the engraver 'L.D.S. INC.'. The outer part of the coin features the twelve stars of the European Union and the inscription 'CITTA' DEL VATICANO'.
                    </p>
                <p><strong>Issuing volume:</strong> 100,000 coins </p>
                <p><strong>Issuing date:</strong> December 2004</p>
            </div>
        </div>
        </div>
    </div>
"""
coins = driver.find_elements(By.XPATH, '//div[@class="box"]')
print("Coins: ", len(coins))
output = {}
for coin in coins:
    # get coin idS
    coin_class_id = coin.get_attribute('id')

    country = coin.find_element(By.XPATH, './/h3').text
    # Vatican means Vatican City
    if country == "Vatican":
        country = "Vatican City"
    featrue = coin.find_element(By.XPATH, './/p[1]')
    description = coin.find_element(By.XPATH, './/p[2]')
    volume = coin.find_element(By.XPATH, './/p[3]')
    image_url = coin.find_element(By.XPATH, './/img').get_attribute('src')

    feature = featrue.text
    if (len(featrue.text.split(':')) > 1):
        feature = featrue.text.split(':')[1].strip()
    descr = description.text
    if (len(description.text.split(':')) > 1):
        descr = description.text.split(':')[1].strip()
    vol = volume.text
    if (len(volume.text.split(':')) > 1):
        vol = volume.text.split(':')[1].strip()

    images = []
    multiples = coin.find_elements(By.XPATH, '//div[@class="flickity-slider"]')
    if len(coin_class_id) > 0 and len(multiples) > 0:
        first_imgage_url = multiples[0].find_element(By.XPATH, './/div[@class="item is-selected"]//img').get_attribute('src')
        images.append(first_imgage_url)

        """
        <picture class="coin-cropper carousel-cell -attribution">
          <source srcset="comm_2009/joint_comm_2009_Belgium.webp" type="image/webp">          
          <source srcset="comm_2009/joint_comm_2009_Belgium.jpg" type="image/jpeg">
          <img src="comm_2009/joint_comm_2009_Belgium.jpg" loading="lazy">
      <span class="attribution"><span class="attribution-details">© Martin Münd/ECB</span> <button aria-label="Photographer"></button></span></picture>
        """
        multiples_contries = multiples[0].find_elements(By.XPATH, './/div[@class="item"]')
        print("Countries: ", len(multiples_contries))
        for multiple in multiples_contries:
            image_url = multiple.find_element(By.XPATH, './/img').get_attribute('src')
            images.append(image_url)

    if (len(images)==0):
        coin_json = {
            "country": country,
            "feature": feature,
            "description": descr,
            "image": image_url,
            "year": year,
            "volume": vol,
            "series": "CC-" + year
        }
        if country not in output:
            output[country] = []
        output[country].append(coin_json)
    else:
        coin_json = {
            "country": country,
            "feature": feature,
            "description": descr,
            "image": image_url,
            "images": images,
            "year": year,
            "volume": vol,
            "series": "CC-" + year
        }
        if country not in output:
            output[country] = []
        output[country].append(coin_json)

driver.quit()

dir = "tmp"
if not os.path.exists(dir):
    os.makedirs(dir)

filename = f"{dir}/cc_catalog.json"

if os.path.exists(filename):
    with open(filename, 'r') as f:
        data = json.load(f)      
else:
    data = {}
data[year] = output

# save cc.json
with open(filename, 'w') as f:
    f.write(json.dumps(data, indent=4))

print(f'Saved {filename}')