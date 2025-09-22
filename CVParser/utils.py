"""
utils.py — Utility generiche, riusabili e indipendenti dal dominio CV.
-------------------------------------------------------------------------------
Dipendenze usate (tutte nel requirements.txt):
- ftfy         : ripara Unicode/encoding nei testi “sporchi”
- dateparser   : parsing date multilingua, nessun hard-code di mesi
- phonenumbers : validazione/normalizzazione telefoni worldwide (E.164)
- pycountry    : normalizzazione paesi (ISO), lookup nomi/alias/codici
- tldextract   : estrae registrable domain + suffix (TLD) da URL/email
- unidecode    : traslitterazione utile per matching robusto
- rapidfuzz    : fuzzy utils (solo per dedupe key opzionale, leggero)
- langdetect   : riconoscimento lingua 

Le funzioni qui definite sono pure e “defensive” (mai eccezioni in uscita).
-------------------------------------------------------------------------------
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple, Optional

# --- Dipendenze esterne leggere ---
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
import pycountry
import tldextract

from babel import Locale

# ftfy è opzionale: se manca, norm() degrada con una pulizia base
try:
    import ftfy
    _HAS_FTFY = True
except Exception:
    ftfy = None  # type: ignore
    _HAS_FTFY = False

try:
    import dateparser
    _HAS_DATEPARSER = True
except Exception:
    dateparser = None  # type: ignore
    _HAS_DATEPARSER = False


# ==============================================================================
# Stringhe & Liste
# ==============================================================================

def norm(s: Any) -> str:
    """
    Normalizza testo “sporco”.
    - ftfy (se disponibile) per fix Unicode
    - unifica newline
    - comprime spazi, trim linee e risultato
    """
    if not isinstance(s, str):
        return ""
    if _HAS_FTFY:
        try:
            s = ftfy.fix_text(s)
        except Exception:
            pass
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    # rimuovi zero-width e simili
    s = s.replace("\u200b", "").replace("\ufeff", "")
    # comprimi spazi multipli orizzontali
    s = re.sub(r"[ \t]+", " ", s)
    # trim per-linea
    s = "\n".join(line.strip() for line in s.splitlines())
    return s.strip()


def is_noise(line: str) -> bool:
    """
    Heuristica semplice per scartare righe rumorose:
    - solo simboli/spazi
    - troppo corte
    - informative legali molto generiche (GDPR)
    """
    if not line:
        return True
    l = line.strip()
    if len(l) <= 1:
        return True
    if re.fullmatch(r"[\W_]+", l):
        return True
    if re.search(r"(autorizz\w*).*(trattament\w*).*(dati|personali)", l, re.I):
        return True
    return False


def dedupe_keep_order(items: List[Any], keyfunc=lambda x: str(x).lower()) -> List[Any]:
    """De-duplica mantenendo l’ordine della prima occorrenza."""
    seen = set()
    out: List[Any] = []
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
    """Accorcia una stringa a max_chars mantenendo parole intere quando possibile."""
    s = norm(s)
    if not s or len(s) <= max_chars:
        return s
    cut = max_chars - len(ellipsis)
    if cut <= 0:
        return ellipsis[:max_chars]
    i = s.rfind(" ", 0, cut)
    if i == -1 or i < int(cut * 0.6):
        return s[:cut].rstrip() + ellipsis
    return s[:i].rstrip() + ellipsis


# ==============================================================================
# Date (multilingua) — via dateparser (no hard-code mesi)
# ==============================================================================

_DATEPARSER_SETTINGS = {
    "PREFER_DAY_OF_MONTH": "first",
    "PREFER_DATES_FROM": "past",
    "RETURN_AS_TIMEZONE_AWARE": False,
    "DATE_ORDER": "DMY",   # riduce ambiguità EU
}

def _dt_to_iso(d) -> str:
    try:
        return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"
    except Exception:
        return ""


def parse_date_any(s: str) -> str:
    """
    Prova a interpretare date in molte lingue/formati con dateparser.
    Ritorna ISO 'YYYY-MM-DD' se possibile; altrimenti ''.
    """
    s0 = norm(s)
    if not s0:
        return ""
    if _HAS_DATEPARSER:
        try:
            d = dateparser.parse(s0, settings=_DATEPARSER_SETTINGS)
            if d:
                iso = _dt_to_iso(d)
                if iso:
                    return iso
        except Exception:
            pass
    # Fallback minimali (solo casi chiari)
    m = re.search(r"\b((?:19|20)\d{2})-(\d{2})-(\d{2})\b", s0)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return ""


def parse_range(s: str) -> Tuple[str, str]:
    """
    Intervalli tipo 'Gen 2020 - Mag 2022', '03/2020 to 2023', '2019 – present'.
    Restituisce (start_iso, end_iso) con end="" se presente/attuale.
    """
    s0 = norm(s).replace("—", "-").replace("–", "-")
    parts = re.split(r"\s*(?:-|to|a|al|fino a|hasta|bis|à)\s*", s0, maxsplit=1, flags=re.I)
    if len(parts) == 2:
        left, right = parts[0], parts[1]
        if re.search(r"\b(present|presente|current|oggi|now|attuale)\b", right, re.I):
            return parse_date_any(left), ""
        return parse_date_any(left), parse_date_any(right)
    return parse_date_any(s0), ""

# --- Localizzazione / traduzioni "senza liste" (paesi) ------------------------
from babel import Locale
import pycountry

def country_to_it(name_or_code: str) -> str:
    """
    Converte un nome/codice paese qualunque nel NOME ITALIANO ufficiale CLDR.
    Passi:
      1) normalizza a entity pycountry (via lookup: nome, alpha2, alpha3)
      2) prende alpha_2
      3) usa CLDR (Babel) per ottenere il nome in italiano
    Fallback: stringa ripulita originale.
    """
    s = norm(name_or_code)
    if not s:
        return ""
    # prova lookup robusto pycountry (nome / alias / codici)
    ent = None
    try:
        ent = pycountry.countries.lookup(s)  # può essere 'Italia', 'IT', 'ITA', 'Italy', 'deutschland'...
    except Exception:
        ent = None
    if not ent:
        return s
    alpha2 = getattr(ent, "alpha_2", None)
    if not alpha2:
        return s
    try:
        it = Locale.parse("it")
        # CLDR usa codici tipo 'IT', 'DE', 'GB' nella mappa territories
        label = it.territories.get(alpha2.upper(), "") or it.territories.get(alpha2.capitalize(), "")
        return label or s
    except Exception:
        return s

def nationality_to_it(text: str) -> str:
    """
    Tenta di 'italianizzare' una nazionalità passando per il Paese.
    Strategia:
      - se contiene una parola che pycountry riconosce come Paese → traduci quel Paese in IT
      - altrimenti, lascia il testo ripulito così com'è (evita traduzioni scorrette).
    Esempi: "Italian", "Française", "Deutsch", "Brazilian" -> "Italia", "Francia", "Germania", "Brasile"
    """
    s = norm(text)
    if not s:
        return ""
    # prova a trovare un Paese nel testo (pycountry.lookup su token e bigrammi)
    words = re.findall(r"[A-Za-zÀ-ÿ]+", s)
    # prova bigrammi prima (United States, Czech Republic, etc.)
    for i in range(len(words) - 1):
        cand = f"{words[i]} {words[i+1]}"
        try:
            ent = pycountry.countries.lookup(cand)
            if ent:
                return country_to_it(ent.name)
        except Exception:
            pass
    # poi singola parola
    for w in words:
        try:
            ent = pycountry.countries.lookup(w)
            if ent:
                return country_to_it(ent.name)
        except Exception:
            pass
    # nulla di riconoscibile: restituisci il testo pulito (meglio nessuna falsa traduzione)
    return s


# ==============================================================================
# Telefono (worldwide) — via phonenumbers
# ==============================================================================

def norm_phone(raw: str) -> str:
    """Normalizza velocemente un numero (tieni solo cifre, e '+' se iniziale)."""
    if not raw:
        return ""
    s = str(raw).strip()
    plus = s.startswith("+")
    digits = re.sub(r"\D", "", s)
    return f"+{digits}" if plus else digits


def phone_candidates(text: str) -> List[str]:
    """Estrae numeri validi dal testo e li ritorna in E.164 (de-duplicati)."""
    out: List[str] = []
    try:
        for match in phonenumbers.PhoneNumberMatcher(text or "", None):
            n = match.number
            if phonenumbers.is_valid_number(n):
                out.append(phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.E164))
    except Exception:
        pass
    return dedupe_keep_order(out)


def country_from_phone(e164: str) -> str:
    """Da numero E.164 → nome paese (ISO pycountry), altrimenti ''."""
    try:
        n = phonenumbers.parse(e164 or "", None)
        region = phonenumbers.region_code_for_number(n)  # 'IT', 'US', ...
        if region:
            c = pycountry.countries.get(alpha_2=region)
            if c:
                return getattr(c, "common_name", None) or c.name
    except Exception:
        pass
    return ""


# ==============================================================================
# Paesi & TLD (pycountry / tldextract) + inferenze
# ==============================================================================

def country_from_tld(url_or_email: str) -> str:
    """
    Deduce il paese dall'ultima label del TLD (se c'è un ccTLD).
    'example.co.uk' → 'United Kingdom'; 'site.com.br' → 'Brazil'
    """
    try:
        ext = tldextract.extract(url_or_email or "")
        suffix = (ext.suffix or "").lower()
        if not suffix:
            return ""
        last = suffix.split(".")[-1]
        if len(last) == 2:
            c = pycountry.countries.get(alpha_2=last.upper())
            if c:
                return getattr(c, "common_name", None) or c.name
    except Exception:
        pass
    return ""


def normalize_country(name_or_code: str) -> str:
    """
    Normalizza nomi/codici paese in nome canonico ISO (inglese).
    Accetta 'IT', 'ITA', 'Italia', 'Germany', ecc.
    """
    s = norm(name_or_code)
    if not s:
        return ""
    # codici
    c = pycountry.countries.get(alpha_2=s.upper())
    if c:
        return getattr(c, "common_name", None) or c.name
    c = pycountry.countries.get(alpha_3=s.upper())
    if c:
        return getattr(c, "common_name", None) or c.name
    # ripulisci punteggiatura (U.S.A. → USA)
    s2 = re.sub(r"[^\w ]+", " ", s).strip()
    try:
        c = pycountry.countries.lookup(s2)
        if c:
            return getattr(c, "common_name", None) or c.name
    except Exception:
        pass
    return s


def country_from_text(text: str) -> str:
    """
    Prova a riconoscere un paese dal testo libero con pycountry (lookup).
    Cerca bigrammi e singole parole capitalizzate comuni.
    """
    s = norm(text)
    if not s:
        return ""
    # codici espliciti
    for m in re.findall(r"\b([A-Z]{2,3})\b", s):
        iso = m.upper()
        c = pycountry.countries.get(alpha_2=iso) if len(iso) == 2 else None
        if c:
            return getattr(c, "common_name", None) or c.name
        c = pycountry.countries.get(alpha_3=iso) if len(iso) == 3 else None
        if c:
            return getattr(c, "common_name", None) or c.name

    words = re.findall(r"[A-Za-zÀ-ÿ]+", s)
    # bigrammi
    for i in range(len(words) - 1):
        cand = f"{words[i]} {words[i+1]}"
        try:
            c = pycountry.countries.lookup(cand)
            if c:
                return getattr(c, "common_name", None) or c.name
        except Exception:
            pass
    # singole parole
    for w in words:
        try:
            c = pycountry.countries.lookup(w)
            if c:
                return getattr(c, "common_name", None) or c.name
        except Exception:
            pass
    return ""


# ==============================================================================
# Regione “hint” per telefoni (alpha-2) — usata dal normalizer
# ==============================================================================

def guess_region_from_internal(internal: Dict[str, Any]) -> str:
    """
    Deduce il codice paese ISO-3166 alpha-2 più probabile per interpretare telefoni SENZA '+':
      1) dai numeri (telefono/cellulare) → regione del prefisso
      2) da TLD/email/sito/linkedin/github (ccTLD)
      3) da contatti.indirizzo.paese / anagrafica.luogo_nascita / anagrafica.nazionalita (testo)
    Ritorna es. 'IT', 'FR', ... oppure '' se non deducibile.
    """
    if not isinstance(internal, dict):
        return ""

    contatti = internal.get("contatti", {}) if isinstance(internal.get("contatti", {}), dict) else {}
    indir    = contatti.get("indirizzo", {}) if isinstance(contatti.get("indirizzo", {}), dict) else {}
    anag     = internal.get("anagrafica", {}) if isinstance(internal.get("anagrafica", {}), dict) else {}

    # 1) telefoni
    for key in ("telefono", "cellulare"):
        raw = contatti.get(key, "")
        try:
            if raw:
                n = phonenumbers.parse(str(raw), None)  # gestisce anche +XX
                if phonenumbers.is_valid_number(n):
                    rc = phonenumbers.region_code_for_number(n)  # 'IT'
                    if rc:
                        return rc
        except Exception:
            pass

    # 2) ccTLD da sorgenti web/email
    for key in ("email", "sito_web", "linkedin", "github"):
        v = contatti.get(key, "")
        name = country_from_tld(v) if v else ""
        if name:
            # mappa a alpha-2
            try:
                c = pycountry.countries.lookup(name)
                if c and getattr(c, "alpha_2", None):
                    return c.alpha_2
            except Exception:
                pass

    # 3) testo libero (paese/luogo/nazionalità)
    for src in (indir.get("paese", ""), anag.get("luogo_nascita", ""), anag.get("nazionalita", "")):
        name = country_from_text(src)
        if name:
            try:
                c = pycountry.countries.lookup(name)
                if c and getattr(c, "alpha_2", None):
                    return c.alpha_2
            except Exception:
                pass

    return ""