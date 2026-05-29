# Visuaal 1: Müraseirejaama tulemuste ja Nursipalu harjutusvälja tegevuste võrdlusgraafik #

Visuaali eesmärk on võrrelda müraseirejaama mõõdetud mürataset Nursipalu harjutusvälja planeeritud tegevustega ning hinnata, kas mürataseme muutused langevad ajaliselt kokku kõrgema müramõjuga tegevustega.

Graafik peab võimaldama kasutajal näha:
- mõõdetud mürataset ajas;
- planeeritud harjutuste mürakategooriat samal ajaperioodil;
- olukordi, kus mõõdetud müratase ületab hinnatava kriitilise taseme piiri;
- võimalikku seost harjutuste ja müratippude vahel.

<img width="1536" height="1024" alt="ChatGPT Image 29  mai 2026, 08_51_17" src="https://github.com/user-attachments/assets/96a95494-a6e4-4ee8-b046-324085bffd2a" />
Illustratiivne pilt

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
