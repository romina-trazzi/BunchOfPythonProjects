# parsers.py — Parsing “layout-aware”, internazionale, senza liste hard-coded
# ------------------------------------------------------------------------------
# Entry point:
#   parse_text_to_internal(text: str, blocks: list[dict] | None, filename: str) -> dict
#
# Dipende solo da utils.py:
#   norm, is_noise, dedupe_keep_order,
#   parse_date_any, parse_range,
#   phone_candidates, country_from_phone, country_from_tld,
#   normalize_country, country_from_text
# ------------------------------------------------------------------------------

from __future__ import annotations

import re

from typing import Any, Dict, List, Tuple, Optional

from utils import (
    norm, is_noise, dedupe_keep_order,
    parse_date_any, parse_range,
    phone_candidates, country_from_phone, country_from_tld, normalize_country, country_from_text, 
    country_to_it, nationality_to_it
)

from unidecode import unidecode


# ==============================================================================
# Heuristic headings (no liste di alias)
#   - riga breve (< 60)
#   - niente numeri
#   - non può finire con : (etichetta)
#   - non può essere un contatto
#   - UPPERCASE o Title Case (>=70% parole capitalizzate)
#   - riga vuota prima o dopo
# ==============================================================================

def _is_heading(line: str) -> bool:
    s = norm(line)
    if not s or len(s) > 60:
        return False
    if s.endswith(":"):                     # ← blocca etichette tipo "Città:"
        return False
    if "@" in s or "://" in s or re.search(r"\d{5,}", s):
        return False
    words = re.findall(r"[^\W\d_][\wÀ-ÿ'-]*", s)
    if not words:
        return False
    cap_ratio = sum(w[:1].isupper() for w in words) / max(1, len(words))
    return s.isupper() or cap_ratio >= 0.7


# ==============================================================================
# Segmenta il testo in sezioni usando solo heading 'di forma' (no liste di alias).
# Regole chiave (demandate a _is_heading):
#   - 2..60 char, niente numeri dominanti
#   - no etichette (niente ':' finale)
#   - no email/url/telefoni
#   - case: ALLCAPS oppure ≥70% Title Case
#   - isolamento: riga vuota prima OPPURE dopo.
# ==============================================================================
   
def detect_sections(text: str) -> Dict[str, str]:
    """
    Segmentazione semplice:
      - un heading è una riga 'titolo' secondo _is_heading
      - consideriamo heading valido se c'è riga vuota PRIMA o DOPO
    """
    txt = norm(text)
    lines = txt.splitlines()
    idxs: List[int] = []
    for i, l in enumerate(lines):
        if not _is_heading(l):
            continue
        prev_blank = (i == 0) or (lines[i-1].strip() == "")
        next_blank = (i+1 < len(lines) and lines[i+1].strip() == "")
        if prev_blank or next_blank:
            idxs.append(i)

    if not idxs:
        return {"body": txt}

    sections: Dict[str, str] = {}
    for j, i in enumerate(idxs):
        title = norm(lines[i])
        start = i + 1
        end = idxs[j+1] if j + 1 < len(idxs) else len(lines)
        chunk = "\n".join(lines[start:end]).strip()
        if chunk:
            sections[title] = chunk
    return sections or {"body": txt}
    
    
# ==============================================================================
# Nome & Cognome (scoring multi-fonte: Layout, Email, LinkedIn, Filename) 
# ==============================================================================

_FILENAME_STOP = {"cv", "resume", "curriculum", "europass", "final", "draft", "copy"}

def _canonize_token(t: str) -> str:
    """Normalizza un token per confronto: strip, lowercase, unidecode."""
    return unidecode(t).strip().lower()

def _tokenize_basic(s: str) -> List[str]:
    """Tokenizzazione semplice: separa su ., _, -, spazi; rimuove cifre; solo alfabetici."""
    s = unidecode(norm(s))
    s = re.sub(r"\d+", "", s)
    parts = re.split(r"[.\-_\s]+", s)
    return [p for p in parts if p and p.isalpha() and len(p) >= 2]

