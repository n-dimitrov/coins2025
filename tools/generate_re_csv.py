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

series_years = {
"AND-01": "2014",
"AUT-01": "2002",
"BEL-01": "1999",
"BEL-02": "2008",
"BEL-03": "2014",
"CYP-01": "2008",
"DEU-01": "1999",
"ESP-01": "1999",
"ESP-02": "2014",
"ESP-03": "2015",
"EST-01": "2011",
"FIN-01": "1999",
"FIN-02": "2007",
"FRA-01": "1999",
"FRA-02": "2022",
"GRC-01": "2002",
"HRV-01": "2023",
"IRL-01": "2002",
"ITA-01": "1999",
"LTU-01": "2015",
"LUX-01": "2002",
"LVA-01": "2014",
"MCO-01": "2001",
"MCO-02": "2006",
"MLT-01": "2008",
"NLD-01": "1999",
"NLD-02": "2014",
"PRT-01": "2002",
"SMR-01": "2006",
"SMR-02": "2017",
"SVK-01": "2009",
"SVN-01": "2007",
"VAT-01": "2002",
"VAT-02": "2005",
"VAT-03": "2006",
"VAT-04": "2014",
"VAT-05": "2017"
}

dir = "tmp"
if not os.path.exists(dir):
    os.makedirs(dir)

input_file = f"{dir}/re_catalog.json"
output_file = f"{dir}/re.csv"

with open(input_file) as f:
    data = json.load(f)

df = pd.DataFrame(columns=["type", "year", "country", "series", "value", "id", "image", "feature", "volume"])

'''
{
    "Andorra": [
        {
            "value": "\u20ac2",
            "description": "",
            "image": "https://www.ecb.europa.eu/euro/coins/common/shared/img/ad/ad_2euro.jpg",
            "images": [
                "https://www.ecb.europa.eu/euro/coins/common/shared/img/ad/ad_2euro.jpg"
            ]
        },
'''

values = {
    "\u20ac2": 2.00,
    "\u20ac1": 1.00,
    "50 cent": 0.50,
    "20 cent": 0.20,
    "10 cent": 0.10,
    "5 cent": 0.05,
    "2 cent": 0.02,
    "1 cent": 0.01,
}

values_codes = {
    "\u20ac2": "200",
    "\u20ac1": "100",
    "50 cent": "050",
    "20 cent": "020",
    "10 cent": "010",
    "5 cent": "005",
    "2 cent": "002",
    "1 cent": "001",
}

# iterate over the data
newrows = []
for country in data:
    print(country)

    for coin in data[country]:
        index = 0
        image = coin['image']
        v = coin['value']
        value = values[v]
        vc = values_codes[v]

        ccode = three_letters[country]

        images = coin['images']
        for image in images:
            index += 1
            coinidex = "RE" + str(index)
            series = ccode + "-0" + str(index)
            year = series_years[series]

            id = "RE" + year + ccode + "-A-" + coinidex + "-" + vc

            newrows.append({
                "type": "RE",
                "year": year,
                "country": country,
                "series": series,
                "value": value,
                "id": id,
                "image": image,
                "feature": "",
                "volume": ""
            })


new_rows_df = pd.DataFrame(newrows)
df = pd.concat([df, new_rows_df], ignore_index=True)
print(df)

# unique_series = df['series'].unique()
# unique_series = sorted(unique_series)
# unique_series = "{\n" + ",\n".join([f'"{s}": "1999"' for s in unique_series]) + "\n}"
# print(unique_series)


df.to_csv(output_file, index=False)
print(f"Data saved to {output_file}")