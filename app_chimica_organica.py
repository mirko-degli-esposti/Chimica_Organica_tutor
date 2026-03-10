import re
import requests
import streamlit as st
from openai import OpenAI
from urllib.parse import quote

# ── Configurazione pagina ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Tutor – Chimica Organica",
    page_icon="🎓",
    layout="centered"
)

# ── Stile minimale ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { max-width: 760px; margin: auto; }
    .stChatMessage { border-radius: 12px; }
    .disclaimer {
        font-size: 0.78rem;
        color: #888;
        border-left: 3px solid #e0e0e0;
        padding-left: 10px;
        margin-top: 8px;
    }
    .mol-container {
        text-align: center;
        margin: 12px auto;
        padding: 8px;
        background: #fafafa;
        border: 1px solid #e8e8e8;
        border-radius: 8px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
Sei un tutor accademico personale per il corso 00148 – Chimica Organica,
Laurea in Scienza dei Materiali (cod. 5940), Università di Bologna, A.A. 2025/2026.
Docente: prof. Paolo Righi. 6 CFU, SSD CHIM/06.

SYLLABUS DEL CORSO
==================

Prerequisiti: argomenti di Chimica Generale.

Programma (argomenti in ordine):
1.  Struttura e legame
2.  Gli alcani
3.  Stereochimica
4.  Le reazioni organiche
5.  Gli alcheni e gli alchini
6.  Coniugazione e aromaticità
7.  Reazione di sostituzione ed eliminazione degli alogenuri alchilici (SN1, SN2, E1, E2)
8.  Reazioni di alcoli, ammine, eteri, epossidi e tioli
9.  Reazioni degli acidi carbossilici e dei loro derivati
10. Reazioni delle aldeidi e dei chetoni
11. Reazioni del carbonio α dei composti carbonilici (enoli, enolati, condensazione aldolica)
12. I radicali

TESTO
=====
Paula Yurkanis Bruice – Elementi di Chimica Organica, 3a ed., EdiSES, 2024
(ISBN: 9788836231652)

ESAME
=====
Prova scritta finale (120 minuti) su tutti gli argomenti del programma di teoria.
Scopo: valutare la comprensione dei concetti esposti a lezione e la capacità di
applicarli alla risoluzione di semplici problemi di chimica organica.
(Il laboratorio è parte separata del corso.)

==================
RAPPRESENTAZIONE DELLE STRUTTURE CHIMICHE
==================

Ogni volta che vuoi mostrare una struttura chimica, una molecola, un intermedio
di reazione o un prodotto, usa OBBLIGATORIAMENTE il seguente formato speciale:

    [MOL: SMILES]

dove SMILES è la notazione SMILES valida della struttura. Esempi:
- Acido acetico:         [MOL: CC(=O)O]
- Etanolo:               [MOL: CCO]
- Benzene:               [MOL: c1ccccc1]
- Bromuro di metile:     [MOL: CBr]
- Acetone:               [MOL: CC(=O)C]
- Cicloesammio:          [MOL: C1CCCCC1]
- Acido benzoico:        [MOL: OC(=O)c1ccccc1]
- Anione enolato:        [MOL: CC(=O)[CH2-]]
- Carbocatione terz.:    [MOL: CC([CH3+])C] (nota: usa [C+] per cariche)

Usa SMILES corretti e precisi. L'interfaccia renderizzerà automaticamente
la struttura 2D — lo studente vedrà il disegno, non il testo SMILES.

Per i meccanismi di reazione in più step, mostra ogni intermedio o prodotto
rilevante con il suo [MOL: SMILES] separato, e descrivi le frecce/trasformazioni
in prosa tra una struttura e l'altra.

Non scrivere MAI le strutture come testo ASCII o come formule di struttura
con trattini — usa sempre [MOL: SMILES].

==================
RUOLO E OBIETTIVO
==================

Il tuo ruolo è accompagnare lo studente nello studio in modo continuativo
ma NON sostitutivo. Non sei un risolutore di esercizi: sei un interlocutore
che aiuta lo studente a capire, ragionare e prepararsi all'esame in modo
autonomo e consapevole.

COMPORTAMENTO
=============
- Inizia SEMPRE chiedendo a che punto del programma si trova lo studente
  e che tipo di supporto desidera in quel momento.
- Usa approccio dialogico: fai domande PRIMA di spiegare.
- Adatta il livello alle risposte dello studente.
- Linguaggio chiaro, incoraggiante ma rigoroso.
- Non usare tono valutativo negativo: accogli gli errori come punti di partenza.

COSA FARE
=========
1. STRUTTURA E REATTIVITÀ: aiuta lo studente a costruire intuizione sui meccanismi —
   non a memorizzarli, ma a capire perché avvengono (elettrofilicità, nucleofilicità,
   stabilità degli intermedi, effetti elettronici e sterici).
   Mostra sempre le strutture rilevanti con [MOL: SMILES].

2. MECCANISMI DI REAZIONE: guida step-by-step, mostrando ogni intermedio.
   Non dare il meccanismo completo subito — chiedi prima cosa lo studente
   sa già sul tipo di reazione e sulle specie coinvolte.

3. STEREOCHIMICA: è un argomento trasversale. Aiuta a ragionare su
   configurazione R/S, reazioni stereospecifiche (SN2 vs SN1),
   diastereomeri e enantiomeri.

4. GRUPPI FUNZIONALI: aiuta a costruire una mappa mentale delle reattività
   comparative — es. perché un estere è meno reattivo di un alogenuro acilico.

5. VERIFICA: dopo ogni spiegazione proponi una micro-domanda di verifica
   (disegna il prodotto, identifica il meccanismo, prevedi la stereochimica).

6. PREPARAZIONE ESAME: simula domande scritte tipiche, aiuta l'autovalutazione.

COSA NON FARE
=============
- Non svolgere esercizi valutativi al posto dello studente.
- Non fornire meccanismi completi senza aver prima verificato
  cosa lo studente sa già.
- Non rispondere a domande fuori contesto rispetto al corso.

LIMITI DELL'IA
==============
Ogni volta che tratti un passaggio tecnico delicato (meccanismi, stereochimica,
reattività comparata), aggiungi sempre una nota del tipo:
"⚠️ Verifica questo passaggio su Bruice (cap. X): l'IA può commettere errori
su dettagli meccanicistici."

FORMATO
=======
- Risposte brevi e dialogiche nella fase di diagnosi.
- Per spiegazioni di meccanismi: usa [MOL: SMILES] per ogni struttura rilevante
  e descrivi le trasformazioni in prosa tra una struttura e l'altra.
- Usa LaTeX solo per equazioni non strutturali: es. $\\Delta G = \\Delta H - T\\Delta S$.
- Non superare 350 parole per risposta, salvo meccanismi multi-step richiesti.
"""

# ── Rendering molecole con CDK Depict ─────────────────────────────────────────
MOL_PATTERN = re.compile(r'\[MOL:\s*([^\]]+)\]')

def fetch_svg(smiles: str, width: int = 280, height: int = 180) -> str | None:
    """Chiama CDK Depict e restituisce l'SVG come stringa, o None se fallisce."""
    try:
        encoded = quote(smiles.strip())
        url = (
            f"https://www.simolecule.com/cdkdepict/depict/bow/svg"
            f"?smi={encoded}&w={width}&h={height}&zoom=1.5"
        )
        r = requests.get(url, timeout=6)
        if r.status_code == 200 and "<svg" in r.text:
            return r.text
    except Exception:
        pass
    return None

def render_message(text: str):
    """
    Renderizza un messaggio del tutor spezzandolo in segmenti di testo
    e strutture molecolari. Ogni [MOL: SMILES] viene sostituito con
    l'SVG di CDK Depict; il resto viene renderizzato come Markdown.
    """
    segments = MOL_PATTERN.split(text)
    # split alterna: testo, smiles, testo, smiles, ...
    for i, seg in enumerate(segments):
        if i % 2 == 0:
            # Segmento di testo
            if seg.strip():
                st.markdown(seg)
        else:
            # Segmento SMILES
            smiles = seg.strip()
            svg = fetch_svg(smiles)
            if svg:
                st.markdown(
                    f'<div class="mol-container">{svg}</div>'
                    f'<p style="text-align:center;font-size:0.75rem;color:#aaa;">'
                    f'<code>{smiles}</code></p>',
                    unsafe_allow_html=True,
                )
            else:
                # Fallback: mostra SMILES come codice
                st.markdown(f"**Struttura** (SMILES): `{smiles}`")

# ── Inizializzazione sessione ──────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "client" not in st.session_state:
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
        st.session_state.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        st.session_state.api_ready = True
    except Exception:
        st.session_state.api_ready = False

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🎓 Tutor – Chimica Organica")
st.caption("00148 · Prof. Righi · Università di Bologna · A.A. 2025/2026")
st.divider()

# ── Disclaimer fisso ──────────────────────────────────────────────────────────
st.markdown("""
<div class="disclaimer">
⚠️ <strong>Nota:</strong> questo tutor è uno strumento di supporto basato su IA.
Può commettere errori su meccanismi e strutture. Verifica sempre le risposte su
Bruice – <em>Elementi di Chimica Organica</em> (3a ed., EdiSES) e sul materiale del corso su Virtuale.
</div>
""", unsafe_allow_html=True)
st.write("")

# ── Controllo API ──────────────────────────────────────────────────────────────
if not st.session_state.get("api_ready"):
    st.error("⚠️ API key non trovata. Configura OPENROUTER_API_KEY nei secrets di Streamlit.")
    st.stop()

# ── Visualizzazione storico ────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            render_message(msg["content"])
        else:
            st.markdown(msg["content"])

# ── Messaggio di benvenuto (solo prima volta) ──────────────────────────────────
if not st.session_state.messages:
    welcome = (
        "Benvenuto/a! Sono il tuo tutor per **Chimica Organica**. "
        "Sono qui per aiutarti a capire strutture, meccanismi e reattività — "
        "non a darti le risposte, ma a farti ragionare sulle molecole.\n\n"
        "Posso mostrarti le strutture chimiche direttamente nella chat. "
        "Per esempio, l'acido acetico è così:\n\n"
        "[MOL: CC(=O)O]\n\n"
        "Per iniziare: **a che punto sei con il programma?** "
        "Stai seguendo le lezioni, stai ripassando per l'esame, "
        "o c'è un argomento — meccanismi SN, gruppi carbonilici, stereochimica — "
        "su cui ti senti in difficoltà?"
    )
    with st.chat_message("assistant"):
        render_message(welcome)
    st.session_state.messages.append({"role": "assistant", "content": welcome})

# ── Input utente ───────────────────────────────────────────────────────────────
if prompt := st.chat_input("Scrivi qui il tuo messaggio..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        # Durante lo streaming: testo grezzo con cursore
        stream_placeholder = st.empty()
        full_response = ""

        try:
            stream = st.session_state.client.chat.completions.create(
                model="anthropic/claude-sonnet-4-5",
                max_tokens=1200,
                stream=True,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT}
                ] + [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    full_response += delta
                    # Streaming: mostra testo grezzo (i tag [MOL:...] appaiono come testo)
                    stream_placeholder.markdown(full_response + "▌")

            # Streaming completato: rimuovi il placeholder grezzo
            stream_placeholder.empty()
            # Renderizza il messaggio finale con le molecole
            render_message(full_response)

        except Exception as e:
            full_response = f"⚠️ Errore nella chiamata API: {str(e)}"
            stream_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

# ── Sidebar: reset e download ──────────────────────────────────────────────────
with st.sidebar:
    st.header("Opzioni")
    if st.button("🔄 Nuova conversazione", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.session_state.get("messages"):
        from datetime import datetime

        def format_chat_markdown():
            lines = [
                "# Conversazione – Tutor Chimica Organica",
                f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                "**Corso:** 00148 – Chimica Organica | UniBO | A.A. 2025/2026",
                "---\n",
            ]
            for msg in st.session_state.messages:
                label = "**Studente**" if msg["role"] == "user" else "**Tutor**"
                lines.append(f"{label}\n\n{msg['content']}\n\n---\n")
            return "\n".join(lines)

        st.download_button(
            label="💾 Scarica conversazione",
            data=format_chat_markdown(),
            file_name=f"chat_chimica_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.divider()
    st.caption("Modello: anthropic/claude-sonnet-4-5")
    st.caption("Strutture: CDK Depict API")
    st.caption("Corso: 00148 – CHIM/06")
    st.caption("Università di Bologna")
