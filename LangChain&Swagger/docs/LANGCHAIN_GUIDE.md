# 🦜 Guida LangChain - Documentazione Tecnica

Questa guida fornisce una panoramica completa delle funzionalità LangChain implementate nel motore RAG.

## 📋 Indice

1. [Architettura LangChain](#architettura-langchain)
2. [Agenti Specializzati](#agenti-specializzati)
3. [Gestione Memoria](#gestione-memoria)
4. [Catene Personalizzate](#catene-personalizzate)
5. [API Endpoints](#api-endpoints)
6. [Configurazione Avanzata](#configurazione-avanzata)
7. [Best Practices](#best-practices)

## 🏗️ Architettura LangChain

### Componenti Principali

```
RAGEngine
├── MemoryManager          # Gestione sessioni e cronologia
├── RAGAgentManager        # Coordinamento agenti
├── ConversationChain      # Catena conversazionale
└── Custom Chains          # Catene personalizzate
```

### Flusso di Elaborazione

1. **Input Query** → Analisi tipo richiesta
2. **Agent Selection** → Scelta agente appropriato
3. **Memory Retrieval** → Recupero contesto sessione
4. **Document Search** → Ricerca nei documenti
5. **Response Generation** → Generazione risposta
6. **Memory Update** → Aggiornamento cronologia

## 🧠 Agenti Specializzati

### Agente di Conversazione (`conversation`)

**Scopo:** Conversazioni naturali e interattive
**Tools:** Document search, conversation history
**Prompt:** Ottimizzato per dialoghi fluidi

```python
# Esempio utilizzo
result = rag_engine.query_with_agent(
    "Ciao! Come posso aiutarti oggi?",
    agent_type="conversation",
    session_id="user_123"
)
```

### Agente di Ricerca (`research`)

**Scopo:** Ricerche approfondite e analisi
**Tools:** Multi-strategy search, web search (opzionale), document analysis
**Prompt:** Focalizzato su ricerca sistematica

```python
# Esempio utilizzo
result = rag_engine.query_with_agent(
    "Fai una ricerca completa sui trend dell'AI nel 2024",
    agent_type="research",
    session_id="research_001"
)
```

### Agente di Analisi (`analysis`)

**Scopo:** Analisi dettagliate e insights
**Tools:** Document analysis, statistical tools
**Prompt:** Orientato all'analisi critica

```python
# Esempio utilizzo
result = rag_engine.query_with_agent(
    "Analizza i pro e contro delle tecnologie discusse",
    agent_type="analysis",
    session_id="analysis_001"
)
```

### Agente di Coding (`coding`)

**Scopo:** Assistenza nella programmazione
**Tools:** Code search, code execution (se abilitato)
**Prompt:** Specializzato per sviluppo software

```python
# Esempio utilizzo (se abilitato)
result = rag_engine.query_with_agent(
    "Scrivi una funzione Python per elaborare i dati",
    agent_type="coding",
    session_id="dev_001"
)
```

## 💭 Gestione Memoria

### Architettura Memoria

```
MemoryManager
├── SessionChatMessageHistory  # Cronologia per sessione
├── Session Management         # Gestione ciclo vita sessioni
├── Automatic Cleanup         # Pulizia automatica
└── Import/Export             # Backup e ripristino
```

### Tipi di Memoria

#### 1. Memoria di Sessione
- **Persistente:** Salvata su file
- **Scadenza:** Configurabile (default: 24 ore)
- **Formato:** JSON strutturato

#### 2. Memoria Conversazionale
- **Buffer:** Ultimi N messaggi
- **Summary:** Riassunto conversazioni lunghe
- **Context:** Mantenimento contesto

### Gestione Sessioni

```python
# Lista sessioni attive
sessions = rag_engine.get_session_list()

# Cronologia specifica sessione
history = rag_engine.get_conversation_history("session_id")

# Pulizia cronologia
rag_engine.clear_conversation_history("session_id")

# Eliminazione sessione
rag_engine.delete_session("session_id")
```

## 🔧 Catene Personalizzate

### Creazione Catene Custom

Le catene personalizzate permettono di definire prompt e logiche specifiche:

```python
# Prompt personalizzato
custom_prompt = """
Sei un esperto {expertise}. Analizza il seguente contesto:

Contesto: {context}
Domanda: {input}

Fornisci una risposta dettagliata come {expertise}:
"""

# Utilizzo catena
result = rag_engine.create_custom_chain(
    prompt_template=custom_prompt,
    query="Analizza questo documento",
    session_id="custom_001",
    expertise="consulente finanziario"  # Variabile personalizzata
)
```

### Template Variabili

Le catene supportano variabili dinamiche:
- `{context}` - Contesto dai documenti
- `{input}` - Query dell'utente
- `{history}` - Cronologia conversazione
- Variabili personalizzate via `**kwargs`

## 🌐 API Endpoints

### Endpoints LangChain

#### Agent Query
```http
POST /agent/query
Content-Type: application/json

{
    "query": "La tua domanda",
    "agent_type": "conversation|research|analysis|coding",
    "session_id": "optional_session_id"
}
```

#### Custom Chain
```http
POST /custom-chain
Content-Type: application/json

{
    "prompt_template": "Il tuo prompt con {context} e {input}",
    "query": "La tua domanda",
    "session_id": "optional_session_id"
}
```

#### Session Management
```http
# Lista sessioni
GET /sessions

# Cronologia sessione
GET /sessions/{session_id}/history

# Pulizia cronologia
DELETE /sessions/{session_id}/history

# Eliminazione sessione
DELETE /sessions/{session_id}
```

#### Streaming
```http
POST /query/stream
Content-Type: application/json

{
    "query": "La tua domanda",
    "session_id": "optional_session_id"
}
```

## ⚙️ Configurazione Avanzata

### Variabili Ambiente

```bash
# Funzionalità LangChain
ENABLE_AGENTS=true
ENABLE_MEMORY=true
ENABLE_CODE_EXECUTION=false
ENABLE_WEB_SEARCH=false

# Gestione Sessioni
SESSION_TIMEOUT_HOURS=24
MAX_SESSIONS=100

# Agenti
AGENT_MAX_ITERATIONS=10
AGENT_VERBOSE=false
```

### Configurazione Agenti

```python
# In config.py
class Settings:
    # Configurazione agenti
    agent_max_iterations: int = 10
    agent_verbose: bool = False
    
    # Tools disponibili per agente
    conversation_tools = ["document_search", "conversation_history"]
    research_tools = ["multi_search", "document_analysis", "web_search"]
    analysis_tools = ["document_analysis", "statistical_analysis"]
    coding_tools = ["code_search", "code_execution"]
```

## 📚 Best Practices

### 1. Gestione Sessioni

```python
# ✅ Buona pratica: ID sessione significativi
session_id = f"user_{user_id}_{timestamp}"

# ✅ Pulizia periodica
if session_expired:
    rag_engine.delete_session(session_id)
```

### 2. Scelta Agenti

```python
# ✅ Agente appropriato per il task
if "analizza" in query.lower():
    agent_type = "analysis"
elif "cerca" in query.lower():
    agent_type = "research"
else:
    agent_type = "conversation"
```

### 3. Prompt Engineering

```python
# ✅ Prompt strutturato e chiaro
prompt = """
Ruolo: {role}
Contesto: {context}
Task: {task}

Istruzioni specifiche:
1. Analizza il contesto fornito
2. Rispondi in modo {style}
3. Includi esempi se pertinenti

Domanda: {input}
Risposta:
"""
```

### 4. Error Handling

```python
# ✅ Gestione errori robusta
try:
    result = rag_engine.query_with_agent(query, agent_type="research")
    if not result.get('success', True):
        # Fallback a agente base
        result = rag_engine.query_with_agent(query, agent_type="conversation")
except Exception as e:
    logger.error(f"Agent error: {e}")
    # Fallback a query standard
    result = rag_engine.query(query)
```

### 5. Performance

```python
# ✅ Streaming per risposte lunghe
for chunk in rag_engine.stream_query(query):
    yield chunk

# ✅ Limitazione sessioni
if session_count > MAX_SESSIONS:
    cleanup_old_sessions()
```

## 🔍 Debugging e Monitoring

### Logging

```python
# Abilita logging dettagliato
AGENT_VERBOSE=true

# Log personalizzati
import logging
logger = logging.getLogger("langchain.agents")
logger.setLevel(logging.DEBUG)
```

### Metriche

```python
# Monitoraggio performance
metrics = {
    "agent_calls": agent_manager.call_count,
    "session_count": memory_manager.active_sessions,
    "avg_response_time": performance_tracker.avg_time
}
```

## 🚀 Esempi Avanzati

### Multi-Agent Workflow

```python
# Workflow ricerca → analisi → conversazione
research_result = rag_engine.query_with_agent(
    "Ricerca informazioni su AI", 
    agent_type="research"
)

analysis_result = rag_engine.query_with_agent(
    f"Analizza questi risultati: {research_result['answer']}", 
    agent_type="analysis"
)

final_result = rag_engine.query_with_agent(
    "Riassumi l'analisi in modo conversazionale", 
    agent_type="conversation"
)
```

### Chain Composition

```python
# Catena composta per analisi completa
analysis_chain = """
Fase 1 - Comprensione: {context}
Fase 2 - Analisi: {input}
Fase 3 - Sintesi: Combina comprensione e analisi
Fase 4 - Raccomandazioni: Suggerimenti pratici

Risultato finale:
"""

result = rag_engine.create_custom_chain(
    prompt_template=analysis_chain,
    query="Analizza la strategia aziendale",
    session_id="strategic_analysis"
)
```

---

**Nota:** Questa documentazione è in continua evoluzione. Per aggiornamenti e nuove funzionalità, consulta il repository del progetto.