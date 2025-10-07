"""
Test script per le funzionalità LangChain avanzate del motore RAG.

Questo script dimostra l'utilizzo di:
- Agenti specializzati (conversation, research, analysis, coding)
- Gestione memoria e sessioni
- Catene personalizzate
- Cronologia conversazioni

Autore: RAG Engine Team
Data: 2024
"""

import os
import sys
import tempfile
from pathlib import Path

# Aggiungi il percorso src al PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent / "src"))

from rag_engine import RAGEngine
from config import settings

def create_sample_document():
    """Crea un documento di esempio per i test"""
    content = """
    # Guida all'Intelligenza Artificiale e Machine Learning
    
    ## Introduzione
    L'intelligenza artificiale (AI) è una tecnologia rivoluzionaria che sta trasformando 
    il modo in cui lavoriamo e viviamo. Il machine learning è un sottoinsieme dell'AI 
    che permette ai computer di apprendere senza essere esplicitamente programmati.
    
    ## Tecnologie Principali
    
    ### Deep Learning
    Il deep learning utilizza reti neurali artificiali con molti strati per 
    riconoscere pattern complessi nei dati.
    
    ### Natural Language Processing (NLP)
    L'NLP permette ai computer di comprendere e generare linguaggio umano.
    
    ### Computer Vision
    La computer vision consente ai computer di interpretare e analizzare immagini.
    
    ## Applicazioni Pratiche
    - Assistenti virtuali
    - Riconoscimento vocale
    - Traduzione automatica
    - Diagnosi medica
    - Veicoli autonomi
    
    ## Sfide e Considerazioni Etiche
    L'AI presenta sfide importanti come la privacy dei dati, 
    la trasparenza degli algoritmi e l'impatto sul lavoro.
    """
    
    # Crea un file temporaneo
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(content)
        return f.name

def test_agents(rag_engine, session_id="langchain_test"):
    """Test degli agenti LangChain specializzati"""
    print("\n" + "="*60)
    print("🧠 TEST AGENTI LANGCHAIN")
    print("="*60)
    
    # Test agente di conversazione
    print("\n🗣️ Test Agente di Conversazione:")
    print("-" * 40)
    conv_result = rag_engine.query_with_agent(
        "Ciao! Puoi farmi un riassunto dei documenti caricati?",
        session_id=session_id,
        agent_type="conversation"
    )
    print(f"Risposta: {conv_result['answer'][:200]}...")
    
    # Test agente di ricerca
    print("\n🔍 Test Agente di Ricerca:")
    print("-" * 40)
    research_result = rag_engine.query_with_agent(
        "Fai una ricerca approfondita sulle tecnologie di AI menzionate",
        session_id=session_id,
        agent_type="research"
    )
    print(f"Risposta: {research_result['answer'][:200]}...")
    
    # Test agente di analisi
    print("\n📊 Test Agente di Analisi:")
    print("-" * 40)
    analysis_result = rag_engine.query_with_agent(
        "Analizza in dettaglio le applicazioni pratiche dell'AI",
        session_id=session_id,
        agent_type="analysis"
    )
    print(f"Risposta: {analysis_result['answer'][:200]}...")
    
    return [conv_result, research_result, analysis_result]

def test_custom_chains(rag_engine, session_id="custom_chain_test"):
    """Test delle catene personalizzate"""
    print("\n" + "="*60)
    print("🔧 TEST CATENE PERSONALIZZATE")
    print("="*60)
    
    # Catena per analisi tecnica
    print("\n⚙️ Catena per Analisi Tecnica:")
    print("-" * 40)
    tech_prompt = """
    Sei un esperto analista tecnico. Analizza il seguente contesto e fornisci 
    una valutazione tecnica dettagliata.
    
    Contesto: {context}
    Domanda: {input}
    
    Analisi tecnica dettagliata:
    """
    
    tech_result = rag_engine.create_custom_chain(
        prompt_template=tech_prompt,
        query="Quali sono le tecnologie più promettenti menzionate?",
        session_id=session_id
    )
    print(f"Risposta: {tech_result['answer'][:200]}...")
    
    # Catena per riassunto esecutivo
    print("\n📋 Catena per Riassunto Esecutivo:")
    print("-" * 40)
    summary_prompt = """
    Sei un consulente senior. Crea un riassunto esecutivo basato sul contesto fornito.
    
    Contesto: {context}
    Richiesta: {input}
    
    Riassunto esecutivo:
    """
    
    summary_result = rag_engine.create_custom_chain(
        prompt_template=summary_prompt,
        query="Crea un riassunto esecutivo sui contenuti",
        session_id=session_id
    )
    print(f"Risposta: {summary_result['answer'][:200]}...")
    
    return [tech_result, summary_result]

