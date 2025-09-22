# parsers.py — Parsing “layout-aware”, internazionale, senza liste hard-coded
# ------------------------------------------------------------------------------
# Entry point:
#   parse_text_to_internal(text: str, blocks: list[dict] | None, filename: str) -> dict
#
# Dipende solo da utils.py:
#   norm, is_noise, dedupe_keep_order, parse_date_any, parse_range,
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
)

# ==============================================================================
# Sezioni: zero alias — solo heading “da layout”
#   - riga breve (< 60)
#   - UPPERCASE o Title Case (>=70% parole capitalizzate)
#   - riga vuota prima o dopo
# ==============================================================================

def _is_heading(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 60:
        return False
    words = [w for w in re.findall(r"[^\W\d_][\wÀ-ÿ'-]*", s)]
    if not words:
        return False
    all_upper = s == s.upper()
    cap_ratio = sum(w[:1].isupper() for w in words) / max(1, len(words))
    return all_upper or cap_ratio >= 0.7

def detect_sections(text: str) -> Dict[str, str]:
    txt = norm(text)
    lines = txt.splitlines()
    idxs: List[int] = []
    for i, l in enumerate(lines):
        if _is_heading(l):
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
# Contatti: pattern generici + deduzione paese via utils (no liste)
# ==============================================================================

EMAIL_RX    = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
WEB_RX      = re.compile(r"(https?://[^\s]+|www\.[^\s]+)", re.I)
LINKEDIN_RX = re.compile(r"(https?://)?(www\.)?linkedin\.com/[^\s,;]+", re.I)
GITHUB_RX   = re.compile(r"(https?://)?(www\.)?github\.com/[^\s,;]+", re.I)

def _looks_like_address(line: str) -> bool:
    """
    Indirizzo “universale” (euristica):
      - contiene ≥ 2 token alfabetici (parole)
      - contiene ≥ 1 token con cifre (numero civico o CAP mescolato)
      - lunghezza 10..120
    Nessun vocabolario di tipi via.
    """
    s = line.strip(" ,;.")
    if not (10 <= len(s) <= 120):
        return False
    tokens = s.split()
    alpha_words = sum(1 for t in tokens if re.search(r"[A-Za-zÀ-ÿ]", t))
    has_digits = any(any(ch.isdigit() for ch in t) for t in tokens)
    return alpha_words >= 2 and has_digits

def _looks_like_city(line: str) -> Optional[str]:
    """
    Città probabile: 1–2 parole capitalizzate, senza @/:///cifre lunghe.
    """
    s = line.strip()
    if "@" in s or "://" in s or re.search(r"\d{4,}", s):
        return None
    m = re.search(r"\b([A-Z][a-zÀ-ÿ]+(?: [A-Z][a-zÀ-ÿ]+)?)\b", s)
    if not m:
        return None
    city = m.group(1)
    if len(city.split()) <= 2:
        return city
    return None

def extract_contacts(text: str) -> Dict[str, Any]:
    out = {
        "indirizzo": {"via": "", "citta": "", "cap": "", "provincia": "", "paese": ""},
        "telefono": "",
        "cellulare": "",
        "email": "",
        "linkedin": "",
        "sito_web": "",
        "github": "",
    }

    txt = norm(text)
    lines = [l for l in txt.splitlines() if not is_noise(l)]

    # email / social / sito
    m = EMAIL_RX.search(txt)
    if m:
        out["email"] = m.group(0)

    li = LINKEDIN_RX.search(txt)
    if li:
        u = li.group(0)
        out["linkedin"] = u if u.startswith("http") else f"https://{u}"

    gh = GITHUB_RX.search(txt)
    if gh:
        u = gh.group(0)
        out["github"] = u if u.startswith("http") else f"https://{u}"

    webs = [w.group(0) for w in WEB_RX.finditer(txt)]
    webs = [w for w in webs if "linkedin.com" not in w and "github.com" not in w]
    if webs:
        w0 = webs[0]
        out["sito_web"] = w0 if w0.startswith("http") else f"https://{w0}"

    # telefoni
    phones = phone_candidates(txt)
    if phones:
        out["telefono"] = phones[0]
        if len(phones) > 1:
            out["cellulare"] = phones[1]

    # indirizzo “light”
    top = "\n".join(lines[:30])

    # CAP generico (4–6 cifre “isolate”)
    cap = re.search(r"\b(\d{4,6})\b", top)
    if cap:
        out["indirizzo"]["cap"] = cap.group(1)

    # via/strada (senza vocabolario): prendi la prima riga che “sembra” indirizzo
    for l in lines[:30]:
        if _looks_like_address(l):
            out["indirizzo"]["via"] = l.strip(" ,;.")
            break

    # città
    for l in lines[:30]:
        c = _looks_like_city(l)
        if c:
            out["indirizzo"]["citta"] = c
            break

    # paese: testo → telefono → TLD
    country = country_from_text(top) or (out["telefono"] and country_from_phone(out["telefono"])) or ""
    if not country:
        for src in (out["sito_web"], out["email"], out["linkedin"], out["github"]):
            if src:
                country = country_from_tld(src)
                if country:
                    break
    out["indirizzo"]["paese"] = normalize_country(country)
    return out

# ==============================================================================
# Nome & Cognome (layout → email → linkedin → filename) — zero blacklist
# ==============================================================================

def _plausible_heading_name(s: str) -> bool:
    if any(ch.isdigit() for ch in s):
        return False
    words = [w for w in s.split() if w]
    if not (1 <= len(words) <= 4):
        return False
    cap_ratio = sum(w[:1].isupper() for w in words) / max(1, len(words))
    return cap_ratio >= 0.75

def _split_fullname(s: str) -> Tuple[str, str]:
    parts = [p for p in norm(s).split() if p]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0].capitalize(), ""
    return parts[0].capitalize(), " ".join(p.capitalize() for p in parts[1:])

