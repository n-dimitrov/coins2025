import pandas as pd

three_letters = {
    "Andorra": "AND",
    "Austria": "AUT",
    "Belgium": "BEL",
    "Croatia": "HRV",
    "Cyprus": "CYP",
    "Estonia": "EST",
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
# load old.csv
df = pd.read_csv('old.csv', delimiter=';')
# print(df)    

names = df['name'].unique()
names = sorted(names)

values = df['value'].unique()
values = sorted(values)

countries = df['country'].unique()
countries = sorted(countries)

series = df['series'].unique()
series = sorted(series)

print(names)
print(values)
print(countries)
print(series)

newrows = []
for index, row in df.iterrows():
    name = row['name']
    value = row['value']
    country = row['country']
    s = row['series']
    date = row['date']

    ccode = three_letters[country]
    type = "RE"
    
    if value == "2.00c":
        type = "CC"
        v = 2.00
    else:
        v = float(value)

    series = 'XXX'
    val = "000"
    year = "XXX"

    # RE1999FIN-A-RE1-005
    if type == "RE":
        cs = ccode + "-0" + s
        year = series_years[cs]
        series = f"RE{s}"
        val = f"{int(v*100):03d}"

    # CC2019AND-A-CC2-200
    else:

        if s.endswith("a"):
            year = s[:-1]
            series = "CC2"
        elif s.endswith("tor"):
            year = "2007"
            series = "TOR"
        elif s.endswith("emu"):
            year = "2009"
            series = "EMU"
        elif s.endswith("tye"):
            year = "2012"
            series = "TYE"
        elif s.endswith("euf"):
            year = "2015"
            series = "EUF"
        else:
            year = s
            series = "CC1"

        val = "200"
    
    id = f"{type}{year}{ccode}-A-{series}-{val}"
    print(f"{name} {v} {country} {s} === {type} {id}")
    newrows.append({
        "name": name,
        "id": id,
        "date": date
    })

df = pd.DataFrame(newrows)
print(df)
df.to_csv('history.csv', index=False)
    
