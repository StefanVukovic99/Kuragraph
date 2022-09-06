import requests
import re 
from sys import exit
import json


try: 
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup
    
bashoYYYYMM = '202207'

resp = requests.get(f'http://sumodb.sumogames.de/Results.aspx?b={bashoYYYYMM}&d=15')
print("got response", resp.status_code)
if(resp.status_code == 404): exit()

parsed_html = BeautifulSoup(resp.content)
recordGroups = [node.text for node in parsed_html.body.select('font') if any(H in node.text for H in ['○', '●', '■', '–', '□'])]

records = []
for group in recordGroups:
    for record in re.findall( r'[○●■□–]+ \w+ \w+', group):
        lowerDivs = ('J', 'Ms', 'Sd')
        if not record.split()[1].startswith(lowerDivs):
            records.append(record)
    
print(records)
print(len(records))

rikishi = {}

for record in records:
    
    hoshi = record.split()[0]
    banzuke1 = record.split()[1]
    shikona = record.split()[2]
    
    scores = [1 if score in ['○', '□'] else -1 for score in hoshi]
    kyujo = [i for (i,score) in enumerate(hoshi) if score in ['■', '–'] ]
    
    rikishi[shikona] = {
        'record': scores,
        'banzuke1': banzuke1,
        'kyujo': kyujo
        }

print(rikishi)

with open(f'{bashoYYYYMM}.json', 'w', encoding='utf-8') as f:
    json.dump(rikishi, f, ensure_ascii=False, indent=4)