def _slug_tokens(s: str) -> List[str]:
    return _tokenize_basic(s)[:4]

def _linkedin_tokens(url: str) -> Optional[List[str]]:
    if not url:
        return None
    m = re.search(r"linkedin\.com/(?:in|pub)/([A-Za-z0-9\-_\.]+)", url, re.I)
    if not m:
        return None
    toks = _slug_tokens(m.group(1))
    return toks if len(toks) >= 2 else None

def _email_tokens(email: str) -> Optional[List[str]]:
    if not email or "@" not in email:
        return None
    local = email.split("@", 1)[0]
    toks = _slug_tokens(local)
    return toks if len(toks) >= 2 else None

def _filename_tokens(fn: str) -> Optional[List[str]]:
    if not fn:
        return None
    s = re.sub(r"\.pdf$", "", fn, flags=re.I)
    s = re.sub(r"\(.*?\)", " ", s)          # es. "(luglio 2025)" → " "
    s = re.sub(r"[_\-]+", " ", s)
    parts = [p for p in re.split(r"\s+", unidecode(norm(s))) if p]
    clean = []
    for p in parts:
        pl = p.lower()
        if pl in _FILENAME_STOP:
            continue
        # NON rimuoviamo mesi/mesi-abbrev — richiesta esplicita
        if re.fullmatch(r"(19|20)\d{2}", pl):               # anni
            continue
        if re.fullmatch(r"v\d+(\.\d+)?", pl, flags=re.I):   # versioni
            continue
        clean.append(p)
    toks = [t for t in clean if t.isalpha() and len(t) >= 2][:4]
    return toks if len(toks) >= 2 else None

def _looks_like_person(toks: List[str]) -> bool:
    # 2–4 token alfabetici; niente numeri
    return 2 <= len(toks) <= 4 and all(t.isalpha() for t in toks)

def _canon_key(toks: List[str]) -> Tuple[str, ...]:
    # Chiave canonica per raggruppare: set ordinato dei token canonicalizzati
    return tuple(sorted({_canonize_token(t) for t in toks}))

def _equivalent_tokens(a: List[str], b: List[str]) -> bool:
    """
    Equivalenza inclusiva:
    - normalizza (lower+unidecode)
    - considera equivalenti se l'insieme di token di A è sottoinsieme di B o viceversa
    """
    A = { _canonize_token(t) for t in a }
    B = { _canonize_token(t) for t in b }
    if not A or not B:
        return False
    return A.issubset(B) or B.issubset(A)

def _titlecase_split(toks: List[str]) -> Tuple[str, str]:
    toks = [t.capitalize() for t in toks]
    if len(toks) == 2:
        return toks[0], toks[1]
    return toks[0], " ".join(toks[1:])

def infer_name(
    blocks: List[Dict[str, Any]] | None,
    email: str,
    linkedin: str,
    filename: str,
    section_titles: Optional[List[str]] = None
) -> Tuple[str, str]:
    """
    Consenso semplice tra LinkedIn, Email, Filename con equivalenza inclusiva.
    1) Raccoglie candidati.
    2) Gruppi per equivalenza (subset).
    3) Se un gruppo ha >=2 fonti → vince (prende la variante più corta).
    4) Altrimenti fallback: LinkedIn > Email > Filename.
    (Layout disattivato per ora.)
    """
    candidates: List[Tuple[str, List[str]]] = []

    li = _linkedin_tokens(linkedin)
    if li and _looks_like_person(li):
        candidates.append(("linkedin", li))

    em = _email_tokens(email)
    if em and _looks_like_person(em):
        candidates.append(("email", em))

    fn = _filename_tokens(filename)
    if fn and _looks_like_person(fn):
        candidates.append(("filename", fn))

    if not candidates:
        return "", ""

    # 2) Raggruppa per equivalenza inclusiva (non per chiave identica)
    groups: List[List[Tuple[str, List[str]]]] = []
    for cand in candidates:
        placed = False
        for g in groups:
            # confronta con il primo membro del gruppo (basta per stabilità)
            if _equivalent_tokens(cand[1], g[0][1]):
                g.append(cand)
                placed = True
                break
        if not placed:
            groups.append([cand])

    # 3) Gruppo migliore = max fonti; tie-break: contiene LinkedIn? poi Email?
    def group_score(g: List[Tuple[str, List[str]]]) -> Tuple[int, int, int]:
        sources = {src for src, _ in g}
        return (
            len(sources),
            1 if "linkedin" in sources else 0,
            1 if "email" in sources else 0,
        )

    best = max(groups, key=group_score)

    if len({src for src, _ in best}) >= 2:
        # consenso: scegli la variante con meno token 
        rep = min((toks for _, toks in best), key=len)
        return _titlecase_split(rep)

    # 4) Fallback deterministico: LinkedIn > Email > Filename
    for prefer in ("linkedin", "email", "filename"):
        for src, toks in candidates:
            if src == prefer:
                return _titlecase_split(toks)

    return "", ""



