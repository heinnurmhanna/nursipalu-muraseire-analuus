# NURSIPALU MÜRASEIRE, HARJUTUSGRAAFIKU JA ILMASTIKUANDMETE KÕRVUTAMINE
Andmetöövoog Nursipalu harjutusvälja graafiku, müraseire ja ilmastikuandmete kõrvutamiseks.

# SPRINT 1 

# TO-DO #
Hanna: 
1. Uurida müraseirejaama andmete allika asukohta
2. Teha githubis täiendused

Roland: 
1. Moodlesse esitada küsimus kasutatava tarkvara kohta
2. Anda esialgsed suunised tiimile andmete kogumise kohta

Raili: 
1. Luua andmeskeem

Aldo ja Hanna: 
1. Toetada Rolandit ning vaadata, kas tehnilisi katsetusi

## Projekti kirjeldus

Projekti eesmärk on luua otsast-lõpuni andmetöövoog, mis kogub ja ühendab Nursipalu müraseirejaama mõõtmised, Kaitseväe harjutusvälja graafiku ning ilmastikuandmed. Andmete põhjal luuakse näidikulaud, mille abil saab hinnata, kas harjutusvälja planeeritud tegevused ja ilmastikutingimused langevad kokku mõõdetud mürataseme muutustega.

Projekti tulemusena valmib andmetöövoog, mis:

- kogub andmeid avalikest ja ajas muutuvatest andmeallikatest;
- puhastab ja teisendab andmed analüüsiks sobivale kujule;
- ühendab müraseire, harjutusgraafiku ja ilmastikuandmed ühise ajatelje alusel;
- kontrollib andmete kvaliteeti;
- kuvab tulemused näidikulaual;
- aitab teha järelduse, kas selline andmete kõrvutamine on tulemuslik.

Projekt ei eelda, et andmete vahel leitakse kindel põhjuslik seos. Peamine eesmärk on hinnata, kas erinevate avalike andmeallikate ajapõhine kõrvutamine annab tõlgendatavaid ja kasulikke tulemusi.

## Äriküsimus

Kas Nursipalu harjutusvälja graafikus planeeritud tegevused ja samaaegsed ilmastikutingimused on seotud müraseirejaamas mõõdetud mürataseme tõusudega?

Näidikulaud aitab vastata näiteks järgmistele küsimustele:
- Kui palju kõrgem on keskmine müratase perioodidel, kus harjutusväljal toimub planeeritud tegevus?
- Kui sageli langevad mürataseme tipud ajaliselt kokku harjutusgraafikus märgitud tegevustega?
- Kas teatud ilmastikutingimused (näiteks tugev tuul või kindel tuulesuund) mõjutavad mõõdetud mürataset?

Võimalikud KPI-d või mõõdikud näidikulaual:
- keskmine müratase tegevusega vs tegevuseta perioodil;
- mürataseme tõusude arv nädalas või päevas;
- planeeritud harjutuste ja müratippude ajalise kattuvuse protsent.

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

## Arhidektuuriskeem 

Joonistage arhitektuuriskeem. Allikast lõpptulemini. Sobib Mermaid, draw.io, Excalidraw või käsitsi joonis + foto.

## Tööülesanded

Hanna Heinnurm - projektijuht (teema algataja)
Roland Pajuleht - transformatsioonide omanik (andmebaaside ülesseadmine, andmete projektijuht) 
Raili Jäe - näidikulaua omanik
Aldo Rääbis - kvaliteedi omanik 

## Projekti riskid ja piirangud

