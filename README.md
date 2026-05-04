# NURSIPALU MÜRASEIRE, HARJUTUSGRAAFIKU JA ILMASTIKUANDMETE KÕRVUTAMINE
Andmetöövoog Nursipalu harjutusvälja graafiku, müraseire ja ilmastikuandmete kõrvutamiseks.

## Projekti kirjeldus

Projekti eesmärk on luua otsast-lõpuni andmetöövoog, mis kogub ja ühendab Nursipalu müraseirejaama mõõtmised, Kaitseväe harjutusvälja graafiku ning ilmastikuandmed. Andmete põhjal luuakse näidikulaud, mille abil saab hinnata, kas harjutusvälja planeeritud tegevused ja ilmastikutingimused langevad kokku mõõdetud mürataseme muutustega.

Projekt ei eelda, et andmete vahel leitakse kindel põhjuslik seos. Peamine eesmärk on hinnata, kas erinevate avalike andmeallikate ajapõhine kõrvutamine annab tõlgendatavaid ja kasulikke tulemusi.

## Äriküsimus

Kas Nursipalu harjutusvälja graafikus planeeritud tegevused ja samaaegsed ilmastikutingimused on seotud müraseirejaamas mõõdetud mürataseme tõusudega?

## Projekti eesmärk

Projekti tulemusena valmib andmetöövoog, mis:

- kogub andmeid avalikest ja ajas muutuvatest andmeallikatest;
- puhastab ja teisendab andmed analüüsiks sobivale kujule;
- ühendab müraseire, harjutusgraafiku ja ilmastikuandmed ühise ajatelje alusel;
- kontrollib andmete kvaliteeti;
- kuvab tulemused näidikulaual;
- aitab teha järelduse, kas selline andmete kõrvutamine on tulemuslik.

## Andmeallikad

| Andmeallikas | Kirjeldus | Muutuvus ajas |
|---|---|---|
| Nursipalu müraseire avaandmed | Müraseirejaama mõõtmistulemused | Uuenevad ajas |
| Kaitseväe harjutusvälja graafik | Planeeritud tegevused ja mürataseme kategooriad | Uuenev JSON-fail |
| Ilmastikuandmed | Tuul, õhurõhk, pilvisus, sademed jm ilmastikunäitajad | Päringu alusel ajas muutuvad |

Kasutatavad andmeallikad:

- Nursipalu müraseire avaandmed: https://noise.ellegroup.eu/public/1
- Kaitseväe harjutusvälja graafiku JSON: https://mil.ee/wp-content/uploads/training-grounds/training_ground_schedule.json
- Ilmastikuandmed: näiteks Open-Meteo või muu avalik ilmaandmete allikas

## Peamised mõõdikud

Projektis analüüsitakse näiteks järgmisi mõõdikuid:

- keskmine müratase planeeritud tegevusega perioodidel;
- keskmine müratase tegevuseta perioodidel;
- mürataseme tõusu juhtumite arv;
- planeeritud harjutuste ja mõõdetud mürataseme tõusude ajaline kattuvus;
- ilmastikutingimuste võimalik seos mürataseme muutustega.

## Tööetapid

### 1. Projekti ettevalmistus

- Luua GitHubi repositoorium.
- Lisada `README.md`.
- Lisada `.gitignore`.
- Lisada `.env.example`.
- Luua projekti kaustastruktuur.
- Kirjeldada esmane äriküsimus.
- Kirjeldada andmeallikad ja nende muutuvus ajas.

Soovituslik kaustastruktuur:

```text
nursipalu-noise-analysis/
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
├── docs/
│   ├── arhitektuur.md
│   ├── progress.md
│   └── projektiplaan.md
├── src/
│   ├── ingest/
│   ├── transform/
│   ├── quality/
│   └── dashboard/
├── data/
│   └── .gitkeep
└── tests/
```

### 2. Andmeallikate kontroll
Kontrollida, kas müraseire avaandmetele saab programmiliselt ligi.
Kontrollida, kas Kaitseväe harjutusgraafiku JSON on koodiga loetav.
Valida sobiv ilmaandmete allikas.
Kontrollida, millised väljad on igas andmeallikas olemas.
Dokumenteerida andmeallikate struktuur.
Tuvastada võimalikud probleemid, näiteks puuduvad väärtused, erinevad ajavööndid ja erinev ajagranulaarsus.

