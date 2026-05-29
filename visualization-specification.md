# Visuaal 1: Müraseirejaama tulemuste ja Nursipalu harjutusvälja tegevuste võrdlusgraafik #

Visuaali eesmärk on võrrelda müraseirejaama mõõdetud mürataset Nursipalu harjutusvälja planeeritud tegevustega ning hinnata, kas mürataseme muutused langevad ajaliselt kokku kõrgema müramõjuga tegevustega.

Graafik peab võimaldama kasutajal näha:
- mõõdetud mürataset ajas;
- planeeritud harjutuste mürakategooriat samal ajaperioodil;
- olukordi, kus mõõdetud müratase ületab hinnatava kriitilise taseme piiri;
- võimalikku seost harjutuste ja müratippude vahel.

<img width="1536" height="1024" alt="ChatGPT Image 29  mai 2026, 08_51_17" src="https://github.com/user-attachments/assets/96a95494-a6e4-4ee8-b046-324085bffd2a" />
Illustratiivne pilt (tegevuste juures ei pea olema kirjeldatud, et millega on tegemist, sest graafikust detailset tegevuste infot avalikult ei kuvata)

## Graafikul kasutatavad andmed ## 
Mõõdetud müratase
Graafikul kuvatakse müraseirejaama mõõdetud A-korrigeeritud müratase (LAeq).

Andmeväli:
avg_noise_db

Kuvamine:
- sinine joon
- Y-telg: müratase (dB)
- Planeeritud tegevuste mürakategooriad

Planeeritud tegevused kuvatakse graafiku taustal värviliste perioodidena.

Andmeväli:
planned_noise_level

### Värvid ### 

| Mürakategooria | Värv | HEX |
|---------------|-------|-------|
| Madal | Heleroheline | `#DFF0D8` |
| Keskmine | Hele kollane | `#FFF3CD` |
| Kõrge | Hele oranž | `#FFE5B4` |
| Väga kõrge | Hele punane | `#F8D7DA` |
| Tegevust ei toimu | Hele hall | `#E9ECEF` |

Taustavärvid peavad olema poolläbipaistvad, et müragraafik jääks nähtavaks.

Võrdluspiir
Graafikule lisatakse horisontaalne katkendjoon:
Ld = 65 dB

Kuvamine:
- tumehall katkendjoon
- kogu graafiku ulatuses

Lõppvisuaalis ei kuvata:
- LCeq
- LZeq
- tuulekiirust
- temperatuuri
- muid ilmaandmeid

Pealkiri
Müraseirejaama mõõdetud müratase ja Nursipalu harjutusvälja planeeritud mürakategooriad

### Märkus ###
Planeeritud mürakategooriaid ei kuvata joonena, sest need ei ole tegelikud mõõdetud müratasemed detsibellides. Tegemist on harjutuste põhjal hinnatud müramõju kategooriatega (madal, keskmine, kõrge, väga kõrge), mistõttu kuvatakse need taustavärvidena ning mõõdetud müratase kuvatakse eraldi joonena.

# Visuaal 2: Mõõdetud müratase tuulesuuna ja tuulekiiruse järgi #

Visuaali eesmärk on anda ülevaade sellest, milliste tuuleolude ajal registreeris müraseirejaam kõrgemaid või madalamaid müratasemeid.

Visuaal võimaldab hinnata võimalikku seost tuulesuuna, tuulekiiruse ja mõõdetud mürataseme vahel.

Kuna analüüs põhineb ühe nädala andmetel, tuleb tulemusi käsitleda indikatiivsena ning neid ei saa kasutada lõplike järelduste tegemiseks ilmastiku mõju kohta.

<img width="1536" height="1024" alt="aa8d82e1-b1e0-4466-8137-2d20008c11f1" src="https://github.com/user-attachments/assets/0e7e6e74-6452-44a8-9fa0-9b3921b5062e" />


## Graafiku tüüp ##

Heatmap (soojuskaart).

Iga lahter kujutab konkreetse tuulesuuna ja tuulekiiruse kombinatsiooni.

Lahtri värv näitab selle kombinatsiooni keskmist mõõdetud mürataset (LAeq).

## Kasutatavad andmed ## 

Müraseire andmed
Andmeväli: avg_noise_db
Kasutatakse lahtri keskmise mürataseme arvutamiseks.

Ilmaandmed
Andmeväljad:
wind_speed
wind_direction

### X-telg ### 

Tuulekiiruse vahemikud.

Tuulekiirus
0–2 m/s
2–4 m/s
4–6 m/s
6–8 m/s
> 8 m/s

### Y-telg ### 

Tuulesuund.

Suund
N
NE
E
SE
S
SW
W
NW

Tuulesuund arvutatakse kraadidest ilmakaartesse.

## Lahtri sisu ## 

Igas lahtris kuvatakse:

Keskmine LAeq (dB)
n = mõõtmiste arv

Näide:

68.4
n = 7

kus:

- 68.4 on keskmine mõõdetud müratase;
- n näitab, mitu mõõtmist selle lahtri arvutamisel kasutati.

## Värviskaala ## 

| Keskmine LAeq (dB) | Värv | HEX |
|--------------------|-------|-------|
| < 45 dB | Hele roheline | `#A8D99B` |
| 45–50 dB | Heleroheline | `#C5E1A5` |
| 50–55 dB | Hele kollane | `#F3E27A` |
| 55–60 dB | Kollakas-oranž | `#F8C96B` |
| 60–65 dB | Oranž | `#F79A3E` |
| > 65 dB | Punane | `#EF5350` |
| Vähe andmeid (n < 5) | Hele hall | `#E9ECEF` |

Kõrgem müratase peab olema visuaalselt selgelt eristatav.

### Väheste andmete kuvamine ###
Kui lahtris on vähem kui 5 mõõtmist:
n < 5
kuvatakse lahter helehallina.
Sellisel juhul ei tohi lahtri põhjal teha järeldusi.

## Pealkiri ## 
Mõõdetud müratase tuulesuuna ja tuulekiiruse järgi

## Tõlgendamine ## 

Visuaal aitab vastata järgmistele küsimustele:
- Milliste tuulesuundade korral registreeriti kõrgem müratase?
- Kas suurema tuulekiiruse korral esineb kõrgemaid müratasemeid?
- Kas kõrgemad müratasemed koonduvad kindlatesse tuuleoludesse?

Visuaal ei tõesta põhjuslikku seost tuule ja mürataseme vahel, vaid näitab mõõdetud mürataseme ja ilmastikutingimuste samaaegset esinemist analüüsiperioodi jooksul.
