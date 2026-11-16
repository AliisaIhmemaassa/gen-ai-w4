# hakuchat

Python chat server + single `index.html` UI. The model calls OpenRouter via the OpenAI library and can use a `web_search` tool, looping until it gives a text answer.

## Requirements

- Python 3
- `OPENROUTER_API_KEY` environment variable (not `OPEN_ROUTER_UUS`)
- Python package: `openai`

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install openai
```

## Run

```bash
export OPENROUTER_API_KEY=<your openrouter key>
.venv/bin/python server.py
```

Then open `http://127.0.0.1:8080`.

## Behavior

- `GET /` serves `index.html`
- `POST /api/chat` body: `{session_id, message}` → `{answer, search_used, search_query, session_id}`
- `web_search` tool runs `curl` via `subprocess.run` against DuckDuckGo HTML, parses `{title, url}` results
- Tool-use loop: max 5 rounds, then returns whatever text was produced
- Conversation history is kept per browser session (client generates a `session_id` stored in `localStorage`)
- UI shows when search was used and with what query; links in answers are clickable

## Notes

- No Flask: server uses the standard library `http.server`
- `server.py` reads `index.html` from disk, so keep both files together
- The API key must never be committed; `OPENROUTER_API_KEY` is read from the environment only

## Reflektio

**Missä kohdassa agentti teki virheen tai huonon ratkaisun, ja miten huomasit sen?**
En löytänyt yhtään selvää virhettä. Agentti sai toteutuksen valmiiksi ilman, että jouduin korjaamaan sen työtä. Se ei kuitenkaan tarkoita, ettei virheitä olisi voinut olla: testasin sovellusta ajamalla sitä ja kokeilemalla muutamia kysymyksiä, ja kaikki toimi odotetusti.

**Minkä osan koodista ymmärrät heikoimmin? Mitä tekisit asialle?**
Heikoiten ymmärrän `chat_core.py`:n tool-use-silmukan. Aion käydä koodin läpi rivi riviltä, lisätä kommentteja omin sanoin ja kirjoittaa muutaman pienen testin, jotta näen, miten se oikeasti käyttäytyy.

**Miten agentin käyttö vaikutti oppimiseesi verrattuna siihen, että olisit kirjoittanut koodin itse?**
Toteutus eteni selvästi nopeammin, mutta oppiminen jäi pinnallisemmaksi. Jos olisin kirjoittanut koodin itse, olisin joutunut perehtymään OpenAI-kirjastoon ja työkalusilmukkaan kunnolla. Agentin kanssa on helppo hyväksyä ehdotuksia ymmärtämättä niitä kunnolla, ja juuri siksi tool-use-silmukka jäi minulle epäselväksi.

**Milloin malli päätti hakea ja milloin ei? Toimiko päätös järkevästi?**
Malli haki, kun kysymys koski ajankohtaisia asioita tai jotain, mikä piti tarkistaa. Yleisiin keskustelukysymyksiin se vastasi suoraan ilman hakua. Päätös tuntui useimmiten järkevältä, koska turhia hakuja ei tullut. Rajatapauksissa malli saattoi kuitenkin jättää haun tekemättä, vaikka siitä olisi ollut hyötyä.