def test_memory_management(rag_engine):
    """Test della gestione memoria e sessioni"""
    print("\n" + "="*60)
    print("💭 TEST GESTIONE MEMORIA E SESSIONI")
    print("="*60)
    
    # Lista sessioni attive
    print("\n📋 Sessioni Attive:")
    print("-" * 40)
    sessions = rag_engine.get_session_list()
    print(f"Sessioni trovate: {sessions['session_count']}")
    for session in sessions['sessions']:
        print(f"  - {session}")
    
    # Cronologia conversazione
    print("\n📚 Cronologia Conversazione (langchain_test):")
    print("-" * 40)
    history = rag_engine.get_conversation_history("langchain_test")
    if history['success']:
        print(f"Messaggi nella cronologia: {history['message_count']}")
        for i, msg in enumerate(history['history'][:3]):  # Mostra solo i primi 3
            print(f"  {i+1}. {msg['type']}: {msg['content'][:100]}...")
    
    # Test pulizia cronologia
    print("\n🧹 Test Pulizia Cronologia:")
    print("-" * 40)
    cleanup_result = rag_engine.clear_conversation_history("custom_chain_test")
    print(f"Pulizia cronologia: {'✅ Successo' if cleanup_result else '❌ Fallito'}")
    
    return sessions, history

def test_streaming(rag_engine, session_id="streaming_test"):
    """Test dello streaming delle risposte"""
    print("\n" + "="*60)
    print("🌊 TEST STREAMING RISPOSTE")
    print("="*60)
    
    print("\n📡 Streaming Query:")
    print("-" * 40)
    print("Domanda: Spiegami il deep learning in modo semplice")
    print("Risposta in streaming:")
    
    try:
        for chunk in rag_engine.stream_query(
            "Spiegami il deep learning in modo semplice",
            session_id=session_id
        ):
            if isinstance(chunk, dict) and 'content' in chunk:
                print(chunk['content'], end='', flush=True)
            elif isinstance(chunk, str):
                print(chunk, end='', flush=True)
        print("\n")
    except Exception as e:
        print(f"❌ Errore nello streaming: {str(e)}")

def main():
    """Funzione principale per testare le funzionalità LangChain"""
    print("🚀 AVVIO TEST FUNZIONALITÀ LANGCHAIN")
    print("="*60)
    
    # Verifica chiave API
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ERRORE: ANTHROPIC_API_KEY non configurata!")
        print("Configura la chiave API nel file .env")
        return
    
    try:
        # Inizializza il motore RAG
        print("\n🔧 Inizializzazione motore RAG...")
        rag_engine = RAGEngine()
        print("✅ Motore RAG inizializzato con successo!")
        
        # Crea e carica documento di esempio
        print("\n📄 Creazione documento di esempio...")
        doc_path = create_sample_document()
        
        try:
            # Carica il documento
            result = rag_engine.add_document(doc_path)
            if result['success']:
                print(f"✅ Documento caricato: {result['message']}")
            else:
                print(f"❌ Errore caricamento: {result['message']}")
                return
            
            # Informazioni collezione
            info = rag_engine.get_collection_info()
            print(f"📊 Documenti nella collezione: {info['document_count']}")
            
            # Test delle funzionalità LangChain
            test_agents(rag_engine)
            test_custom_chains(rag_engine)
            test_memory_management(rag_engine)
            test_streaming(rag_engine)
            
            print("\n" + "="*60)
            print("🎉 TUTTI I TEST COMPLETATI CON SUCCESSO!")
            print("="*60)
            
            # Statistiche finali
            final_info = rag_engine.get_collection_info()
            final_sessions = rag_engine.get_session_list()
            
            print(f"\n📊 Statistiche Finali:")
            print(f"  - Documenti: {final_info['document_count']}")
            print(f"  - Sessioni attive: {final_sessions['session_count']}")
            print(f"  - Agenti abilitati: {'✅' if settings.enable_agents else '❌'}")
            print(f"  - Memoria abilitata: {'✅' if settings.enable_memory else '❌'}")
            
        finally:
            # Pulizia
            try:
                os.unlink(doc_path)
                print(f"\n🧹 File temporaneo rimosso: {doc_path}")
            except:
                pass
                
    except Exception as e:
        print(f"\n❌ ERRORE DURANTE I TEST: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()