### Projekti riskid
| Risk | Mõju | Maandus |
|---|---|---|
| Müraseire andmetele ligipääs on keeruline | Andmete sissevõtt võib venida | Kontrollida ligipääsu esimesel nädalal |
| Andmeallikate ajagranulaarsus on erinev | Andmeid on keeruline võrrelda | Viia kõik andmed tunnipõhiseks |
| Ajavööndid ei ühti | Võrdlus võib anda valesid tulemusi | Kasutada ühtset ajavööndit |
| Harjutusgraafik kirjeldab planeeritud, mitte tegelikku tegevust | Seose tõlgendamine on piiratud | Kirjeldada see projekti piiranguna |
| Ilmastikuandmed ei pärine täpselt samast asukohast | Tulemused võivad olla ligikaudsed | Dokumenteerida ilmaandmete allikas ja koordinaadid |
| Selget seost ei ilmne | Tulemus võib tunduda nõrk | Rõhutada, et eesmärk on hinnata kõrvutamise tulemuslikkust |

### Projekti piirangud
- Harjutusvälja graafik näitab planeeritud tegevusi, mitte tingimata tegelikult toimunud tegevusi.
- Müraseirejaam võib mõõta ka muid heliallikaid peale harjutusvälja tegevuse.
- Ilmastikuandmed võivad pärineda lähimast mõõtepunktist või mudelandmetest.
- Andmete kõrvutamisel ei pruugi ilmneda selget seost.
- Projekt ei tõesta põhjuslikku seost, vaid loob andmetöövoo ja hindab ajapõhise kõrvutamise kasulikkust.

### Tehnilised katsetused 
Tehke esimesed tehnilised katsetused. Kas API vastab? Kas saate andmebaasiga ühenduda? Kas valitud tööriistad jooksevad?

#### Andmeallikate kontroll

Kontrollida, kas müraseire avaandmetele saab programmiliselt ligi.
- Kontrollida, kas Kaitseväe harjutusgraafiku JSON on koodiga loetav.
- Valida sobiv ilmaandmete allikas.
- Kontrollida, millised väljad on igas andmeallikas olemas.
- Dokumenteerida andmeallikate struktuur.
- Tuvastada võimalikud probleemid, näiteks puuduvad väärtused, erinevad ajavööndid ja erinev ajagranulaarsus.

## Töö etapid 

Siia vist võiksime juurde kirjutada ka samm sammulised mõtted, et milline projekt on

1. Määratleda äriküsimus. Sõnastada, mida soovitakse teada saada (kas harjutused ja ilm mõjutavad mürataset).
2. Kaardistada andmeallikad. Leida müraseire, harjutusgraafiku ja ilmastiku andmeallikad ning kontrollida ligipääsu.
3. Luua projekti struktuur. Teha GitHubi repo, kaustad, README ja vajalikud konfiguratsioonifailid.
4. Koguda andmed automaatselt. Luua skriptid, mis laadivad regulaarselt alla müra-, ilma- ja harjutusgraafiku andmed.
5. Salvestada toorandmed. Hoida algandmed failides või andmebaasis, et neid saaks hiljem uuesti kasutada.
6. Puhastada ja teisendada andmed. Ühtlustada ajatemplid, eemaldada vigased väärtused ja viia kõik andmed samale ajatasemele (nt tunnipõhiseks).
7. Ühendada andmed üheks tabeliks. Siduda müraseire, harjutusgraafiku ja ilmastikuandmed ühise ajajoone alusel.
8. Kontrollida andmekvaliteeti. Teha testid puuduvate väärtuste, duplikaatide ja ebareaalsete mõõtmiste leidmiseks.
9. Luua dashboard / näidikulaud. Kuvada graafikud ja KPI-d, mis aitavad võrrelda mürataset, harjutusi ja ilmastikku.
10. Analüüsida tulemusi. Vaadata, kas harjutuste ja mürataseme vahel ilmneb ajaline seos ning kuidas ilm võib tulemusi mõjutada.
11. Dokumenteerida projekt. Kirjeldada arhitektuur, töövoog, testid, piirangud ja käivitamise juhend.
12. Esitleda lõpptulemust. Salvestada demo/video ja näidata kogu andmetöövoogu allikast dashboardini.
