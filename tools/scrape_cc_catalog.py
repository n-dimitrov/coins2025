from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time
import os
import json
import pandas as pd
import argparse

options = Options()
options.add_argument("Accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7")
options.add_argument("User-Agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

# CLI
parser = argparse.ArgumentParser(description='Scrape ECB commemorative coins page and generate JSON/CSV outputs')
parser.add_argument('-y', '--year', default='2025', help='Year to scrape (default: 2025)')
parser.add_argument('-o', '--outdir', default='tmp', help='Output directory (default: tmp)')
parser.add_argument('--no-csv', action='store_true', help='Do not generate CSV, only JSON')
parser.add_argument('--skip-placeholder', dest='skip_placeholder', action='store_true', help='Skip placeholder images (default)')
parser.add_argument('--no-skip-placeholder', dest='skip_placeholder', action='store_false', help='Do not skip placeholder images')
parser.set_defaults(skip_placeholder=True)
args = parser.parse_args()

year = args.year
outdir = args.outdir

driver = webdriver.Chrome(options=options)
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

if not os.path.exists(outdir):
    os.makedirs(outdir, exist_ok=True)

filename = f"{outdir}/cc_catalog.json"

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

# --- generate CSV (same output path used by previous generate_cc_csv.py) ---
output_csv = f"{outdir}/cc.csv"

three_letters = {
    "Andorra": "AND",
    "Austria": "AUT",
    "Belgium": "BEL",
    "Croatia": "HRV",
    "Cyprus": "CYP",
    "Estonia": "EST",
    "Euro area countries": "Euro area countries",
    "Finland": "FIN",
    "France": "FRA",
    "Germany": "DEU",
    "Greece": "GRC",
    "Ireland": "IRL",
    "Italy": "ITA",
    "Latvia": "LVA",
    "Lithuania": "LTU",
    "Luxembourg": "LUX",
    "Malta": "MLT",
    "Monaco": "MCO",
    "Netherlands": "NLD",
    "Portugal": "PRT",
    "San Marino": "SMR",
    "Slovakia": "SVK",
    "Slovenia": "SVN",
    "Spain": "ESP",
    "Vatican City": "VAT"
}

if not args.no_csv:
    print("Generating CSV from", filename)
    with open(filename) as f:
        ccdata = json.load(f)

newrows = []
skipped_coins = []  # collect coins skipped because of placeholder images
for y in ccdata:
    for country in ccdata[y]:
        if country == "Euro area countries":
            for coin in ccdata[y][country]:
                feature = coin.get('feature', '')
                image_main = coin.get('image', '')
                volume = coin.get('volume', '')
                series = coin.get('series', '')
                coinidex = series.split('-')[-1]
                images = coin.get('images', []) or [image_main]

                # optionally skip the entire coin if any placeholder images are present
                if args.skip_placeholder:
                    placeholder_images = [img for img in images if 'placeholder_coming_soon' in img.lower()]
                    if placeholder_images:
                        skipped_coins.append({
                            "year": y,
                            "country": country,
                            "series": series,
                            "feature": feature,
                            "skipped_images": placeholder_images
                        })
                        # skip this coin entirely
                        continue

                for image in images:
                    # try to extract country code from filename; fallback to XXX
                    try:
                        c = image.split('_')[-1].split('.jpg')[0]
                    except Exception:
                        c = image
                    ccode = "XXX"
                    if three_letters.get(c) is not None:
                        ccode = three_letters[c]
                    _id = "CC" + y + ccode + "-A-" + coinidex + "-200"

                    row = {
                        "type": "CC",
                        "year": y,
                        "country": c,
                        "value": 2.00,
                        "series": series,
                        "id": _id,
                        "feature": feature,
                        "image": image,
                        "volume": volume if volume is not None else ""
                    }
                    newrows.append(row)
        else:
            index = 0
            for coin in ccdata[y][country]:
                feature = coin.get('feature', '')
                image = coin.get('image', '')

                # skip single-image coins whose image is a placeholder (if requested)
                if args.skip_placeholder and isinstance(image, str) and 'placeholder_coming_soon' in image.lower():
                    skipped_coins.append({
                        "year": y,
                        "country": country,
                        "series": coin.get('series', ''),
                        "feature": feature,
                        "skipped_image": image
                    })
                    continue

                volume = coin.get('volume', '')
                series = coin.get('series', '')
                ccode = three_letters.get(country, 'XXX')
                index += 1
                coinidex = "CC" + str(index)
                _id = "CC" + y + ccode + "-A-" + coinidex + "-200"

                row = {
                    "type": "CC",
                    "year": y,
                    "country": country,
                    "value": 2.00,
                    "series": series,
                    "id": _id,
                    "feature": feature,
                    "image": image,
                    "volume": volume if volume is not None else ""
                }
                newrows.append(row)

    df = pd.DataFrame(newrows)
    if not df.empty:
        df = df[["type", "year", "country", "series", "value", "id", "image", "feature", "volume"]]
        df.to_csv(output_csv, index=False)
        print(f"Data saved to {output_csv}")
    else:
        print("No rows to save to CSV")
    # report skipped placeholder coins
    if skipped_coins:
        print(f"Skipped {len(skipped_coins)} coin(s) because of placeholder images. Writing details to {outdir}/skipped_cc.json")
        try:
            with open(f"{outdir}/skipped_cc.json", 'w') as sf:
                json.dump(skipped_coins, sf, indent=2)
        except Exception as e:
            print("Failed to write skipped coins file:", e)
    else:
        print("No placeholder-skipped coins detected.")
else:
    print('CSV generation skipped by --no-csv')