# ==============================================================================
# Contatti: pattern generici + deduzione paese (priorità: phone → TLD → testo)
# ==============================================================================

EMAIL_RX    = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
WEB_RX      = re.compile(r"(https?://[^\s]+|www\.[^\s]+)", re.I)
LINKEDIN_RX = re.compile(r"(https?://)?(www\.)?linkedin\.com/[^\s,;]+", re.I)
GITHUB_RX   = re.compile(r"(https?://)?(www\.)?github\.com/[^\s,;]+", re.I)

def _looks_like_address(line: str) -> bool:
    s = line.strip(" ,;.")
    if not (8 <= len(s) <= 120):
        return False
    if ":" in s:  # riga etichettata → no indirizzo
        return False
    tokens = s.split()
    has_digits = any(any(ch.isdigit() for ch in t) for t in tokens)
    # serve almeno una parola con iniziale maiuscola (Via, Rue, Street, ... o nome proprio)
    has_cap_word = any(re.match(r"[A-ZÀ-Ý][a-zà-ÿ]+", t) for t in tokens)
    # almeno 2 parole alfabetiche
    alpha_words = sum(1 for t in tokens if re.search(r"[A-Za-zÀ-ÿ]", t))
    return has_digits and has_cap_word and alpha_words >= 2

def _looks_like_city(line: str) -> Optional[str]:
    s = line.strip()
    if "@" in s or "://" in s or re.search(r"\d{2,}", s):
        return None
    # prendi max 2-3 parole capitalizzate
    m = re.match(r"^([A-Z][a-zÀ-ÿ]+(?: [A-Z][a-zÀ-ÿ]+){0,2})$", s)
    if not m:
        return None
    city = m.group(1).strip()
    return city if 2 <= len(city) <= 48 else None


