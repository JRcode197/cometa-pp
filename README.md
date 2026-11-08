# Cometa Crescita → Portfolio Performance

Feed **gratuito e pubblico** delle quotazioni mensili del comparto **Crescita del Fondo Cometa**, recuperate dal [sito ufficiale Cometa](https://www.cometafondo.it/andamenti/crescita/) e convertite in JSON per [Portfolio Performance](https://www.portfolio-performance.info/).

[![Aggiornamento delle quote](https://github.com/JRcode197/cometa-pp/actions/workflows/update.yml/badge.svg)](https://github.com/JRcode197/cometa-pp/actions/workflows/update.yml)
[![Test](https://github.com/JRcode197/cometa-pp/actions/workflows/tests.yml/badge.svg)](https://github.com/JRcode197/cometa-pp/actions/workflows/tests.yml)

> **Non ufficiale.** Progetto indipendente, non affiliato a Fondo Cometa né a Portfolio Performance. I dati pubblicati sono valori quota pubblici, **non** quote detenute, versamenti, rendimenti personali o dati dell'area riservata. Verifica i valori importanti con la fonte originale.

## 🚀 Utilizzo immediato in Portfolio Performance

**Feed JSON:** https://JRcode197.github.io/cometa-pp/cometa-crescita.json

**Pagina informativa:** https://JRcode197.github.io/cometa-pp/

**Stato e data di aggiornamento:** https://JRcode197.github.io/cometa-pp/status.json

> I link Pages funzionano solo **dopo il primo deploy riuscito**. Se ottieni un errore 404, consulta [Attivazione iniziale](#attivazione-iniziale-del-sito-pages).

1. In Portfolio Performance crea un **titolo vuoto** (ad es. *Fondo Cometa – Crescita*), imposta valuta **EUR** e lascia l'ISIN vuoto: il comparto pensionistico non è un ETF negoziato con ISIN.
2. Apri la configurazione delle **quotazioni storiche** del titolo e scegli **JSON** come fornitore.
3. Inserisci le impostazioni seguenti e prova **Anteprima / Preview** prima di salvare.

| Impostazione | Valore |
| --- | --- |
| URL quotazioni storiche | `https://JRcode197.github.io/cometa-pp/cometa-crescita.json` |
| JSONPath data | `$[*].date` |
| JSONPath prezzo / Close | `$[*].close` |
| Formato data, se richiesto | `yyyy-MM-dd` |
| Valuta | EUR |

Il JSON è un array ordinato dal mese più vecchio al più recente:

```json
[
  {"date": "2005-04-30", "close": 11.965},
  {"date": "2005-05-31", "close": 12.001}
]
```

**Nota:** il secondo valore è *solo un esempio illustrativo*, non una quotazione storica verificata. Le date sono l'ultimo giorno **di calendario** del mese di riferimento, non necessariamente il giorno lavorativo in cui Cometa ha determinato la quota. Non sono disponibili prezzi inframensili o in tempo reale.

### Valore della tua posizione

Per calcolare il valore della posizione previdenziale, inserisci separatamente in Portfolio Performance le **quote effettivamente assegnate** da Cometa. Questo progetto fornisce *solo* il prezzo unitario; **non** recupera TFR, contribuzioni del datore di lavoro, costi, quote detenute né movimenti dell'area riservata. Non usare il semplice totale dei versamenti come quantità di quote.

## Fonte, aggiornamento e file disponibili

- **Fonte:** https://www.cometafondo.it/andamenti/crescita/ — tabella storica `DATA / QUOTA`.
- **Frequenza dei dati:** mensile, secondo le pubblicazioni del fondo.
- **Tentativo automatico di aggiornamento:** ogni **mercoledì alle 07:21 UTC**, tramite GitHub Actions; gli orari di GitHub non sono garantiti.
- **Riesecuzione manuale:** [Actions → Cometa Crescita - aggiorna e pubblica le quote](https://github.com/JRcode197/cometa-pp/actions/workflows/update.yml) → **Run workflow**.
- **JSON per Portfolio Performance:** `/cometa-crescita.json`
- **CSV storico:** `/cometa-crescita.csv` (separatore `;`, decimali `,`).
- **Metadati:** `/status.json` (`generated_at_utc`, `last_quote_date`, `last_quote_eur`, `number_of_months`, fonte).

Il workflow esegue **test → download → validazione → creazione feed → pubblicazione su GitHub Pages**. Se l'importazione o un controllo fallisce, il deployment non procede. La precedente versione eventualmente pubblicata *potrebbe restare online*; controlla la data nel file `status.json` e lo stato dell'ultimo workflow.

## Attivazione iniziale del sito Pages

Questo repository è **pubblico**; è quindi idoneo a GitHub Pages con il piano GitHub Free.

1. Il proprietario apre [Settings → Pages](https://github.com/JRcode197/cometa-pp/settings/pages).
2. Nella sezione **Build and deployment**, imposta **Source: GitHub Actions**. Non serve creare un workflow GitHub suggerito dalla schermata: `.github/workflows/update.yml` è già incluso.
3. Vai in [Actions → workflow quote](https://github.com/JRcode197/cometa-pp/actions/workflows/update.yml), premi **Run workflow** sul ramo `main`.
4. Verifica che i job `build` e `deploy` siano entrambi verdi.
5. Apri `https://JRcode197.github.io/cometa-pp/status.json` e confronta `last_quote_eur` con l'ultima quota del sito Cometa.

**Importante:** l'autorizzazione per modificare `Settings → Pages` non è disponibile a tutti i connettori GitHub. Il proprietario deve eventualmente eseguire il passaggio 2 dall'interfaccia GitHub.

## Esecuzione locale e sviluppo

Richiede Python **3.12+** e accesso HTTPS alla pagina ufficiale per l'acquisizione live.

```bash
git clone https://github.com/JRcode197/cometa-pp.git
cd cometa-pp
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/fetch_cometa.py --outdir site
```

Su Windows attiva l'ambiente con `.venv\\Scripts\\activate`, anziché `source`.

I file statici vengono scritti nella cartella `site/`, che è esclusa dal repository salvo il segnaposto `site/index.html`. Il workflow pubblica il contenuto generato come artefatto Pages, senza fare commit dei prezzi su `main`.

### Struttura

```text
.github/
  workflows/
    update.yml       # controlli, download, build, deploy GitHub Pages
    tests.yml        # test delle modifiche in pull request
  dependabot.yml     # aggiornamento dipendenze
scripts/
  fetch_cometa.py    # lettura e validazione dati ufficiali
tests/
  test_parser.py     # verifiche con fixture HTML sintetiche
site/
  index.html         # segnaposto, sovrascritto a ogni build
requirements.txt
README.md
```

## Validazione e limiti

Il parser controlla struttura della tabella, date duplicate e mancanti, intervallo di plausibilità dei NAV, valori storici di riferimento, serie non troncata, data futura e obsolescenza eccessiva. La pagina viene letta via HTTPS, con timeout, limite alle dimensioni e retry selettivi. La suite di test usa HTML sintetico, quindi **non garantisce che un futuro cambiamento della pagina Cometa sia automaticamente compatibile**.

Se il sito Cometa cambia struttura, i dati vengono ritirati/corretti oppure il valore di una quota storica viene ricalcolato, lo script può **interrompere intenzionalmente la pubblicazione**. In tal caso analizza il log del workflow e confronta i dati ufficiali prima di aggiornare il parser o i valori di controllo.

### Risoluzione dei problemi

| Sintomo | Verifica / soluzione |
| --- | --- |
| JSON o pagina restituisce 404 | Apri Settings → Pages, seleziona GitHub Actions, esegui e controlla il workflow |
| Errore `Get Pages site failed` | Pages non attivato oppure token privo dei permessi necessari per leggere Pages; controlla Source e permessi workflow |
| Job `Acquisisci e valida le quotazioni` fallisce | Apri i log: possibile modifica sito, anomalia quota, sito indisponibile o blocco richieste |
| Anteprima Portfolio Performance vuota | Controlla URL accessibile, JSONPath e formato data; verifica che `status.json` non sia obsoleto |
| Prezzi invariati per settimane | Normale tra due pubblicazioni mensili; controlla il mese in `last_quote_date` |
| Feed presente, posizione senza valore | Inserisci le quote realmente detenute e i movimenti nel conto titoli di Portfolio Performance |

## Contributi e avvertenze

Issue e pull request sono benvenute per segnalare errori, modifiche del sito, miglioramenti del parser e test. **Non pubblicare** estratti dell'area riservata o documenti contenenti nominativi, conti, transazioni, TFR, matricole o dati personali.

Questo progetto fornisce soltanto la trasformazione tecnica di informazioni pubbliche. Non è una raccomandazione di investimento; prima di usarne i dati per decisioni economiche verifica la fonte Cometa. Attualmente il repository **non dichiara una licenza software**: per riutilizzi o redistribuzioni del codice valgono i diritti riservati dell'autore, finché non viene aggiunta una licenza esplicita.
