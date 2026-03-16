# MalLog
## 1. Poslovni problem

### Opredelitev problema

Skrbniki strežnikov in razvijalci se pogosto srečujejo z velikimi količinami strežniških logov, iz katerih je težko hitro razbrati, ali se dogaja kaj sumljivega. Med tipičnimi problemi so:

- preveliko število neuspelih prijav,
- nenavadno veliko število zahtevkov iz istega IP naslova,
- dostopi do občutljivih endpointov (npr. `/admin`, `/login`, `/config`),
- nenavadni vzorci obnašanja v kratkem časovnem obdobju,
- težko ročno pregledovanje velikih `.log` datotek.

Ročna analiza logov je počasna, nepregledna in podvržena napakam, zato je smiselno imeti sistem, ki loge sprejme, obdela in izpostavi potencialne anomalije.

### Namen sistema

Sistem **MalLog** omogoča uporabnikom:

- prijavo v spletno aplikacijo,
- nalaganje strežniških log datotek,
- pregled strukturiranih log zapisov,
- samodejno zaznavanje sumljivih vzorcev,
- pregled opozoril in poročil o morebitnih varnostnih incidentih.

Glavni cilj sistema je poenostaviti odkrivanje nenavadne aktivnosti v strežniških logih z uporabo mikrostoritvene arhitekture.

### Uporabniki sistema

- **Administrator / varnostni analitik**
  - nalaga log datoteke,
  - pregleduje zaznane anomalije,
  - analizira opozorila in sumljive IP-je.

### Komunikacija komponent

Sistem je sestavljen iz več neodvisnih mikrostoritev, ki:

- komunicirajo prek **REST API**,
- imajo jasno ločene odgovornosti,
- lahko uporabljajo ločene podatkovne baze,
- skupaj tvorijo enoten sistem za pregled in analizo logov.

---

## 2. Glavne domene in mikrostoritve

Sistem je razdeljen na tri glavne poslovne domene.

### 1. Authentication Service – Domena: avtentikacija in uporabniki

#### Odgovornosti:
- registracija uporabnika,
- prijava uporabnika,
- upravljanje JWT žetonov,
- osnovni podatki o uporabniku.

Ta storitev skrbi za identiteto uporabnika in nadzor dostopa do sistema.

---

### 2. Log Ingestion Service – Domena: sprejem in obdelava logov

#### Odgovornosti:
- nalaganje `.log` datotek,
- razčlenjevanje log zapisov,
- normalizacija logov v strukturirano obliko,
- shranjevanje log zapisov,
- filtriranje po IP, status kodi, časovnem žigu ali endpointu.

Ta storitev je vir resnice za vse naložene in obdelane log podatke.

---

### 3. Anomaly Detection Service – Domena: analiza in zaznavanje anomalij

#### Odgovornosti:
- analiza strukturiranih logov,
- zaznavanje sumljivih vzorcev,
- generiranje opozoril,
- razvrščanje anomalij po stopnji tveganja,
- priprava poročil za uporabniški vmesnik.

Primeri anomalij:
- preveč neuspelih prijav v kratkem času,
- preveč zahtev iz istega IP naslova,
- dostopi do občutljivih endpointov,
- nenavadni časovni vzorci dostopa,
- nenaden porast napak tipa 4xx ali 5xx.

Ta storitev predstavlja jedro varnostne analize sistema.

---

## 3. Arhitektura sistema

Sistem sledi mikrostoritveni arhitekturi z jasno ločenimi domenami in odgovornostmi.

### Komunikacija

- **Web aplikacija → mikrostoritve:** REST API
- **Mikrostoritve med seboj:** REST API
- **Avtentikacija uporabnika:** JWT

### Podatkovna ločitev

Vsaka mikrostoritev lahko uporablja svojo lastno podatkovno bazo:

- **Authentication Service** → AuthDB
- **Log Ingestion Service** → LogsDB
- **Anomaly Detection Service** → AlertsDB

Ni deljene baze podatkov, kar omogoča:

- ohlapno sklopljenost,
- jasne meje odgovornosti,
- lažje vzdrževanje,
- možnost neodvisnega razvoja posameznih storitev.

### Diagram arhitekture

![architecture.png](/docs/architecture.png)
## 4. Struktura repozitorija
Repozitorij je organiziran po poslovnih domenah, podobno kot v screaming architecture pristopu, kakršen je uporabljen tudi v referenčnem repozitoriju.
```
MalLog/
│
├── auth-service/
│   ├── app/
│   ├── routes/
│   ├── models/
│   ├── services/
│   ├── utils/
    ├── tests/
        └── test_auth_api.py
│   └── run.py
│
├── log-ingestion-service/
│   ├── app/
│   ├── routes/
│   ├── models/
│   ├── parsers/
│   ├── services/
│   └── run.py
│
├── anomaly-detection-service/
│   ├── app/
│   ├── routes/
│   ├── models/
│   ├── detectors/
│   ├── services/
│   └── run.py
│
├── mal-log-web/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── public/
│
├── docs/
│   └── architecture-diagram.png
│
├── compose.yml
└── README.md
```

### Načela organizacije

- Vsaka storitev ima svojo jasno odgovornost.
- Poslovna logika je ločena od transportnega sloja.
- Frontend je ločen od backend mikrostoritev.
- Struktura repozitorija odraža poslovne domene sistema.

## 5. Komunikacija med storitvami

### REST API (sinhrona komunikacija)
**Authentication Service**
- POST /register
- POST /login
- GET /me

**Log Ingestion Service**
- POST /logs/upload
- GET /logs
- GET /logs/:id
- GET /logs/filter

**Anomaly Detection Service**
- POST /analyze/:uploadId
- GET /alerts
- GET /alerts/:id
- GET /reports/summary

### Arhitekturna načela

**Sistem sledi načelom**:
- mikrostoritvena arhitektura,
- ločene odgovornosti,
- REST komunikacija,
- ločene podatkovne baze,
- modularnost in razširljivost,
- enostavna možnost nadgradnje z naprednejšo detekcijo anomalij.

## 6. Povzetek
**MalLog** je mikrostoritveni sistem za nalaganje, pregled in analizo strežniških logov.
Omogoča:
- varno prijavo uporabnikov,
- nalaganje in strukturiranje log zapisov,
- zaznavanje sumljive aktivnosti,
- pregled opozoril in poročil v spletni aplikaciji.

Arhitektura sistema zagotavlja modularnost, jasno ločitev odgovornosti in dobro osnovo za nadaljnjo nadgradnjo, na primer z naprednejšimi metodami za detekcijo anomalij.