def infer_name(blocks: List[Dict[str, Any]] | None, email: str, linkedin: str, filename: str) -> Tuple[str, str]:
    # 1) header della prima pagina
    cands: List[Tuple[str, float]] = []
    for b in (blocks or []):
        if b.get("page") != 0:
            continue
        t = (b.get("text") or "").strip()
        if not t or not _plausible_heading_name(t):
            continue
        score = (1.0 / (1.0 + float(b.get("y0", 9999.0)))) + (float(b.get("x1", 0.0)) - float(b.get("x0", 0.0))) / 1000.0
        cands.append((t, score))
    cands.sort(key=lambda x: x[1], reverse=True)
    if cands:
        return _split_fullname(cands[0][0])

    # 2) email
    if email:
        loc = email.split("@", 1)[0]
        loc = re.sub(r"\d+", "", loc).replace("_", ".").replace("-", ".")
        toks = [t for t in loc.split(".") if t]
        if len(toks) >= 2:
            return toks[0].capitalize(), toks[1].capitalize()

    # 3) linkedin
    if linkedin:
        m = re.search(r"linkedin\.com/(?:in|pub)/([A-Za-z0-9\-_\.]+)", linkedin, re.I)
        if m:
            slug = m.group(1).replace("_", ".").replace("-", ".")
            toks = [t for t in slug.split(".") if t]
            if len(toks) >= 2:
                return toks[0].capitalize(), toks[1].capitalize()

    # 4) filename
    if filename:
        base = re.sub(r"\.pdf$", "", filename, flags=re.I)
        base = re.sub(r"\(.*?\)", " ", base)
        base = re.sub(r"[_\-]+", " ", base)
        cand = " ".join([w for w in base.split() if w])
        n, c = _split_fullname(cand)
        if n:
            return n, c

    return "", ""

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
    # Niente classificazione aggressiva: tutto in “altre_competenze”,
    # lasciamo ai layer successivi (o all’utente) la categorizzazione.
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

        # “Titolo @ Istituto” o “Titolo – Istituto” (generico)
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
    sections = detect_sections(text)

    contacts = extract_contacts(text)
    nome, cognome = infer_name(blocks, contacts.get("email", ""), contacts.get("linkedin", ""), filename)

    # Sezione “lingue”: prova a individuare col titolo (senza liste), altrimenti usa tutto
    lang_section = ""
    for h, c in sections.items():
        if re.search(r"\blang(?:uage|ues|uaggi|idiomas|langues|sprachen)\b", h.lower()):
            lang_section = c
            break
    languages = extract_languages(lang_section, text)

    # Sezione “skills”: idem
    skills_section = ""
    for h, c in sections.items():
        if re.search(r"\b(skill|competenze|habilidades|comp[ée]tences|f[äa]higkeiten)\b", h.lower()):
            skills_section = c
            break
    skills = extract_skills(skills_section, text)

    # Esperienze / istruzione: cerca intestazioni per *radici* (no liste), altrimenti vuoto
    exp_section = ""
    for h, c in sections.items():
        if re.search(r"\b(experien|employment|impiego|beruf|lavor)\b", h.lower()):
            exp_section = c
            break
    edu_section = ""
    for h, c in sections.items():
        if re.search(r"\b(educat|formaz|ausbild|stud)\b", h.lower()):
            edu_section = c
            break

    experiences = extract_experience(exp_section)
    education   = extract_education(edu_section)
    privacy     = extract_privacy(text)

    internal = {
        "anagrafica": {
            "nome": nome or "",
            "cognome": cognome or "",
            "data_nascita": "",
            "luogo_nascita": "",
            "nazionalita": "",
            "sesso": "",
            "stato_civile": "",
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
