"""
normalizers.py — Mappa il 'formato interno' prodotto dal parser
nel JSON finale (chiavi in italiano), con pulizia e coerenza.

Funzione pubblica:
    to_schema(internal: dict) -> dict

Note:
- Nessuna 'completamento_percentuale' viene inserita: la % è responsabilità di chi visualizza.
- Evitiamo tassonomie hard-coded. Qui si fa solo sanificazione, validazione formale e riempimento dei campi dello schema.
"""

from __future__ import annotations

from typing import Any, Dict, List

import re

# Librerie esterne leggere già nel requirements
from email_validator import validate_email, EmailNotValidError  # validazione email
import validators  # URL semplici (http/https)
import phonenumbers  # normalizzazione telefoni E.164

# Utility comuni nostre
from utils import (
    norm, dedupe_keep_order, shorten,
    country_from_tld, normalize_country, guess_region_from_internal,
)


# -------------------------------------------------------------
# Helpers locali di normalizzazione
# -------------------------------------------------------------

def _norm_email(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    try:
        return validate_email(s, check_deliverability=False).normalized
    except EmailNotValidError:
        return ""

def _norm_url(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    if not (s.startswith("http://") or s.startswith("https://")):
        s = "https://" + s
    return s if validators.url(s) else ""

def _norm_phone(s: str, region_hint: str = "US") -> str:
    """
    Tenta E.164 con phonenumbers:
      - se ha il +, parse senza regione
      - altrimenti prova col region_hint (derivato da email/TLD/altro)
    """
    raw = (s or "").strip()
    if not raw:
        return ""
    try:
        if raw.startswith("+"):
            num = phonenumbers.parse(raw, None)
        else:
            num = phonenumbers.parse(raw, region_hint or "US")
        if phonenumbers.is_valid_number(num):
            return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        pass
    return ""

def _ensure_list_of_dicts(items: List[Dict[str, Any]] | None, template: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not items:
        return [template.copy()]
    # se ci sono ma non sono dict, forziamo il template vuoto
    out: List[Dict[str, Any]] = []
    for it in items:
        if isinstance(it, dict):
            out.append(it)
    return out or [template.copy()]

def _clean_text_block(s: str) -> str:
    # Accetta testo multi-riga ma limita lunghezze assurde e normalizza spazi
    s = norm(s or "")
    return shorten(s, 2000)

def _clean_short(s: str, maxlen: int = 160) -> str:
    return shorten(norm(s or ""), maxlen)


# -------------------------------------------------------------
# Normalizzazione principale
# -------------------------------------------------------------

def to_schema(internal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte il dict 'internal' (prodotto dal parser) nello schema finale:
    {
      "anagrafica": {...},
      "contatti": {...},
      "istruzione": [ ... ],
      "esperienze_lavorative": [ ... ],
      "competenze_tecniche": {...},
      "competenze_linguistiche": [ ... ],
      "competenze_trasversali": [],
      "certificazioni": [ ... ],
      "progetti": [ ... ],
      "pubblicazioni": [ ... ],
      "interessi": [],
      "patente": [],
      "autorizzazione_trattamento_dati": "",
      "disponibilita": {...}
    }
    """
    internal = internal or {}

    # ---------------- anagrafica ----------------
    an = internal.get("anagrafica", {}) or {}
    anagrafica = {
        "nome": _clean_short(an.get("nome", ""), 80),
        "cognome": _clean_short(an.get("cognome", ""), 120),
        "data_nascita": _clean_short(an.get("data_nascita", ""), 20),
        "luogo_nascita": _clean_short(an.get("luogo_nascita", ""), 120),
        "nazionalita": _clean_short(an.get("nazionalita", ""), 80),
        "sesso": _clean_short(an.get("sesso", ""), 20),
        "stato_civile": _clean_short(an.get("stato_civile", ""), 40),
    }

    # ---------------- contatti ----------------
    cont = internal.get("contatti", {}) or {}
    indir = cont.get("indirizzo", {}) or {}

    # Regione da usare come hint per i telefoni (dedotta da internal: email/TLD ecc.)
    region_hint = guess_region_from_internal(internal) or "US"

    telefono = _norm_phone(cont.get("telefono", ""), region_hint)
    cellulare = _norm_phone(cont.get("cellulare", ""), region_hint)

    email = _norm_email(cont.get("email", ""))
    linkedin = _norm_url(cont.get("linkedin", ""))
    github = _norm_url(cont.get("github", ""))
    sito = _norm_url(cont.get("sito_web", ""))

    # Se il sito non c'è ma posso dedurre dominio valido da linkedin/github, lascio com’è (non invento)
    # Paese: già stimato a monte, ma passo comunque da normalize_country per coerenza finale
    paese = normalize_country(indir.get("paese", ""))

    contatti = {
        "indirizzo": {
            "via": _clean_short(indir.get("via", ""), 160),
            "citta": _clean_short(indir.get("citta", ""), 120),
            "cap": _clean_short(indir.get("cap", ""), 12),
            "provincia": _clean_short(indir.get("provincia", ""), 80),
            "paese": paese,
        },
        "telefono": telefono,
        "cellulare": cellulare,
        "email": email,
        "linkedin": linkedin,
        "sito_web": sito,
        "github": github,
    }

    # ---------------- istruzione ----------------
    istr_items = internal.get("istruzione", []) or []
    istr_norm: List[Dict[str, Any]] = []
    for it in istr_items:
        if not isinstance(it, dict):
            continue
        istr_norm.append({
            "titolo_studio": _clean_short(it.get("titolo_studio", ""), 200),
            "istituto": _clean_short(it.get("istituto", ""), 200),
            "citta": _clean_short(it.get("citta", ""), 120),
            "paese": _clean_short(it.get("paese", ""), 120),
            "data_inizio": _clean_short(it.get("data_inizio", ""), 20),
            "data_fine": _clean_short(it.get("data_fine", ""), 20),
            "voto": _clean_short(it.get("voto", ""), 50),
            "descrizione": _clean_text_block(it.get("descrizione", "")),
            "tesi": _clean_short(it.get("tesi", ""), 280),
        })
    istruzione = _ensure_list_of_dicts(istr_norm, {
        "titolo_studio": "", "istituto": "", "citta": "", "paese": "",
        "data_inizio": "", "data_fine": "", "voto": "", "descrizione": "", "tesi": ""
    })

    # ---------------- esperienze_lavorative ----------------
    exp_items = internal.get("esperienze_lavorative", []) or []
    exp_norm: List[Dict[str, Any]] = []
    for it in exp_items:
        if not isinstance(it, dict):
            continue
        exp_norm.append({
            "posizione": _clean_short(it.get("posizione", ""), 200),
            "azienda": _clean_short(it.get("azienda", ""), 200),
            "citta": _clean_short(it.get("citta", ""), 120),
            "paese": _clean_short(it.get("paese", ""), 120),
            "data_inizio": _clean_short(it.get("data_inizio", ""), 20),
            "data_fine": _clean_short(it.get("data_fine", ""), 20),
            "descrizione": _clean_text_block(it.get("descrizione", "")),
            "responsabilita": dedupe_keep_order([
                _clean_short(x, 200) for x in it.get("responsabilita", []) if isinstance(x, str)
            ])[:30],
            "risultati_ottenuti": dedupe_keep_order([
                _clean_short(x, 200) for x in it.get("risultati_ottenuti", []) if isinstance(x, str)
            ])[:30],
        })
    esperienze_lavorative = _ensure_list_of_dicts(exp_norm, {
        "posizione": "", "azienda": "", "citta": "", "paese": "",
        "data_inizio": "", "data_fine": "", "descrizione": "",
        "responsabilita": [], "risultati_ottenuti": []
    })

    # ---------------- competenze_tecniche ----------------
    comp = internal.get("competenze_tecniche", {}) or {}
    competenze_tecniche = {
        "linguaggi_programmazione": dedupe_keep_order([_clean_short(x, 120) for x in comp.get("linguaggi_programmazione", []) if isinstance(x, str)])[:50],
        "framework":                 dedupe_keep_order([_clean_short(x, 120) for x in comp.get("framework", []) if isinstance(x, str)])[:50],
        "database":                  dedupe_keep_order([_clean_short(x, 120) for x in comp.get("database", []) if isinstance(x, str)])[:50],
        "strumenti":                 dedupe_keep_order([_clean_short(x, 120) for x in comp.get("strumenti", []) if isinstance(x, str)])[:50],
        "metodologie":               dedupe_keep_order([_clean_short(x, 120) for x in comp.get("metodologie", []) if isinstance(x, str)])[:50],
        "altre_competenze":          dedupe_keep_order([_clean_short(x, 160) for x in comp.get("altre_competenze", []) if isinstance(x, str)])[:150],
    }

    # ---------------- competenze_linguistiche ----------------
    langs = internal.get("competenze_linguistiche", []) or []
    langs_norm: List[Dict[str, Any]] = []
    for it in langs:
        if not isinstance(it, dict):
            continue
        langs_norm.append({
            "lingua": _clean_short(it.get("lingua", ""), 120),
            "livello_scritto": _clean_short(it.get("livello_scritto", ""), 8),
            "livello_parlato": _clean_short(it.get("livello_parlato", ""), 8),
            "certificazioni": dedupe_keep_order([
                _clean_short(x, 160) for x in it.get("certificazioni", []) if isinstance(x, str)
            ])[:20],
        })
    competenze_linguistiche = _ensure_list_of_dicts(langs_norm, {
        "lingua": "", "livello_scritto": "", "livello_parlato": "", "certificazioni": []
    })

    # ---------------- competenze_trasversali ----------------
    soft = internal.get("competenze_trasversali", []) or []
    competenze_trasversali = dedupe_keep_order([_clean_short(x, 160) for x in soft if isinstance(x, str)])[:50]

    # ---------------- certificazioni ----------------
    certs = internal.get("certificazioni", []) or []
    certs_norm: List[Dict[str, Any]] = []
    for it in certs:
        if not isinstance(it, dict):
            continue
        certs_norm.append({
            "nome": _clean_short(it.get("nome", ""), 200),
            "ente_certificatore": _clean_short(it.get("ente_certificatore", ""), 200),
            "data_ottenimento": _clean_short(it.get("data_ottenimento", ""), 20),
            "data_scadenza": _clean_short(it.get("data_scadenza", ""), 20),
            "numero_certificato": _clean_short(it.get("numero_certificato", ""), 80),
        })
    certificazioni = _ensure_list_of_dicts(certs_norm, {
        "nome": "", "ente_certificatore": "", "data_ottenimento": "", "data_scadenza": "", "numero_certificato": ""
    })

    # ---------------- progetti ----------------
    projs = internal.get("progetti", []) or []
    projs_norm: List[Dict[str, Any]] = []
    for it in projs:
        if not isinstance(it, dict):
            continue
        link = _norm_url(it.get("link", ""))
        projs_norm.append({
            "nome": _clean_short(it.get("nome", ""), 200),
            "descrizione": _clean_text_block(it.get("descrizione", "")),
            "ruolo": _clean_short(it.get("ruolo", ""), 160),
            "tecnologie": dedupe_keep_order([_clean_short(x, 120) for x in it.get("tecnologie", []) if isinstance(x, str)])[:40],
            "link": link,
        })
    progetti = _ensure_list_of_dicts(projs_norm, {
        "nome": "", "descrizione": "", "ruolo": "", "tecnologie": [], "link": ""
    })

    # ---------------- pubblicazioni ----------------
    pubs = internal.get("pubblicazioni", []) or []
    pubs_norm: List[Dict[str, Any]] = []
    for it in pubs:
        if not isinstance(it, dict):
            continue
        link = _norm_url(it.get("link", ""))
        pubs_norm.append({
            "titolo": _clean_short(it.get("titolo", ""), 240),
            "autori": dedupe_keep_order([_clean_short(x, 120) for x in it.get("autori", []) if isinstance(x, str)])[:20],
            "data": _clean_short(it.get("data", ""), 20),
            "rivista_conferenza": _clean_short(it.get("rivista_conferenza", ""), 200),
            "link": link,
        })
    pubblicazioni = _ensure_list_of_dicts(pubs_norm, {
        "titolo": "", "autori": [], "data": "", "rivista_conferenza": "", "link": ""
    })

    # ---------------- interessi / patente ----------------
    interessi = dedupe_keep_order([_clean_short(x, 80) for x in internal.get("interessi", []) if isinstance(x, str)])[:30]
    patente    = dedupe_keep_order([_clean_short(x, 40) for x in internal.get("patente", []) if isinstance(x, str)])[:10]

    # ---------------- privacy / disponibilita ----------------
    privacy = _clean_text_block(internal.get("autorizzazione_trattamento_dati", ""))
    disp = internal.get("disponibilita", {}) or {}
    disponibilita = {
        "trasferte": _clean_short(disp.get("trasferte", ""), 80),
        "trasferimento": _clean_short(disp.get("trasferimento", ""), 80),
        "tipo_contratto_preferito": dedupe_keep_order([
            _clean_short(x, 60) for x in disp.get("tipo_contratto_preferito", []) if isinstance(x, str)
        ])[:10]
    }

    # ---------------- OUTPUT finale ----------------
    schema: Dict[str, Any] = {
        "anagrafica": anagrafica,
        "contatti": contatti,
        "istruzione": istruzione,
        "esperienze_lavorative": esperienze_lavorative,
        "competenze_tecniche": competenze_tecniche,
        "competenze_linguistiche": competenze_linguistiche,
        "competenze_trasversali": competenze_trasversali,
        "certificazioni": certificazioni,
        "progetti": progetti,
        "pubblicazioni": pubblicazioni,
        "interessi": interessi,
        "patente": patente,
        "autorizzazione_trattamento_dati": privacy,
        "disponibilita": disponibilita,
    }
    return schema