def extract_contacts(text: str) -> Dict[str, Any]:
    out = {
        "indirizzo": {"via": "", "citta": "", "cap": "", "provincia": "", "paese": ""},
        "telefono": "", "cellulare": "",
        "email": "", "linkedin": "", "sito_web": "", "github": "",
    }

    txt = norm(text)
    all_lines = [l for l in txt.splitlines() if not is_noise(l)]

    # --- 2.1 Zona contatti: solo header (prime ~120 righe) o fino a titolo sezione "work/edu"
    cutoff_rx = re.compile(r"\b(experien|employment|impiego|beruf|lavor|career|history|work|educat|formaz|ausbild|stud|school|univers|degree|training)\b", re.I)
    cutoff = None
    for i, l in enumerate(all_lines[:200]):
        if _is_heading(l) and cutoff_rx.search(l.lower()):
            cutoff = i
            break
    lines = all_lines[: (cutoff if cutoff is not None else 120)]

    # --- 2.2 email / social / sito
    m = EMAIL_RX.search("\n".join(lines))
    if m:
        out["email"] = m.group(0)

    li = LINKEDIN_RX.search("\n".join(lines))
    if li:
        u = li.group(0)
        out["linkedin"] = u if u.startswith("http") else f"https://{u}"

    gh = GITHUB_RX.search("\n".join(lines))
    if gh:
        u = gh.group(0)
        out["github"] = u if u.startswith("http") else f"https://{u}"

    webs = [w.group(0) for w in WEB_RX.finditer("\n".join(lines))]
    webs = [w for w in webs if "linkedin.com" not in w and "github.com" not in w]
    if webs:
        w0 = webs[0]
        out["sito_web"] = w0 if w0.startswith("http") else f"https://{w0}"

    # --- 2.3 telefoni
    phones = phone_candidates("\n".join(lines))
    if phones:
        out["telefono"] = phones[0]
        if len(phones) > 1:
            out["cellulare"] = phones[1]

    # --- 2.4 paese: phone → TLD → testo (nella zona contatti)
    top = "\n".join(lines[:80])
    country = ""
    if out["telefono"]:
        country = country_from_phone(out["telefono"]) or ""
    if not country:
        for src in (out["sito_web"], out["email"], out["linkedin"], out["github"]):
            if src:
                country = country_from_tld(src)
                if country:
                    break
    if not country:
        country = country_from_text(top) or ""
    out["indirizzo"]["paese"] = normalize_country(country)

    # --- 2.5 CAP (evita anni tipo 2021). Se IT → 5 cifre, altrimenti 4–6 ma non 1900–2099
    cap = ""
    if out["indirizzo"]["paese"].lower() == "italy":
        mcap = re.search(r"\b(\d{5})\b", top)
        if mcap:
            cap = mcap.group(1)
    else:
        mcap = re.search(r"\b(\d{4,6})\b", top)
        if mcap:
            cand = mcap.group(1)
            if not (1900 <= int(cand) <= 2099):  # scarta anni
                cap = cand
    out["indirizzo"]["cap"] = cap

    # --- 2.6 città: label esplicite; fallback prudente; escludi nazioni
    city = ""
    city_lbl = re.compile(r"\b(citt[aà]|city)\s*[:\-]\s*([A-Z][A-Za-zÀ-ÿ' -]{1,48})\b", re.I)
    for l in lines[:120]:
        mm = city_lbl.search(l)
        if mm:
            cand = mm.group(2).strip()
            # es. "Genova (Italia)" → "Genova"
            cand = re.sub(r"\s*\(.+?\)$", "", cand).strip()
            city = cand
            break
    if not city:
        for l in lines[:120]:
            s = l.strip()
            if ":" in s:  # evita etichette "Paese: Italia"
                continue
            if len(s) > 48 or len(s.split()) > 3:
                continue
            c = _looks_like_city(s)
            if c:
                # escludi se è un paese (pycountry lo riconosce in country_from_text)
                if normalize_country(c) and normalize_country(c).lower() == c.lower():
                    continue
                city = c
                break
    out["indirizzo"]["citta"] = city

    # --- 2.7 via: escludi righe con più etichette "X: Y"
    labelish = re.compile(r"\b(paese|nazionalit[aà]|data di nascita|luogo di nascita|sesso|citt[aà]|indirizzo|address|email|telefono|phone)\b", re.I)
    for l in lines[:120]:
        if ":" in l and labelish.search(l):
            continue
        if _looks_like_address(l):
            out["indirizzo"]["via"] = l.strip(" ,;.")
            break

    return out


# ============================
# Anagrafica
# ============================

