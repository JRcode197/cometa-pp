# Cometa Crescita → Portfolio Performance

Repository per il recupero automatico dei **valori quota mensili pubblici** del comparto **Crescita del Fondo Cometa** e l'esposizione in JSON/CSV utilizzabile da Portfolio Performance. Fonte esclusiva: https://www.cometafondo.it/andamenti/crescita/

> Il repository non include credenziali, posizione previdenziale individuale, contribuzioni o TFR. Non è affiliato né a Fondo Cometa né a Portfolio Performance.
>
> **Stato:** codice, test e workflow installati. Il primo download reale e la pubblicazione sono da verificare dopo la configurazione di GitHub Pages. I test sono sintetici e non sostituiscono il collaudo del sito reale.

## Visibilità e GitHub Pages

Il repository è stato creato **privato**, e rimane privato finché non decidi di modificarlo. GitHub Pages per repository privati può richiedere un piano GitHub a pagamento. Anche con un repository privato, il sito Pages standard può essere **pubblicamente accessibile**: pubblica esclusivamente dati pubblici.

Per usare GitHub Pages, apri **Settings → Pages → Build and deployment → Source**, seleziona **GitHub Actions** e verifica che il tuo piano lo consenta. Se GitHub Pages risulta bloccato, la soluzione più semplice con GitHub Free è rendere pubblico *solo questo repository*, che non contiene alcun dato personale.

## Configurazione Portfolio Performance

Dopo il primo workflow riuscito e la pubblicazione di Pages, apri:

https://JRcode197.github.io/cometa-pp/cometa-crescita.json

Configura nel titolo *Fondo Cometa - Crescita* (EUR):

| Campo | Valore |
| --- | --- |
| Fornitore quotazioni storiche | JSON |
| URL | `https://JRcode197.github.io/cometa-pp/cometa-crescita.json` |
| JSONPath data | `$[*].date` |
| JSONPath prezzo | `$[*].close` |
| Formato data (se richiesto) | `yyyy-MM-dd` |

Controlla le quotazioni con **Anteprima**. Il feed aggiorna il valore unitario, non il numero di quote possedute.

## Automazione

Il workflow `.github/workflows/update.yml` è programmato ogni mercoledì alle 07:21 UTC, e può anche essere eseguito manualmente dalla scheda **Actions**. Esegue test, scarica l'HTML ufficiale, verifica la coerenza della serie, genera i feed e ne tenta il deploy.

Il workflow `.github/workflows/tests.yml` esegue la suite sulle pull request. Le dipendenze sono versionate e Dependabot propone aggiornamenti mensili.

I file pubblicati sono `cometa-crescita.json`, `cometa-crescita.csv`, `status.json` e `index.html`.

## Sicurezza e gestione errori

- Nessun login Cometa e nessun token personale.
- Solo HTTPS dal dominio ufficiale, con timeout, limiti di dimensione e tentativi per errori transitori.
- Il parser rifiuta righe duplicate, buchi mensili, serie troncate, date future, valori palesemente errati e ritardi oltre 150 giorni.
- Controlli storici di integrità sui valori verificati manualmente. Un eventuale ricalcolo storico di Cometa richiede revisione.
- In caso di fallimento non viene pubblicata una nuova versione; il feed precedentemente pubblicato potrebbe rimanere online. Controlla `status.json` e il workflow.
- Le date nel feed rappresentano l'ultimo giorno **di calendario** di ciascun mese; non sono date delle transazioni.
- Permissions del workflow minimali: read di default e `pages:write` e `id-token:write` solo nel job deploy.

## Test

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
python3 scripts/fetch_cometa.py --outdir site
```

L'ultimo comando richiede accesso alla pagina ufficiale e va eseguito durante il collaudo. In caso di errore consulta la scheda Actions o verifica che Cometa non abbia modificato la struttura della tabella.

## Primo collaudo

1. Abilita **Pages → GitHub Actions** se il piano lo consente.
2. Vai in **Actions → Cometa Crescita - aggiorna e pubblica le quote → Run workflow**.
3. Verifica che `build` e `deploy` terminino correttamente.
4. Apri https://JRcode197.github.io/cometa-pp/status.json, verifica `generated_at_utc` e `last_quote_date`; confronta l'ultima quota con quella del sito ufficiale.

Se GitHub Pages non è disponibile per il piano attuale, non tentare di pubblicare dati personali: scegli la visibilità pubblica *solo per questo repository* oppure un hosting alternativo per il JSON.
