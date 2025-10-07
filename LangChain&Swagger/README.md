# 🤖 LangChain RAG Engine

Un motore di **Retrieval-Augmented Generation (RAG)** avanzato che utilizza **Claude Sonnet** e **LangChain** per l'elaborazione intelligente di documenti e conversazioni AI.

## 📋 Indice
- [🚀 Panoramica](#-panoramica)
- [🔥 Caratteristiche Principali](#-caratteristiche-principali)
- [📁 Struttura del Progetto](#-struttura-del-progetto)
- [🛠️ Installazione e Setup](#️-installazione-e-setup)
- [🐳 Docker e Deployment](#-docker-e-deployment)
- [📖 API Documentation](#-api-documentation)
- [🧪 Testing](#-testing)
- [🔧 Configurazione](#-configurazione)
- [📚 Documentazione Tecnica](#-documentazione-tecnica)
- [🚀 Quick Start](#-quick-start)
- [🔒 Sicurezza](#-sicurezza)
- [📊 Monitoring](#-monitoring)
- [🤝 Contributi](#-contributi)

## 🚀 Panoramica

Un motore di **Retrieval-Augmented Generation (RAG)** completo che utilizza **Claude Sonnet** di Anthropic e il framework **LangChain**, completamente dockerizzato per un deployment production-ready.

Il sistema combina la potenza dell'AI generativa con la precisione del retrieval semantico, offrendo un'esperienza di conversazione intelligente basata sui tuoi documenti.


+------------------+       +-------------------------+
|   Client (UI)    | <---> | FastAPI + Swagger (/docs)|
+------------------+       +------------+------------+
                                      |
                                      v
                        +-------------+--------------+
                        |  API endpoints (src/api.py)|
                        +------+------+--------------+
                               |      |
                               |      v
                               |   Agents (src/agents.py)
                               v
                  Vector Store (Chroma)  <---  Embeddings (HF)
                       (src/vector_store.py)
                               |
                               v
                        Knowledge Base (chunk da PDF/TXT/DOCX)
                           (src/document_processor.py)


## 🔥 Caratteristiche Principali

### 🧠 **Motore RAG Avanzato**
- **LangChain Chains**: Implementazione con LCEL (LangChain Expression Language)
- **Retrieval Semantico**: Ricerca intelligente nei documenti usando embeddings
- **Claude Sonnet Integration**: Generazione di risposte di alta qualità
- **Memory Persistente**: Gestione della cronologia delle conversazioni
- **Custom Chains**: Workflow personalizzabili per casi d'uso specifici

### 🤖 **Agenti AI Specializzati**
- **🗣️ Conversation Agent**: Chat naturale con memoria del contesto
- **🔍 Research Agent**: Ricerca approfondita e analisi di documenti
- **📊 Analysis Agent**: Analisi dati e insights avanzati
- **💻 Coding Agent**: Assistenza per programmazione e debugging

### 📚 **Gestione Documenti Intelligente**
- **Multi-formato**: Supporto per PDF, DOCX, TXT, MD, CSV, JSON, XML, HTML
- **Chunking Intelligente**: Suddivisione ottimale dei documenti
- **Vector Store**: Database vettoriale con ChromaDB e FAISS
- **Batch Processing**: Caricamento di intere directory
- **Metadata Extraction**: Estrazione automatica di metadati

### ⚡ **API REST Completa**
- **FastAPI Framework**: Performance elevate e type safety
- **Swagger/OpenAPI**: Documentazione interattiva automatica
- **Streaming Responses**: Risposte in tempo reale
- **Session Management**: Gestione sessioni utente persistenti
- **Rate Limiting**: Controllo del traffico API
- **CORS Support**: Supporto cross-origin

### 🐳 **Deployment Production-Ready**
- **Docker Compose**: Orchestrazione multi-container
- **Nginx Reverse Proxy**: Load balancing e SSL termination
- **Redis Caching**: Cache distribuita per performance
- **Health Checks**: Monitoraggio automatico dello stato
- **Auto-scaling**: Scalabilità orizzontale
- **Backup Automatico**: Script di backup schedulati

## 📁 Struttura del Progetto

```
LangChain/
├── 📁 src/                          # Codice sorgente principale
│   ├── 🐍 api.py                    # FastAPI server con Swagger UI
│   ├── 🧠 rag_engine.py             # Motore RAG principale
│   ├── 🤖 agents.py                 # Agenti AI specializzati
│   ├── 💭 memory_manager.py         # Gestione memoria e sessioni
│   ├── 📄 document_processor.py     # Elaborazione documenti
│   ├── 🗃️ vector_store.py           # Database vettoriale
│   ├── 📋 models.py                 # Modelli Pydantic
│   ├── ⚙️ config.py                 # Configurazione sistema
│   └── 📖 swagger_config.py         # Configurazione Swagger UI
├── 📁 examples/                     # Esempi e test
│   ├── 🧪 test_api.py               # Test API endpoints
│   ├── 🔗 test_langchain_features.py # Test funzionalità LangChain
│   └── 🚀 test_rag_engine.py        # Test motore RAG
├── 📁 docs/                         # Documentazione
│   └── 📚 LANGCHAIN_GUIDE.md        # Guida LangChain completa
├── 📁 data/                         # Directory documenti
├── 📁 logs/                         # File di log
├── 📁 backups/                      # Backup automatici
├── 📁 ssl/                          # Certificati SSL
├── 🐳 Dockerfile                    # Container principale
├── 🐳 docker-compose.yml            # Orchestrazione servizi
├── 🌐 nginx.conf                    # Configurazione Nginx
├── 📦 requirements.txt              # Dipendenze Python
├── 🚀 start.py                      # Script di avvio
├── 🔧 .env.example                  # Template configurazione
└── 📖 README.md                     # Questa documentazione
```

### 🔍 Dettaglio File Principali

#### 📁 **src/** - Codice Sorgente
- **`api.py`**: Server FastAPI con 8 endpoint principali:
  - `/docs` - Swagger UI interattiva
  - `/health` - Health check sistema
  - `/query` - Query RAG standard
  - `/agent/query` - Query con agenti specializzati
  - `/upload/file` - Upload singolo file
  - `/upload/directory` - Upload directory completa
  - `/sessions` - Gestione sessioni utente
  - `/query/stream` - Streaming responses

- **`rag_engine.py`**: Motore RAG principale con:
  - Integrazione Claude Sonnet
  - LangChain Chains con LCEL
  - Retrieval semantico
  - Generazione contestuale

- **`agents.py`**: 4 agenti specializzati:
  - **ConversationAgent**: Chat generale
  - **ResearchAgent**: Ricerca approfondita
  - **AnalysisAgent**: Analisi dati
  - **CodingAgent**: Assistenza programmazione

- **`memory_manager.py`**: Gestione memoria con:
  - Cronologia conversazioni
  - Sessioni utente persistenti
  - Context management
  - LangChain Memory chains

#### 📁 **examples/** - Test e Esempi
- **`test_api.py`**: Test completi API endpoints
- **`test_langchain_features.py`**: Test funzionalità LangChain
- **`test_rag_engine.py`**: Test motore RAG

#### 🐳 **Docker e Deployment**
- **`Dockerfile`**: Container Python ottimizzato
- **`docker-compose.yml`**: Orchestrazione con Nginx + Redis
- **`nginx.conf`**: Reverse proxy e load balancing

## 🛠️ Installazione e Setup

### 📋 Prerequisiti
- **Python 3.11+**
- **Docker & Docker Compose**
- **Chiave API Anthropic**
- **8GB RAM** (raccomandati)

### 🚀 Installazione Rapida

1. **Clone del Repository**
```bash
git clone <repository-url>
cd LangChain
```

2. **Configurazione Environment**
```bash
cp .env.example .env
# Modifica .env con la tua ANTHROPIC_API_KEY
```

3. **Avvio con Docker**
```bash
docker-compose up -d
```

4. **Verifica Installazione**
```bash
curl http://localhost:8000/health
```

### 🔧 Installazione Manuale

1. **Setup Python Environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure
venv\Scripts\activate     # Windows
```

2. **Installazione Dipendenze**
```bash
pip install -r requirements.txt
```

3. **Avvio Applicazione**
```bash
python start.py
```

## 🐳 Docker e Deployment

### 🏗️ Architettura Container

```yaml
services:
  rag-engine:     # Applicazione principale
    ports: 8000
    volumes: ./data, ./logs
    
  nginx:          # Reverse proxy
    ports: 80, 443
    depends_on: rag-engine
    
  redis:          # Cache distribuita
    ports: 6379
    volumes: redis-data
```

### 🚀 Comandi Docker Utili

```bash
# Build e avvio
docker-compose up -d --build

# Visualizza logs
docker-compose logs -f rag-engine

# Restart servizio
docker-compose restart rag-engine

# Stop completo
docker-compose down

# Cleanup completo
docker-compose down -v --rmi all
```

### 🔄 Deployment Production

1. **Configurazione SSL**
```bash
# Copia certificati in ssl/
cp your-cert.pem ssl/
cp your-key.pem ssl/
```

2. **Environment Production**
```bash
cp .env.example .env.production
# Configura variabili production
```

3. **Deploy**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📖 API Documentation

### 🌐 Swagger UI
Accedi alla documentazione interattiva: **http://localhost:8000/docs**

### 📋 Endpoint Principali

#### 🏥 **Health Check**
```http
GET /health
```
Verifica stato sistema e dipendenze.

#### 🔍 **Query RAG**
```http
POST /query
Content-Type: application/json

{
  "query": "La tua domanda qui",
  "session_id": "optional-session-id"
}
```

#### 🤖 **Query con Agenti**
```http
POST /agent/query
Content-Type: application/json

{
  "query": "La tua domanda",
  "agent_type": "research|analysis|conversation|coding",
  "session_id": "optional-session-id"
}
```

#### 📤 **Upload Documenti**
```http
POST /upload/file
Content-Type: multipart/form-data

file: [your-document.pdf]
```

#### 📁 **Upload Directory**
```http
POST /upload/directory
Content-Type: application/json

{
  "directory_path": "/path/to/your/documents"
}
```

#### ⚡ **Streaming Response**
```http
POST /query/stream
Content-Type: application/json

{
  "query": "La tua domanda",
  "session_id": "optional-session-id"
}
```

#### 👥 **Gestione Sessioni**
```http
GET /sessions/{session_id}
DELETE /sessions/{session_id}
```

## 🧪 Testing

### 🔬 Test Automatici

```bash
# Test API endpoints
python examples/test_api.py

# Test funzionalità LangChain
python examples/test_langchain_features.py

# Test motore RAG
python examples/test_rag_engine.py
```

### 🧪 Test Manuali

1. **Test Health Check**
```bash
curl http://localhost:8000/health
```

2. **Test Query Semplice**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Ciao, come stai?"}'
```

3. **Test Upload File**
```bash
curl -X POST "http://localhost:8000/upload/file" \
  -F "file=@test-document.pdf"
```

## 🔧 Configurazione

### 📝 File .env

```env
# API Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key
API_HOST=0.0.0.0
API_PORT=8000

# LangChain Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langchain_api_key

# Vector Store Configuration
CHROMA_PERSIST_DIRECTORY=./data/chroma
COLLECTION_NAME=documents

# Memory Configuration
MEMORY_TYPE=conversation_buffer_window
MEMORY_K=10

# Agent Configuration
DEFAULT_AGENT_TYPE=conversation
AGENT_TEMPERATURE=0.7
AGENT_MAX_TOKENS=2000

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

### ⚙️ Configurazioni Avanzate

#### 🧠 **Memory Settings**
```python
# memory_manager.py
MEMORY_TYPES = {
    "buffer": ConversationBufferMemory,
    "window": ConversationBufferWindowMemory,
    "summary": ConversationSummaryMemory
}
```

#### 🤖 **Agent Settings**
```python
# agents.py
AGENT_CONFIGS = {
    "conversation": {"temperature": 0.7, "max_tokens": 2000},
    "research": {"temperature": 0.3, "max_tokens": 4000},
    "analysis": {"temperature": 0.1, "max_tokens": 3000},
    "coding": {"temperature": 0.2, "max_tokens": 4000}
}
```

## 📚 Documentazione Tecnica

### 🔗 **LangChain Integration**

Il sistema utilizza LangChain per:
- **Chains**: Workflow complessi con LCEL
- **Memory**: Gestione contesto conversazionale
- **Agents**: Agenti specializzati per task specifici
- **Retrievers**: Ricerca semantica nei documenti
- **Embeddings**: Rappresentazione vettoriale dei testi

### 🧠 **Architettura RAG**

```
User Query → Agent Selection → Memory Retrieval → Document Search → Context Assembly → Claude Sonnet → Response Generation → Memory Update → User Response
```

### 📊 **Vector Store**

- **ChromaDB**: Database vettoriale principale
- **Embeddings**: OpenAI text-embedding-ada-002
- **Chunking**: Recursive character splitting
- **Metadata**: Estrazione automatica da documenti

### 🔄 **Session Management**

- **Persistent Sessions**: Salvate in database locale
- **Memory Types**: Buffer, Window, Summary
- **Auto-cleanup**: Sessioni scadute rimosse automaticamente
- **Export/Import**: Backup e restore conversazioni

## 🚀 Quick Start

### 1️⃣ **Setup Iniziale**
```bash
git clone <repository>
cd LangChain
cp .env.example .env
# Configura ANTHROPIC_API_KEY in .env
```

### 2️⃣ **Avvio Rapido**
```bash
docker-compose up -d
```

### 3️⃣ **Prima Query**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Ciao! Come funzioni?"}'
```

### 4️⃣ **Upload Documenti**
```bash
curl -X POST "http://localhost:8000/upload/file" \
  -F "file=@your-document.pdf"
```

### 5️⃣ **Query sui Documenti**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Riassumi il documento che ho caricato"}'
```

## 🔒 Sicurezza

### 🛡️ **Best Practices Implementate**

- **API Key Protection**: Chiavi API mai esposte nei log
- **Input Validation**: Validazione rigorosa input utente
- **Rate Limiting**: Controllo traffico API
- **CORS Configuration**: Configurazione cross-origin sicura
- **SSL/TLS**: Supporto HTTPS in production
- **Container Security**: Container non-root

### 🔐 **Configurazione SSL**

```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    
    location / {
        proxy_pass http://rag-engine:8000;
    }
}
```

## 📊 Monitoring

### 📈 **Health Checks**

```bash
# Sistema generale
curl http://localhost:8000/health

# Componenti specifici
curl http://localhost:8000/health/detailed
```

### 📋 **Logging**

```python
# Configurazione logging
LOG_CONFIG = {
    "version": 1,
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": "./logs/app.log",
            "level": "INFO"
        }
    }
}
```

### 📊 **Metriche**

- **Response Time**: Tempo risposta API
- **Memory Usage**: Utilizzo memoria sistema
- **Document Count**: Numero documenti indicizzati
- **Session Count**: Sessioni attive
- **Error Rate**: Tasso errori

## 🤝 Contributi

### 🛠️ **Come Contribuire**

1. **Fork** del repository
2. **Crea** branch feature (`git checkout -b feature/amazing-feature`)
3. **Commit** modifiche (`git commit -m 'Add amazing feature'`)
4. **Push** branch (`git push origin feature/amazing-feature`)
5. **Apri** Pull Request

### 📋 **Guidelines**

- **Code Style**: Segui PEP 8 per Python
- **Documentation**: Documenta nuove funzionalità
- **Testing**: Aggiungi test per nuovo codice
- **Type Hints**: Usa type hints Python

### 🐛 **Bug Reports**

Usa il template GitHub Issues per segnalare bug:
- **Descrizione** del problema
- **Steps to reproduce**
- **Expected behavior**
- **Environment details**

---

## 📞 Supporto

- **📧 Email**: [your-email@domain.com]
- **🐛 Issues**: [GitHub Issues](link-to-issues)
- **📖 Docs**: [Documentation](link-to-docs)
- **💬 Discord**: [Community Discord](link-to-discord)

---

**Sviluppato con ❤️ usando Claude Sonnet e LangChain**