# Etichette multilingua (minimali) — niente liste lunghe, solo pattern diffusi
_LBL_DOB   = re.compile(r"(data\s*di\s*nascita|date\s*of\s*birth|dob|geburtsdatum|fecha\s*de\s*nacimiento|date\s*de\s*naissance)", re.I)
_LBL_POB   = re.compile(r"(luogo\s*di\s*nascita|place\s*of\s*birth|geburtsort|lugar\s*de\s*nacimiento|lieu\s*de\s*naissance)", re.I)
_LBL_NAT   = re.compile(r"(nazionalit[aà]|nationality|nationalit[yéè])", re.I)
_LBL_SEX   = re.compile(r"(sesso|sex|genre|geschlecht|sexo)", re.I)
_LBL_MSTAT = re.compile(r"(stato\s*civile|marital\s*status|familienstand|estado\s*civil|situation\s*familiale)", re.I)

def _clean_tail(v: str) -> str:
    """Rimuove separatori iniziali e code tra parentesi."""
    v = norm(v)
    v = re.sub(r"^\s*[:\-–—]\s*", "", v)
    v = re.sub(r"\s*\([^)]*\)\s*$", "", v)  # es. "(Italia)"
    return v.strip(" ,;:|")

def _first_date_token(s: str) -> str:
    """Isola la sottostringa che 'sembra' una data dalla riga."""
    s = norm(s)
    m = re.search(r"\b\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}\b", s)
    if m: return m.group(0)
    m = re.search(r"\b\d{1,2}[\/\-.]\d{4}\b", s)
    if m: return m.group(0)
    m = re.search(r"\b[A-Za-zÀ-ÿ]{3,15}\s+\d{4}\b", s)
    if m: return m.group(0)
    m = re.search(r"\b(19|20)\d{2}\b", s)
    if m: return m.group(0)
    return ""

def _pick_after_label(lines: List[str], lbl_rx: re.Pattern) -> Optional[str]:
    """Prende 'Label: valore' sulla stessa riga, altrimenti la riga successiva non-noise."""
    for i, l in enumerate(lines):
        if not lbl_rx.search(l):
            continue
        tail = re.split(lbl_rx, l, maxsplit=1)[-1]
        tail = _clean_tail(tail)
        if tail:
            return tail
        if i + 1 < len(lines):
            nxt = _clean_tail(lines[i + 1])
            if nxt and not is_noise(nxt):
                return nxt
    return None

