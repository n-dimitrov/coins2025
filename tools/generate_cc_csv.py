import pandas as pd
import json
import os

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

'''
{
    "2004": {
        "Vatican City": [
            {
                "country": "Vatican City",
                "feature": "75th anniversary of the founding of the Vatican City State",
                "description": "The inner part shows a schematic representation of the perimeter walls of the Vatican City with St Peter's Basilica in the foreground. Also in the inner part are the inscriptions '75\no\nANNO DELLO STATO' and '1929-2004' as well as, in smaller letters, the name of the designer 'VEROI' and the initials of the engraver 'L.D.S. INC.'. The outer part of the coin features the twelve stars of the European Union and the inscription 'CITTA' DEL VATICANO'.",
                "image": "https://www.ecb.europa.eu/euro/coins/comm/html/comm_2004/comm_2004_va.jpg",
                "year": "2004",
                "volume": "100,000 coins",
                "series": "CC-2020"
            }
        ],

    }
}
'''

dir = "tmp"
if not os.path.exists(dir):
    os.makedirs(dir)

input_file = f"{dir}/cc_catalog.json"
output_file = f"{dir}/cc.csv"

# Load the data
print("Loading data from ", input_file)
with open(input_file) as f:
    data = json.load(f)

df = pd.DataFrame(columns=["type", "year", "country", "series", "value", "id", "image", "feature", "volume"])

# iterate over the data
newrows = []
for year in data:
    print(year)
    for country in data[year]:
        print("  " + country)
        if (country == "Euro area countries"):
            for coin in data[year][country]:
                feature = coin['feature']
                description = coin['description']
                image = coin['image']
                volume = coin['volume']
                series = coin['series']
                coinidex = series.split('-')[-1]
                images = coin['images']
                for image in images:
                    c = image.split('_')[-1].split('.jpg')[0]    
                    ccode = "XXX"
                    if (three_letters.get(c) != None):
                        ccode = three_letters[c]
                    id = "CC" + year + ccode + "-A-" + coinidex + "-200"
                    # print(c + " " + ccode + " " + id)

                    row = {
                        "type": "CC",
                        "year": year,
                        "country": c,
                        "value": 2.00,
                        "series": series,
                        "id": id,
                        "feature": feature,
                        "image": image,
                        "volume": ""
                     }
                    newrows.append(row)

        else:
            index = 0
            for coin in data[year][country]:
                feature = coin['feature']
                description = coin['description']
                image = coin['image']
                volume = coin['volume']
                series = coin['series']
                ccode = three_letters[country]
                index += 1
                coinidex = "CC" + str(index)
                id = "CC" + year + ccode + "-A-" + coinidex + "-200"

                row = {
                        "type": "CC",
                        "year": year,
                        "country": country,
                        "value": 2.00,
                        "series": series,
                        "id": id,
                        "feature": feature,
                        "image": image,
                        "volume": volume
                     }
                newrows.append(row)

               
new_rows_df = pd.DataFrame(newrows)
df = pd.concat([df, new_rows_df], ignore_index=True)

print(df)
df.to_csv(output_file, index=False)
print(f"Data saved to {output_file}")