import sys, csv, json, pandas as pd, datetime

from urllib.error import HTTPError, URLError

dt_format = '%Y-%m-%d'

url = 'https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv'
#url = 'owid-covid-data-03.csv'

# Output file name
fn_out = 'owid_data.js'

# Reads remote or local file
try:
    df = pd.read_csv(url)
except (HTTPError, FileNotFoundError, URLError) as e:
    exit('File "' + url + '" NOT found')

# Removes World data and N/A
df = df[df.iso_code != 'OWID_WRL'].dropna(subset=['iso_code'])

# Converts 'date' field to datetime64 type
df.date = pd.to_datetime(df.date)

# Forward fill data grouping by country
df = df.sort_values(by=['iso_code', 'date'], ascending=True).groupby('iso_code', sort=False).apply(lambda x: x.ffill())

df_last = df.drop_duplicates('iso_code', keep='last').loc[:]
df_last['total_vaccinations_vol'] = df_last.total_vaccinations_per_hundred * df_last.population


#df.info()
#df_last.info()


# Scatter plot data and country cards
scat  = round(df_last[['location', 'date', 'total_cases_per_million', 'total_deaths_per_million', 'total_vaccinations_per_hundred', 'population_density', 'diabetes_prevalence', 'aged_65_older']], 2)#.dropna()

coun = list()

for s in scat.iterrows():
    coun.append({
        'value': s[1].location,
        'data': {
            'date': s[1].date.strftime('%B %d, %Y'),
            'total_cases_per_1m': s[1].total_cases_per_million,
            'total_deaths_per_1m': s[1].total_deaths_per_million,
            'total_vaccs_per_100': s[1].total_vaccinations_per_hundred,
            'population_density': s[1].population_density
        }
    })

print(coun)

# Cumulative report
cont = df_last[df_last.total_vaccinations_vol > 0][[
                'continent', 'population', 'total_vaccinations_vol'
            ]].groupby('continent').sum()

cont['total_vaccinations_per_hundred_weighted'] = cont.total_vaccinations_vol / cont.population

#print(cont)

cont_ts = round(
    df[['continent', 'date', 'total_vaccinations']].dropna().groupby(by=['continent', 'date']).sum() / 10**6, 2
)

#print(cont_ts)

cont_ts_res = {
    'dt_format': dt_format,
    'xs': dict(),
    'cols': list()
}

for c in cont_ts.index.unique('continent'):
    a = c + ' axis-x'

    cont_ts_res['xs'][c] = a

    cont_ts_res['cols'].append([a] + cont_ts.loc[c].index.strftime(dt_format).tolist())
    cont_ts_res['cols'].append([c] + cont_ts.loc[c].total_vaccinations.values.tolist())

print(cont_ts_res)

with open(fn_out, 'w', newline='', encoding='utf-8') as f:
    f.write('/*\n')
    f.write('*  Developed by Goldsmiths MADJ student Yaroslava Kiryukhina\n')
    f.write('*  Coursework #3: Automatically generated data file by Python script\n')
    f.write('*/\n\n')

    #f.write('var scat = ' + json.dumps({
    #        'location': scat.location.to_list(),
    #        'date': scat.date.dt.strftime(dt_format).tolist(),
    #        'total_deaths_per_1m': round(scat.total_deaths_per_million, 2).to_list(),
    #        'diabetes_prevalence': scat.diabetes_prevalence.to_list(),
    #        'aged_65_older': round(scat.aged_65_older, 2).to_list(),
    #        'total_vaccinations_per_100': scat.total_vaccinations_per_hundred.to_list()
    #    }, ensure_ascii=False) + ';\n\n')

    f.write('var regions = ' + json.dumps({
            'continent': cont.index.to_list(),
            'total_vaccinations_per_100': round(cont.total_vaccinations_per_hundred_weighted, 2).to_list()
        }, ensure_ascii=False) + ';\n\n')

    f.write('var regions_ts = ' + json.dumps(cont_ts_res, ensure_ascii=False) + ';\n\n')

    f.write('var countries = ' + json.dumps(coun, ensure_ascii=False) + ';\n\n')