def _format_date_it(iso_or_any: str) -> str:
    """'YYYY-MM-DD' -> 'DD/MM/YYYY'; se non è ISO, torna pulito com'è."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", iso_or_any)
    if not m:
        return iso_or_any
    return f"{m.group(3)}/{m.group(2)}/{m.group(1)}"

def _normalize_sex_minimal(val: str) -> str:
    """
    Regola minimale, senza liste:
    - prendi la prima lettera alfabetica; 'f' -> 'F', 'm' -> 'M'
    - altrimenti ritorna il valore pulito così com'è
    """
    s = norm(val)
    m = re.search(r"[A-Za-zÀ-ÿ]", s)
    if not m:
        return s
    first = m.group(0).lower()
    if first == 'f':
        return 'F'
    if first == 'm':
        return 'M'
    return s

def extract_personal_block(text: str) -> Dict[str, str]:
    """
    Ritorna sempre tutte le chiavi:
      - data_nascita in 'DD/MM/YYYY' se interpretabile,
      - luogo_nascita / nazionalita / stato_civile: testo pulito,
      - sesso: 'F'/'M' con regola minimale, altrimenti testo pulito.
    """
    lines = [l for l in norm(text).splitlines() if not is_noise(l)]

    # Data di nascita
    dob_raw = _pick_after_label(lines, _LBL_DOB)
    dob = ""
    if dob_raw:
        # isola il pezzo 'più da data' prima di passarlo al parser
        token = _first_date_token(dob_raw) or dob_raw
        dob_iso = parse_date_any(token)  # utils: ISO 'YYYY-MM-DD' o stringa pulita
        dob = _format_date_it(dob_iso)

    # Luogo di nascita
    pob = ""
    raw_pob = _pick_after_label(lines, _LBL_POB) or ""
    if raw_pob:
        raw_pob = _clean_tail(raw_pob)
        raw_pob = re.split(r"\b(paese|country|state|nation|citt[aà]|city)\b", raw_pob, maxsplit=1, flags=re.I)[0]
        pob = raw_pob.strip(" ,;")

    # Nazionalità (testo pulito, senza mapping/blacklist)
    nat = ""
    raw_nat = _pick_after_label(lines, _LBL_NAT) or ""
    if raw_nat:
        raw_nat = _clean_tail(raw_nat)
        raw_nat = re.split(r"\b(data|luogo|born|birth|citt[aà]|city|paese|country)\b", raw_nat, maxsplit=1, flags=re.I)[0]
        nat = raw_nat.strip(" ,;")

    # Sesso (normalizzazione minimale)
    sex_raw = _pick_after_label(lines, _LBL_SEX) or ""
    sex = _normalize_sex_minimal(sex_raw) if sex_raw else ""

    # Stato civile (testo pulito)
    mstat = ""
    raw_ms = _pick_after_label(lines, _LBL_MSTAT) or ""
    if raw_ms:
        mstat = _clean_tail(raw_ms)

    return {
        "data_nascita": dob,
        "luogo_nascita": pob or "",
        "nazionalita": nat or "",
        "sesso": sex,
        "stato_civile": mstat or "",
    }
    
# ==============================================================================
# Lingue (CEFR) — agnostico
# ==============================================================================

def _left_of_level(line: str) -> Optional[str]:
    m = re.search(rf"(.+?)\b(A1|A2|B1|B2|C1|C2)\b", line, re.I)
    if not m:
        return None
    return m.group(1).strip(" :–—-|\u2022").strip()

def extract_languages(section_text: str, all_text: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    txt = (section_text or all_text)
    lines = [l for l in norm(txt).splitlines() if not is_noise(l)]

    # con livello
    for ln in lines:
        left = _left_of_level(ln)
        if left:
            lvl = re.search(r"(A1|A2|B1|B2|C1|C2)", ln, re.I).group(1).upper()
            out.append({"lingua": left, "livello_scritto": lvl, "livello_parlato": lvl, "certificazioni": []})

    # senza livello: brevi righe capitalizzate (fallback prudente)
    if not out:
        for ln in lines:
            if len(ln) <= 24 and re.fullmatch(r"[^\d\W][\wÀ-ÿ' -]{1,23}", ln):
                words = ln.split()
                cap_ratio = sum(w[:1].isupper() for w in words) / max(1, len(words))
                if cap_ratio >= 0.5:
                    out.append({"lingua": ln.strip(), "livello_scritto": "", "livello_parlato": "", "certificazioni": []})

    # dedupe
    seen = set(); ded = []
    for it in out:
        key = it["lingua"].strip().lower()
        if key in seen: 
            continue
        seen.add(key)
        ded.append(it)

    return ded[:5] or [{"lingua": "", "livello_scritto": "", "livello_parlato": "", "certificazioni": []}]

# ==============================================================================
# Competenze — solo tokenizzazione; niente tassonomie
# ==============================================================================

def _tokenize_bullets(section_text: str, all_text: str) -> List[str]:
    txt = section_text or all_text
    raw = re.split(r"[•\u2022\-\u25CF,\n;]|  +", txt)
    return [norm(t) for t in raw if norm(t)]

def extract_skills(section_text: str, all_text: str) -> Dict[str, List[str]]:
    tokens = _tokenize_bullets(section_text, all_text)
    altre = [t for t in tokens if not is_noise(t) and len(t) <= 160]
    return {
        "linguaggi_programmazione": [],
        "framework": [],
        "database": [],
        "strumenti": [],
        "metodologie": [],
        "altre_competenze": dedupe_keep_order(altre)[:150],
    }

# ==============================================================================
# Esperienze & Istruzione — pattern strutturali, zero vocaboli
# ==============================================================================

def _paragraphs(section_text: str) -> List[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", section_text or "") if p.strip()][:60]

def _first_city(lines: List[str]) -> str:
    for l in lines[:3]:
        c = _looks_like_city(l)
        if c:
            return c
    return ""

def _first_range(lines: List[str]) -> Tuple[str, str]:
    # range (varie forme) o singola data
    for l in lines[:3]:
        m = re.search(
            r"(.{0,30})(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}|\d{1,2}[/\-.]\d{4}|\b[A-Za-zÀ-ÿ]{3,9}\s+\d{4}\b|\b(?:19|20)\d{2}\b)"
            r".{0,15}(?:-|–|—|to|a|al|fino a|hasta|bis|à).{0,15}"
            r"(\bpresente|current|oggi|now|attuale\b|\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}|\d{1,2}[/\-.]\d{4}|\b[A-Za-zÀ-ÿ]{3,9}\s+\d{4}\b|\b(?:19|20)\d{2}\b)",
            l, re.I)
        if m:
            return parse_range(m.group(0))
    for l in lines[:3]:
        d = parse_date_any(l)
        if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            return d, ""
    return "", ""

def extract_experience(section_text: str) -> List[Dict[str, Any]]:
    if not section_text:
        return [{
            "posizione": "", "azienda": "", "citta": "", "paese": "",
            "data_inizio": "", "data_fine": "", "descrizione": "",
            "responsabilita": [], "risultati_ottenuti": []
        }]

    out: List[Dict[str, Any]] = []
    for para in _paragraphs(section_text):
        lines = [l for l in para.splitlines() if not is_noise(l)]
        if not lines:
            continue

        header = lines[0]
        posizione, azienda = "", ""

        # Pattern neutri: "Titolo @ Azienda" oppure "Titolo - Azienda"
        if "@" in header:
            left, right = header.split("@", 1)
            posizione = left.strip(" -:|")
            azienda = right.strip(" -:|")
        elif " - " in header or " – " in header or " — " in header:
            parts = re.split(r"\s[–—-]\s", header, maxsplit=1)
            if len(parts) == 2:
                posizione, azienda = parts[0].strip(" -:|"), parts[1].strip(" -:|")
            else:
                posizione = header.strip(" -:|")
        else:
            posizione = header.strip(" -:|")

        data_inizio, data_fine = _first_range(lines)
        citta = _first_city(lines)
        descrizione = "\n".join(lines[1:]) if len(lines) > 1 else ""

        out.append({
            "posizione": posizione, "azienda": azienda, "citta": citta, "paese": "",
            "data_inizio": data_inizio, "data_fine": data_fine, "descrizione": descrizione,
            "responsabilita": [], "risultati_ottenuti": []
        })

    return out or [{
        "posizione": "", "azienda": "", "citta": "", "paese": "",
        "data_inizio": "", "data_fine": "", "descrizione": "",
        "responsabilita": [], "risultati_ottenuti": []
    }]

def extract_education(section_text: str) -> List[Dict[str, Any]]:
    if not section_text:
        return [{
            "titolo_studio": "", "istituto": "", "citta": "", "paese": "",
            "data_inizio": "", "data_fine": "", "voto": "", "descrizione": "", "tesi": ""
        }]

    out: List[Dict[str, Any]] = []
    for para in _paragraphs(section_text):
        lines = [l for l in para.splitlines() if not is_noise(l)]
        if not lines:
            continue

        header = lines[0]
        titolo, istituto = header.strip(" -:|"), ""

        # “Titolo @ Istituto” o “Titolo – Istituto”
        if "@" in header:
            left, right = header.split("@", 1)
            titolo = left.strip(" -:|")
            istituto = right.strip(" -:|")
        elif " - " in header or " – " in header or " — " in header:
            parts = re.split(r"\s[–—-]\s", header, maxsplit=1)
            if len(parts) == 2:
                titolo, istituto = parts[0].strip(" -:|"), parts[1].strip(" -:|")

        data_inizio, data_fine = _first_range(lines)
        citta = _first_city(lines)
        descrizione = "\n".join(lines[1:]) if len(lines) > 1 else ""

        out.append({
            "titolo_studio": titolo, "istituto": istituto, "citta": citta, "paese": "",
            "data_inizio": data_inizio, "data_fine": data_fine, "voto": "", "descrizione": descrizione, "tesi": ""
        })

    return out or [{
        "titolo_studio": "", "istituto": "", "citta": "", "paese": "",
        "data_inizio": "", "data_fine": "", "voto": "", "descrizione": "", "tesi": ""
    }]

# ==============================================================================
# Privacy / GDPR — pattern minimale
# ==============================================================================

def extract_privacy(text: str) -> str:
    for ln in [l for l in norm(text).splitlines() if not is_noise(l)]:
        if re.search(r"(autorizz\w*).*(trattament\w*).*(dati|personali)", ln, re.I):
            return ln.strip().rstrip(".,;: ")
    return ""

# ==============================================================================
# Orchestratore
# ==============================================================================

def parse_text_to_internal(text: str, blocks: List[Dict[str, Any]] | None, filename: str) -> Dict[str, Any]:
    # 1) sezioni
    sections = detect_sections(text)

    # 2) contatti
    contacts = extract_contacts(text)  # tua funzione già presente nel parser

    # 3) nome/cognome (consenso semplice; passa i titoli per evitare collisioni con headings)
    nome, cognome = infer_name(
        blocks=blocks,
        email=contacts.get("email", ""),
        linkedin=contacts.get("linkedin", ""),
        filename=filename or "",
        section_titles=list(sections.keys())
    )

    # 4) anagrafica “etichettata” conservativa
    personal = extract_personal_block(text)

    # 5) lingue (solo sezione dedicata)
    lang_section = ""
    for h, c in sections.items():
        if re.search(r"\blang(uage|uaggi|ues|ues|ues|ues|ues|ues|ues)?\b", h.lower()):
            lang_section = c; break
    languages = extract_languages(lang_section, lang_section or "") if lang_section else []

    # 6) skills (solo sezione dedicata)
    skills_section = ""
    for h, c in sections.items():
        if re.search(r"\b(skill|competenze|habilidades|comp[ée]tences|f[äa]higkeiten)\b", h.lower()):
            skills_section = c; break
    skills = extract_skills(skills_section, skills_section or "") if skills_section else {
        "linguaggi_programmazione": [],
        "framework": [],
        "database": [],
        "strumenti": [],
        "metodologie": [],
        "altre_competenze": [],
    }

    # 7) esperienze / education (radici ampie)
    exp_section = ""
    for h, c in sections.items():
        if re.search(r"\b(experien|employment|impiego|beruf|lavor|career|history|work)\b", h.lower()):
            exp_section = c; break
    edu_section = ""
    for h, c in sections.items():
        if re.search(r"\b(educat|formaz|ausbild|stud|school|univers|degree|training)\b", h.lower()):
            edu_section = c; break

    experiences = extract_experience(exp_section)
    education   = extract_education(edu_section)
    privacy     = extract_privacy(text)

    internal = {
        "anagrafica": {
            "nome": nome or "",
            "cognome": cognome or "",
            "data_nascita": personal.get("data_nascita",""),
            "luogo_nascita": personal.get("luogo_nascita",""),
            "nazionalita": personal.get("nazionalita",""),
            "sesso": personal.get("sesso",""),
            "stato_civile": personal.get("stato_civile",""),
        },
        "contatti": contacts,
        "istruzione": education,
        "esperienze_lavorative": experiences,
        "competenze_tecniche": skills,
        "competenze_linguistiche": languages,
        "competenze_trasversali": [],
        "certificazioni": [],
        "progetti": [],
        "pubblicazioni": [],
        "interessi": [],
        "patente": [],
        "autorizzazione_trattamento_dati": privacy,
        "disponibilita": {
            "trasferte": "",
            "trasferimento": "",
            "tipo_contratto_preferito": []
        },
        "_meta": {
            "section_titles": list(sections.keys())[:15]
        }
    }
    return internal