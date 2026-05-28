# Edenemisraport

## Mis on valmis

- [x] Docker Compose käivitab kõik teenused
- [x] Andmeid saadakse allikast kätte
- [x] Andmed laetakse `staging` / raw kihti
- [x] Vähemalt üks transformatsioon toimib
- [x] Vähemalt üks näidikulaud on nähtaval
- [ ] Vähemalt üks andmekvaliteedi test läbib

Valmis on minimaalne otsast-otsani andmevoog: andmed loetakse allikatest sisse, salvestatakse raw/staging kihti, transformeeritakse DuckDB `merged` vaatesse ning kuvatakse Dash näidikulaual.

## Järgmised sammud

- Täpsustada lõplikud KPI-d ja graafikud.
- Koguda pikema perioodi kohta andmeid (praegu saab 1 päeva andmed korraga).
- Lisada ja dokumenteerida andmekvaliteedi testid.


## Mis takistab

- Hetkel pole blokeerivaid probleeme.


## Kontrollpunkt

Käsk, millega saab kontrollida, et töövoog töötab:

```bash
docker compose up --build
