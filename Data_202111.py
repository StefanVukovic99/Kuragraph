import json
from helpers import toRGBfloat, opacifyRGBint

bashoYYYYmm = '202111'

bashoName = "Kyushu 2021"

kinboshi = [];

sansho = {
    'Ura':'技',
    'Abi': '敢',
    'Takanosho': '敢'
}

with open(f'{bashoYYYYmm}.json') as f:
    rikishi = json.load(f)
    
DAYS = len(rikishi['Hoshoryu']['record'])

print(rikishi['Hoshoryu']['record'])

kadoban = (1, 0.9, 0.5, 1)
noChange = (0.93,0.92,0.88,1)
placeholder = (0.93,0.92,0.88)
black = (0,0,0)

mawashiColors = {
        'Abi': black,
        'Akua': toRGBfloat((173,195,185)),
        'Aoiyama':  (0.17, 0.40, 0.19),
        'Asanoyama': opacifyRGBint((134,92,129)),
        'Chiyomaru': (0.16, 0.85, 0.06),
        'Chiyonokuni': toRGBfloat((7,24,34)),
        'Chiyoshoma': (0.01,0.24,0.04),
        'Chiyotairyu': (0.14, 0.36, 0.10),
        'Daieisho':(0.6,0.03,0.24),
        'Endo': (0.36,0.01,0.47),
        'Hidenoumi': (0.42, 0.25, 0),
        'Hokutofuji': opacifyRGBint((97,97,101)),
        'Hoshoryu':  (0.03,0.61,0.83),
        'Ichinojo': (0.06,0.22,0.77),
        'Ichiyamamoto':black,
        'Ishiura': (0.86, 0.77, 0.16),
        'Kagayaki': (0.61, 0.43, 0.05),
        'Kaisei': (1,0.6,0),
        'Kiribayama': black,
        'Kotoeko':   (0.78, 0.60, 0.77),
        'Kotokuzan': (0.51, 0.4, 0.2),
        'Kotonowaka': (0.30, 0.96, 0.90),
        'Kotoshoho': toRGBfloat((59,94,121)),
        'Meisei': toRGBfloat((8,25,71)),
        'Mitakeumi': (0.52, 0.1, 0.43),
        'Myogiryu': black,
        'Nishikigi': (0.14, 0.32, 0.17),
        'Oho': (0.42, 0.33, 0.04),
        'Okinoumi': toRGBfloat((19,29,13)),
        'Onosho': toRGBfloat((92,0,20)),
        'Takakeisho': opacifyRGBint((97,97,101)),
        'Takanosho':  toRGBfloat((88,0,27)),
        'Takarafuji':(0.12, 0.02, 0.48),
        'Takayasu': toRGBfloat((57,0,10)),
        'Tamawashi': toRGBfloat((13,33,51)),
        'Terunofuji': (0.33, 0.06, 0.48),
        'Terutsuyoshi': black,
        'Tochinoshin': (0.43, 0, 0.68),
        'Tsurugisho': (0, 0, 0),
        'Sadanoumi': (0.10, 0.36, 0.06),
        'Shimanoumi': (1,0.6,0),
        'Shodai': (0,0,0.15),
        'Shohozan': black,
        'Tobizaru':(0.40, 0.54, 0.66),
        'Ura': (1, 0.55, 0.79),
        'Wakamotoharu':  black,
        'Wakatakakage': (0.06,0.22,0.77),
        'Yutakayama': (0.04, 0.30, 0.09),        
};
    
for (shikona, info) in rikishi.items():
    rikishi[shikona]['color'] = mawashiColors[shikona]
    
