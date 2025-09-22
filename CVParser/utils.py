"""
utils.py — Utility generiche, riusabili e indipendenti dal dominio CV.
-------------------------------------------------------------------------------
Contiene funzioni piccole, con singola responsabilità, usabili in qualunque
progetto: normalizzazione stringhe, parsing date (internazionale), telefoni,
paesi e TLD, dedup, filtri “rumore”.

Dipendenze (tutte già nel requirements.txt):
- dateparser : interpreta date in molte lingue e formati (senza hard-code)
- phonenumbers : valida/formatta numeri di telefono (worldwide) in E.164
- pycountry : normalizzazione paesi (ISO), lookup nomi/alias/codici
- tldextract : estrae registrable domain + suffix (TLD) da URL/email
-------------------------------------------------------------------------------
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple, Optional, Iterable

# --- Dipendenze esterne (leggere, pure-Python o con wheel stabili) ------------
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
import pycountry
import tldextract

try:
    import dateparser
    HAS_DATEPARSER = True
except Exception:
    dateparser = None  # type: ignore
    HAS_DATEPARSER = False


# ==============================================================================
# Stringhe & Liste
# ==============================================================================

def norm(s: str) -> str:
    """
    Normalizza una stringa “sporca”:
    - rimuove caratteri invisibili (zero-width space, BOM)
    - uniforma le newlines
    - comprime spazi multipli
    - trim linee e risultato finale
    Non solleva eccezioni: se non è str → restituisce "".
    """
    if not isinstance(s, str):
        return ""
    s = s.replace("\u200b", "").replace("\ufeff", "").replace("\r\n", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = "\n".join(line.strip() for line in s.splitlines())
    return s.strip()


def is_noise(line: str) -> bool:
    """
    Heuristica semplice per scartare righe “rumorose”:
    - solo simboli/spazi
    - troppo corte
    - frasi standard su autorizzazioni privacy (GDPR) molto generiche
    Nota: NON è specifica dei CV; va bene come filtro generico.
    """
    if not line:
        return True
    l = line.strip()
    if re.fullmatch(r"[\W_]+", l):
        return True
    if len(l) <= 1:
        return True
    if re.search(r"(autorizz\w*).*?(trattament\w*).*?(dati|personali)", l, re.I):
        return True
    return False


def dedupe_keep_order(items: List[str], keyfunc=lambda x: x.lower()) -> List[str]:
    """
    De-duplica mantenendo l’ordine della prima occorrenza.
    - keyfunc: funzione per costruire la chiave di confronto (case-insensitive di default).
    """
    seen = set()
    out: List[str] = []
    for it in items or []:
        try:
            k = keyfunc(it)
        except Exception:
            k = it
        if k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out


def shorten(s: str, max_chars: int = 160, ellipsis: str = "…") -> str:
    """
    Accorcia una stringa a max_chars mantenendo parole intere quando possibile.
    - Usa norm() per ripulire.
    - Se è già ≤ max_chars: nessun taglio.
    - Altrimenti tronca e aggiunge ellissi.
    """
    s = norm(s)
    if not s:
        return ""
    if len(s) <= max_chars:
        return s

    cut = max_chars - len(ellipsis)
    if cut <= 0:
        return ellipsis[:max_chars]

    # prova a troncare alla fine dell’ultima parola completa entro "cut"
    i = s.rfind(" ", 0, cut)
    if i == -1 or i < int(cut * 0.6):
        return s[:cut].rstrip() + ellipsis
    return s[:i].rstrip() + ellipsis


# ==============================================================================
# Date (internazionali) — via dateparser
# ==============================================================================

# Impostazioni sensate per CV:
# - preferisce il passato,
# - se giorno/mese mancano, sceglie l’inizio (1),
# - ordine DMY per ambiguità (puoi modificarlo se la tua base CV è diversa)
_DATEPARSER_SETTINGS = {
    "PREFER_DAY_OF_MONTH": "first",
    "PREFER_DATES_FROM": "past",
    "RETURN_AS_TIMEZONE_AWARE": False,
    "DATE_ORDER": "DMY",
    # "LANGUAGES": ["it", "en", "fr", "de", "es"],  # solo se vuoi forzare
}

def _dt_to_iso(d) -> str:
    """Converte un datetime in stringa ISO 'YYYY-MM-DD'. Fallback: ""."""
    try:
        return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"
    except Exception:
        return ""


def parse_date_any(s: str) -> str:
    """
    Interpreta una data in modo multilingua e multi-formato usando dateparser.
    Esempi validi: 'Jul 2021', 'ottobre 2019', '03/2020', '2017', '2020-05-12'.
    Ritorna: ISO 'YYYY-MM-DD' se interpretabile, altrimenti la stringa normalizzata.
    Non solleva eccezioni.
    """
    raw = s
    s = norm(s)
    if not s:
        return ""

    if HAS_DATEPARSER:
        try:
            d = dateparser.parse(s, settings=_DATEPARSER_SETTINGS)
            if d:
                iso = _dt_to_iso(d)
                if iso:
                    return iso
        except Exception:
            pass

    # Fallback minimalisti se dateparser non c’è / non capisce
    m = re.search(r"\b((?:19|20)\d{2})[\/\-.]([01]?\d)[\/\-.]([0-3]?\d)\b", s)
    if m:
        y, mn, d = map(int, m.groups())
        return f"{y:04d}-{mn:02d}-{d:02d}"
    m = re.search(r"\b((?:19|20)\d{2})[\/\-.]([01]?\d)\b", s)
    if m:
        y, mn = map(int, m.groups())
        return f"{y:04d}-{mn:02d}-01"
    m = re.search(r"\b((?:19|20)\d{2})\b", s)
    if m:
        y = int(m.group(1))
        return f"{y:04d}-01-01"

    # Non interpretabile: restituisce il testo pulito
    return s


def parse_range(s: str) -> Tuple[str, str]:
    """
    Interpreta intervalli di date tipo:
      'Gen 2020 - Mag 2022', '03/2020 to 2023', '2019 – presente/current/now'
    Ritorna: (start_iso, end_iso) con end_iso = "" se 'presente'.
    Non solleva eccezioni.
    """
    s = norm(s).replace("—", "-").replace("–", "-")
    # separatori comuni in varie lingue
    parts = re.split(r"\s*(?:-|to|a|al|fino a|hasta|bis|à)\s*", s, maxsplit=1, flags=re.I)
    if len(parts) == 2:
        start_raw, end_raw = parts[0], parts[1]
        if re.search(r"\b(presente|current|oggi|now|attuale)\b", end_raw, re.I):
            return parse_date_any(start_raw), ""
        return parse_date_any(start_raw), parse_date_any(end_raw)
    return parse_date_any(s), ""


# ==============================================================================
# Telefono (worldwide) — via phonenumbers
# ==============================================================================

def norm_phone(raw: str) -> str:
    """
    Normalizza velocemente un numero di telefono “sporco”:
    - mantiene solo cifre e il '+' iniziale
    - rimuove spazi, trattini, parentesi, ecc.
    Non valida: per la validazione usare phonenumbers.
    """
    if not raw:
        return ""
    s = str(raw).strip()
    # conserva un eventuale '+' in testa
    plus = s.lstrip().startswith("+")
    digits = re.sub(r"\D", "", s)
    return f"+{digits}" if plus else digits


def phone_candidates(text: str) -> List[str]:
    """
    Estrae numeri di telefono validi dal testo e li ritorna in formato E.164.
    - Ricerca worldwide (region=None) → nessun bias locale.
    - Output de-duplicato e in ordine di apparizione.
    Non solleva eccezioni.
    """
    out: List[str] = []
    try:
        for match in phonenumbers.PhoneNumberMatcher(text or "", None):
            num = match.number
            if phonenumbers.is_valid_number(num):
                e164 = phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
                out.append(e164)
    except Exception:
        pass
    return dedupe_keep_order(out)


def country_from_phone(e164: str) -> str:
    """
    Dato un numero E.164, deduce il paese (nome canonico ISO in inglese).
    Esempio: '+39...' → 'Italy'. Fallback: ''.
    Non solleva eccezioni.
    """
    try:
        num = phonenumbers.parse(e164 or "", None)
        region = phonenumbers.region_code_for_number(num)  # ISO-3166 alpha-2
        if region:
            c = pycountry.countries.get(alpha_2=region)
            if c:
                return c.name
    except NumberParseException:
        pass
    except Exception:
        pass
    return ""


# ==============================================================================
# Paesi & TLD (pycountry / tldextract) + Inferenza Paese
# ==============================================================================

def country_from_tld(url_or_email: str) -> str:
    """
    Prova a dedurre il paese dall'ultima label del TLD (segnale debole, ma utile).
      'example.co.uk' → 'uk' → 'United Kingdom'
      'site.com.br'   → 'br' → 'Brazil'
    Fallback: ''.
    Non solleva eccezioni.
    """
    try:
        ext = tldextract.extract(url_or_email or "")
        suffix = ext.suffix  # es. 'co.uk' | 'com.br' | 'it'
        if not suffix:
            return ""
        cc = suffix.split(".")[-1]  # ultima label ('it', 'uk', 'br'…)
        if len(cc) == 2:
            c = pycountry.countries.get(alpha_2=cc.upper())
            if c:
                return c.name
    except Exception:
        pass
    return ""


def normalize_country(name_or_code: str) -> str:
    """
    Normalizza nomi o codici paese in un nome canonico ISO (inglese).
    Accetta: 'U.S.', 'USA', 'Estados Unidos', 'Deutschland', 'Italia', 'IT', 'DE', 'BRA', ...
    Se non riconosciuto, restituisce la stringa pulita.
    Non solleva eccezioni.
    """
    s = norm(name_or_code)
    if not s:
        return ""

    # Prova alpha-2 (IT, US, DE, BR, ...)
    try:
        c = pycountry.countries.get(alpha_2=s.upper())
        if c:
            return c.name
    except Exception:
        pass

    # Prova alpha-3 (ITA, USA, DEU, BRA, ...)
    try:
        c = pycountry.countries.get(alpha_3=s.upper())
        if c:
            return c.name
    except Exception:
        pass

    # Rimuovi punteggiatura comune (U.S.A. -> USA)
    s2 = re.sub(r"[^\w ]+", " ", s).strip()

    # Lookup per nome/alias (pycountry gestisce molte varianti locali)
    try:
        c = pycountry.countries.lookup(s2)
        if c:
            return c.name
    except Exception:
        pass

    return s


def country_from_text(text: str) -> str:
    """
    Riconosce un paese dal testo libero usando SOLO pycountry (niente liste hard-code).
    Strategia:
      1) cerca codici ISO (alpha-2/alpha-3) presenti nel testo,
      2) prova lookup su bigrammi (p.es. 'United States', 'Czech Republic'),
      3) prova lookup su singole parole (p.es. 'Italia', 'Deutschland', 'Brasil'),
    Ritorna il nome canonico ISO (inglese) o '' se non trovato.
    Non solleva eccezioni.
    """
    s = norm(text)
    if not s:
        return ""

    # 1) Codici ISO espliciti nel testo
    for m in re.findall(r"\b([A-Z]{2,3})\b", s):
        iso = m.upper()
        c2 = pycountry.countries.get(alpha_2=iso) if len(iso) == 2 else None
        c3 = pycountry.countries.get(alpha_3=iso) if len(iso) == 3 else None
        if c2:
            return c2.name
        if c3:
            return c3.name

    # 2) Bigrammi (e.g., "United States", "Czech Republic")
    words = re.findall(r"[A-Za-zÀ-ÿ]+", s)
    for i in range(len(words) - 1):
        cand = f"{words[i]} {words[i+1]}"
        try:
            c = pycountry.countries.lookup(cand)
            if c:
                return c.name
        except Exception:
            pass

    # 3) Singole parole (alias locali: "España", "Brasil", "Deutschland", ...)
    for w in words:
        try:
            c = pycountry.countries.lookup(w)
            if c:
                return c.name
        except Exception:
            pass

    return ""


# ---- Inferenza “multi-segnale” del paese (alpha2 + name) --------------------

def _country_from_region_code(region_code: str) -> tuple[str, str]:
    """Da 'IT' -> ('IT', 'Italy'). Tollerante a alias e lowercase."""
    if not region_code:
        return "", ""
    try:
        c = pycountry.countries.get(alpha_2=region_code.upper())
        if c:
            name = getattr(c, "common_name", None) or getattr(c, "name", "")
            return c.alpha_2, name
    except Exception:
        pass
    return "", ""


def _country_from_phone_tuple(num_raw: str) -> tuple[str, str]:
    """
    Versione 'tuple' per lo scoring: da telefono → (alpha2, name).
    Usa norm_phone + phonenumbers. Fallback: vuoti.
    """
    if not num_raw:
        return "", ""
    s = norm_phone(num_raw)
    if not s:
        return "", ""
    try:
        n = phonenumbers.parse(s, None)
        if phonenumbers.is_valid_number(n):
            region = phonenumbers.region_code_for_number(n)  # es. 'IT'
            return _country_from_region_code(region)
    except NumberParseException:
        pass
    except Exception:
        pass
    # Tentativo "soft" se manca il prefisso +
    try:
        n = phonenumbers.parse(s, "US")
        if phonenumbers.is_possible_number(n):
            region = phonenumbers.region_code_for_number(n)
            return _country_from_region_code(region)
    except Exception:
        pass
    return "", ""


def _country_from_tld_tuple(url_or_email: str) -> tuple[str, str]:
    """
    Versione 'tuple' per lo scoring: da TLD/email → (alpha2, name).
    Gestisce 'co.uk' → 'GB' e 'el' → 'GR' come alias storici minimi.
    """
    if not url_or_email:
        return "", ""
    try:
        ext = tldextract.extract(url_or_email)
        suffix = (ext.suffix or "").lower()
        if not suffix:
            return "", ""
        tld_last = suffix.split(".")[-1]  # 'uk' da 'co.uk'
        special = {"uk": "GB", "el": "GR"}  # alias rari / storici
        code = special.get(tld_last.upper(), tld_last.upper())
        return _country_from_region_code(code)
    except Exception:
        return "", ""


def _country_from_text_tuple(name_or_code: str) -> tuple[str, str]:
    """
    Versione 'tuple' per lo scoring: da testo libero → (alpha2, name).
    Usa pycountry.lookup e ricerca per contenimento (no liste hard-coded).
    """
    s = norm(name_or_code)
    if not s:
        return "", ""
    c = None
    # Lookup diretto (alpha2/alpha3 o nome)
    try:
        c = pycountry.countries.lookup(s)
    except Exception:
        c = None
    # Ricerca grezza per contenimento su name/common_name/official_name
    if not c:
        for cc in pycountry.countries:
            names: list[str] = []
            for attr in ("name", "common_name", "official_name"):
                v = getattr(cc, attr, None)
                if v:
                    names.append(v.lower())
            if any(s.lower() == nm or s.lower() in nm for nm in names):
                c = cc
                break
    if c:
        return c.alpha_2, (getattr(c, "common_name", None) or getattr(c, "name", ""))
    return "", ""


def _vote(codes: Iterable[tuple[str, str]]) -> tuple[str, str]:
    """
    Sceglie il paese con più 'voti' tra le sorgenti (phone, tld, testo).
    Ritorna (alpha2, name) oppure vuoti se nessun segnale.
    """
    counts: dict[str, int] = {}
    names: dict[str, str] = {}
    for code, name in codes:
        if not code:
            continue
        k = code.upper()
        counts[k] = counts.get(k, 0) + 1
        if k not in names and name:
            names[k] = name
    if not counts:
        return "", ""
    best = max(counts.items(), key=lambda kv: kv[1])[0]
    return best, names.get(best, _country_from_region_code(best)[1])


def guess_region_from_internal(internal: Dict[str, Any]) -> Dict[str, str]:
    """
    Deduce il paese più probabile guardando:
    - telefono/cellulare (prefisso internazionale)
    - email / sito / linkedin / github (TLD)
    - indirizzo.paese / luogo_nascita (testo libero)
    Restituisce {'alpha2': 'IT', 'name': 'Italy'} o vuoti se non deducibile.
    Non solleva eccezioni.
    """
    if not isinstance(internal, dict):
        return {"alpha2": "", "name": ""}

    contatti = internal.get("contatti", {}) if isinstance(internal.get("contatti", {}), dict) else {}
    indirizzo = contatti.get("indirizzo", {}) if isinstance(contatti.get("indirizzo", {}), dict) else {}
    anag = internal.get("anagrafica", {}) if isinstance(internal.get("anagrafica", {}), dict) else {}

    # 1) phone-based
    phone_code = _country_from_phone_tuple(contatti.get("telefono", ""))
    cell_code  = _country_from_phone_tuple(contatti.get("cellulare", ""))

    # 2) tld-based
    tld_candidates = [
        _country_from_tld_tuple(contatti.get("email", "")),
        _country_from_tld_tuple(contatti.get("sito_web", "")),
        _country_from_tld_tuple(contatti.get("linkedin", "")),
        _country_from_tld_tuple(contatti.get("github", "")),
    ]

    # 3) text-based
    text_candidates = [
        _country_from_text_tuple(indirizzo.get("paese", "")),
        _country_from_text_tuple(anag.get("luogo_nascita", "")),
        _country_from_text_tuple(anag.get("nazionalita", "")),
    ]

    alpha2, name = _vote([phone_code, cell_code, *tld_candidates, *text_candidates])
    return {"alpha2": alpha2, "name": name}
