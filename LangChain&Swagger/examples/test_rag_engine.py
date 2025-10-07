"""
Script di esempio per testare il motore RAG
"""
import sys
import os
import asyncio
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from rag_engine import RAGEngine
from config import settings


async def main():
    """Funzione principale di test"""
    print("🚀 Inizializzazione del motore RAG con Claude Sonnet...")
    
    try:
        # Inizializza il motore RAG
        rag = RAGEngine()
        print("✅ Motore RAG inizializzato con successo!")
        
        # Test 1: Informazioni sulla collezione
        print("\n📊 Informazioni sulla collezione:")
        info = rag.get_collection_info()
        print(json.dumps(info, indent=2, ensure_ascii=False))
        
        # Test 2: Aggiungi un documento di esempio (se esiste)
        example_text = """
        LangChain è un framework per lo sviluppo di applicazioni basate su modelli di linguaggio di grandi dimensioni (LLM).
        
        Caratteristiche principali di LangChain:
        1. Catene (Chains): Combinano più componenti per creare applicazioni complesse
        2. Agenti (Agents): Utilizzano LLM per decidere quali azioni intraprendere
        3. Memoria (Memory): Mantiene lo stato tra le chiamate
        4. Retrieval: Integra fonti di dati esterne
        
        LangChain supporta diversi provider di LLM come OpenAI, Anthropic, Hugging Face e molti altri.
        Il framework è progettato per essere modulare e facilmente estensibile.
        """
        
        # Crea un file di esempio temporaneo
        temp_file = Path("temp_example.txt")
        temp_file.write_text(example_text, encoding='utf-8')
        
        print("\n📄 Aggiunta documento di esempio...")
        result = rag.add_documents_from_file(str(temp_file))
        print(f"✅ Risultato: {result['message']}")
        print(f"📊 Documenti aggiunti: {result['documents_added']}")
        
        # Pulisci il file temporaneo
        temp_file.unlink()
        
        # Test 3: Query di esempio
        print("\n❓ Test di query...")
        questions = [
            "Cos'è LangChain?",
            "Quali sono le caratteristiche principali di LangChain?",
            "Quali provider di LLM supporta LangChain?",
            "Come funziona la memoria in LangChain?"
        ]
        
        for question in questions:
            print(f"\n🔍 Domanda: {question}")
            response = rag.query(question, include_sources=True)
            
            if response['success']:
                print(f"💬 Risposta: {response['answer']}")
                print(f"⏱️ Tempo di risposta: {response['response_time_seconds']:.2f}s")
                if response.get('sources'):
                    print(f"📚 Fonti utilizzate: {response['num_sources']}")
            else:
                print(f"❌ Errore: {response['message']}")
        
        # Test 4: Ricerca di documenti simili
        print("\n🔎 Test ricerca documenti simili...")
        similar_docs = rag.get_similar_documents("framework per LLM", k=3)
        print(f"📋 Trovati {len(similar_docs)} documenti simili")
        
        for i, doc in enumerate(similar_docs, 1):
            print(f"\n{i}. Score: {doc['similarity_score']:.4f}")
            print(f"   Contenuto: {doc['content'][:200]}...")
        
        # Test 5: Test funzionalità LangChain (se abilitate)
        if hasattr(rag, 'agent_manager') and rag.agent_manager:
            print("\n🤖 Test Agenti LangChain...")
            
            # Test agente di conversazione
            print("\n💬 Test Agente Conversazione:")
            agent_response = rag.query_with_agent(
                "Riassumi le caratteristiche principali di LangChain",
                session_id="test_session",
                agent_type="conversation"
            )
            if agent_response['success']:
                print(f"🤖 Risposta agente: {agent_response['answer']}")
            
            # Test agente di ricerca
            print("\n🔍 Test Agente Ricerca:")
            research_response = rag.query_with_agent(
                "Analizza in dettaglio i componenti di LangChain",
                session_id="test_session",
                agent_type="research"
            )
            if research_response['success']:
                print(f"🔬 Risposta ricerca: {research_response['answer']}")
            
            # Test catena personalizzata
            print("\n⛓️ Test Catena Personalizzata:")
            custom_response = rag.create_custom_chain(
                prompt_template="Sei un esperto di AI. Analizza: {context}\nDomanda: {input}\nRisposta dettagliata:",
                query="Quali sono i vantaggi di LangChain?",
                session_id="custom_session"
            )
            if custom_response['success']:
                print(f"🔗 Risposta catena: {custom_response['answer']}")
        
        # Test 6: Test gestione sessioni (se memoria abilitata)
        if hasattr(rag, 'memory_manager') and rag.memory_manager:
            print("\n💾 Test Gestione Sessioni...")
            
            # Lista sessioni
            sessions = rag.get_session_list()
            print(f"📋 Sessioni attive: {len(sessions)}")
            
            # Cronologia conversazione
            if sessions:
                session_id = sessions[0]
                history = rag.get_conversation_history(session_id)
                print(f"📜 Messaggi in sessione {session_id}: {len(history)}")
        
        # Test 7: Informazioni finali sulla collezione
        print("\n📊 Informazioni finali sulla collezione:")
        final_info = rag.get_collection_info()
        print(f"📄 Documenti totali: {final_info.get('count', 0)}")
        print(f"🤖 Modello: {final_info.get('model', 'N/A')}")
        print(f"🔧 Chunk size: {final_info.get('chunk_size', 'N/A')}")
        
        print("\n🎉 Test completato con successo!")
        
    except Exception as e:
        print(f"❌ Errore durante il test: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Verifica che la chiave API sia configurata
    if not settings.anthropic_api_key or settings.anthropic_api_key == "your_anthropic_api_key_here":
        print("❌ Errore: ANTHROPIC_API_KEY non configurata!")
        print("💡 Configura la chiave API nel file .env")
        sys.exit(1)
    
    # Esegui il test
    exit_code = asyncio.run(main())
    sys.exit(exit_code)