### 3. Andmete sissevõtt
Luua skript müraseire andmete allalaadimiseks.
Luua skript harjutusgraafiku JSON-i allalaadimiseks.
Luua skript ilmaandmete pärimiseks.
Salvestada toorandmed lokaalselt või andmebaasi.
Tagada, et andmete sissevõtt on korratav ja automatiseeritav.
Lisada konfiguratsioon .env faili kaudu.

Võimalikud failid:
```src/ingest/ingest_noise.py
src/ingest/ingest_schedule.py
src/ingest/ingest_weather.py
```

### 4. Andmete transformatsioon
Puhastada müraseire andmed.
Teisendada harjutusgraafiku andmed ajavahemikeks.
Puhastada ja ühtlustada ilmaandmed.
Teisendada kõik ajad samasse ajavööndisse.
Viia andmed ühisele ajatasemele, näiteks tunnipõhiseks.
Ühendada müra-, graafiku- ja ilmaandmed üheks analüüsitabeliks.

Lõplik analüüsitabel võiks sisaldada näiteks järgmisi välju:

```timestamp
station_id
avg_noise_db
max_noise_db
scheduled_activity
planned_noise_level
wind_speed
wind_direction
pressure
cloud_cover
precipitation
```

### 5. Andmekvaliteedi kontroll

Projektis lisatakse vähemalt kolm andmekvaliteedi testi.

Võimalikud testid:

| Test | Kirjeldus |
|---|---|
| `not_null_timestamp` | Ajatempel peab olema olemas |
| `unique_station_timestamp` | Ühe jaama kohta ei tohi samal tunnil olla mitu rida |
| `noise_value_range` | Müratase peab jääma realistlikku vahemikku |
| `schedule_start_before_end` | Harjutuse algusaeg peab olema enne lõpuaega |
| `weather_value_range` | Ilmaandmed peavad jääma mõistlikesse piiridesse |

### 6. Näidikulaua loomine

Dashboard peaks vastama äriküsimusele ja sisaldama vähemalt kahte KPI-d või visuaali.

Võimalikud dashboard’i vaated:

müratase ajas;
harjutusgraafiku tegevused ajas;
keskmine müratase tegevusega ja tegevuseta perioodidel;
mürataseme ja tuulekiiruse võrdlus;
mürataseme ja tuulesuuna võrdlus;
mürataseme ja õhurõhu, pilvisuse või sademete võrdlus.

### 7. Dokumentatsioon

README või eraldi dokumentatsioon peaks sisaldama:

projekti kirjeldust;
äriküsimust;
andmeallikate kirjeldust;
arhitektuuri;
käivitamise juhendit;
andmekvaliteedi testide kirjeldust;
dashboard’i kirjeldust;
tulemusi ja järeldusi;
projekti piiranguid;
tööjaotust.

### 8. Video ja lõplik esitamine

Lõpus salvestatakse kuni 10-minutiline video, kus näidatakse:

projekti eesmärki;
andmeallikaid;
andmetöövoogu;
GitHubi repo struktuuri;
andmete transformatsioone;
andmekvaliteedi teste;
dashboard’i;
peamisi tulemusi ja piiranguid.

## Ajakava

### Nädal 1: Planeerimine ja arhitektuur
Periood: 18.05–24.05

Eesmärk on saada paika projekti mõte, andmeallikad ja arhitektuur.

Tulemused:

GitHubi repo loodud.
docs/arhitektuur.md lisatud.
Äriküsimus sõnastatud.
Andmeallikad kirjeldatud.
Esmane arhitektuuriskeem tehtud.
Rollid ja tööjaotus kokku lepitud.
Peamised riskid kirja pandud.

### Nädal 2: Esimene töötav andmevoog

Periood: 25.05–31.05

Eesmärk on ehitada minimaalne töötav lahendus ühest andmeallikast visuaalini.

Tulemused:

Vähemalt üks andmeallikas programmiliselt sisse loetud.
Vähemalt üks transformatsioon tehtud.
Vähemalt üks lihtne visuaal loodud.
docs/progress.md täidetud.
Tehnilised takistused dokumenteeritud.

### Nädal 3: Lõplik lahendus

Periood: 01.06–07.06

Eesmärk on lisada kõik andmeallikad, kvaliteeditestid, dashboard ja lõplik dokumentatsioon.

Tulemused:

Kõik põhiandmeallikad sisse loetud.
Andmed ühendatud analüüsitabeliks.
Vähemalt kolm andmekvaliteedi testi loodud.
Dashboard valmis.
README valmis.
Video salvestatud.
Repo ja video Moodle’isse esitatud.
Võimalikud GitHubi ülesanded
Andmeallikad
 Uurida müraseire avaandmete struktuuri.
 Uurida Kaitseväe graafiku JSON-i struktuuri.
 Valida ilmaandmete allikas.
 Kirjeldada kõik kasutatavad väljad.
Andmete sissevõtt
 Luua müraseire andmete sissevõtu skript.
 Luua harjutusgraafiku sissevõtu skript.
 Luua ilmaandmete sissevõtu skript.
 Lisada .env.example.
Transformatsioonid
 Ühtlustada ajatemplid.
 Agregeerida müraseire andmed tunnipõhiseks.
 Teisendada harjutusgraafik ajavahemikeks.
 Ühendada müra-, graafiku- ja ilmaandmed.
Andmekvaliteet
 Lisada ajatemplite not null kontroll.
 Lisada duplikaatide kontroll.
 Lisada mürataseme väärtuste vahemiku kontroll.
 Lisada graafiku algus- ja lõpuaja kontroll.
 Lisada ilmaandmete väärtuste vahemiku kontroll.
Dashboard
 Luua mürataseme ajajoone visuaal.
 Lisada harjutusgraafiku tegevused visuaalile.
 Lisada tegevusega ja tegevuseta perioodide võrdlus.
 Lisada ilmastikutingimuste vaade.
 Lisada filtrid.
Dokumentatsioon
 Kirjutada README.
 Kirjutada arhitektuuridokument.
 Kirjutada progressidokument.
 Kirjeldada projekti piirangud.
 Lisada käivitamise juhend.

## Projekti riskid
| Risk | Mõju | Maandus |
|---|---|---|
| Müraseire andmetele ligipääs on keeruline | Andmete sissevõtt võib venida | Kontrollida ligipääsu esimesel nädalal |
| Andmeallikate ajagranulaarsus on erinev | Andmeid on keeruline võrrelda | Viia kõik andmed tunnipõhiseks |
| Ajavööndid ei ühti | Võrdlus võib anda valesid tulemusi | Kasutada ühtset ajavööndit |
| Harjutusgraafik kirjeldab planeeritud, mitte tegelikku tegevust | Seose tõlgendamine on piiratud | Kirjeldada see projekti piiranguna |
| Ilmastikuandmed ei pärine täpselt samast asukohast | Tulemused võivad olla ligikaudsed | Dokumenteerida ilmaandmete allikas ja koordinaadid |
| Selget seost ei ilmne | Tulemus võib tunduda nõrk | Rõhutada, et eesmärk on hinnata kõrvutamise tulemuslikkust |


## Projekti piirangud
Harjutusvälja graafik näitab planeeritud tegevusi, mitte tingimata tegelikult toimunud tegevusi.
Müraseirejaam võib mõõta ka muid heliallikaid peale harjutusvälja tegevuse.
Ilmastikuandmed võivad pärineda lähimast mõõtepunktist või mudelandmetest.
Andmete kõrvutamisel ei pruugi ilmneda selget seost.
Projekt ei tõesta põhjuslikku seost, vaid loob andmetöövoo ja hindab ajapõhise kõrvutamise kasulikkust.

## Edukriteeriumid

Projekt loetakse õnnestunuks, kui:
vähemalt üks põhiandmevoog tuleb ajas muutuvast andmeallikast;
andmete sissevõtt on automatiseeritud;
olemas on vähemalt üks transformatsioonisamm;
olemas on vähemalt kolm andmekvaliteedi testi;
loodud on dashboard vähemalt kahe KPI või visuaaliga;
README kirjeldab projekti eesmärki, arhitektuuri ja käivitamist;
andmete põhjal on tehtud järeldus, kas selline kõrvutamine annab kasulikku infot.
