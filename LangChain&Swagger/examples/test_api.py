"""
Script di esempio per testare l'API REST del motore RAG
"""
import requests
import json
import time
from pathlib import Path


class RAGAPIClient:
    """Client per l'API RAG"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self):
        """Verifica lo stato dell'API"""
        response = self.session.get(f"{self.base_url}/health")
        return response.json()
    
    def query(self, question: str, include_sources: bool = True):
        """Invia una query al motore RAG"""
        data = {
            "question": question,
            "include_sources": include_sources
        }
        response = self.session.post(f"{self.base_url}/query", json=data)
        return response.json()
    
    def upload_file(self, file_path: str):
        """Carica un file"""
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f)}
            response = self.session.post(f"{self.base_url}/upload/file", files=files)
        return response.json()
    
    def search_similar(self, query: str, k: int = 5):
        """Cerca documenti simili"""
        data = {
            "query": query,
            "k": k
        }
        response = self.session.post(f"{self.base_url}/search/similar", json=data)
        return response.json()
    
    def get_collection_info(self):
        """Ottieni informazioni sulla collezione"""
        response = self.session.get(f"{self.base_url}/collection/info")
        return response.json()
    
    def clear_collection(self):
        """Pulisci la collezione"""
        response = self.session.delete(f"{self.base_url}/collection/clear")
        return response.json()
    
    # New LangChain methods
    def agent_query(self, query: str, session_id: str = "default", agent_type: str = "conversation"):
        """Query using LangChain Agents"""
        data = {
            "query": query,
            "session_id": session_id,
            "agent_type": agent_type
        }
        response = self.session.post(f"{self.base_url}/agent/query", json=data)
        return response.json()
    
    def get_sessions(self):
        """Get list of all active sessions"""
        response = self.session.get(f"{self.base_url}/sessions")
        return response.json()
    
    def delete_session(self, session_id: str):
        """Delete a specific session"""
        response = self.session.delete(f"{self.base_url}/sessions/{session_id}")
        return response.json()
    
    def get_conversation_history(self, session_id: str):
        """Get conversation history for a session"""
        response = self.session.get(f"{self.base_url}/sessions/{session_id}/history")
        return response.json()
    
    def clear_conversation_history(self, session_id: str):
        """Clear conversation history for a session"""
        response = self.session.delete(f"{self.base_url}/sessions/{session_id}/history")
        return response.json()
    
    def custom_chain_query(self, prompt_template: str, query: str, session_id: str = "default"):
        """Use a custom LangChain chain"""
        data = {
            "prompt_template": prompt_template,
            "query": query,
            "session_id": session_id
        }
        response = self.session.post(f"{self.base_url}/custom-chain", json=data)
        return response.json()


def main():
    """Funzione principale di test"""
    print("🚀 Test dell'API RAG Engine...")
    
    # Inizializza il client
    client = RAGAPIClient()
    
    try:
        # Test 1: Health check
        print("\n🏥 Health check...")
        health = client.health_check()
        print(f"✅ Status: {health['status']}")
        print(f"⏰ Uptime: {health.get('uptime_seconds', 0):.2f}s")
        
        # Test 2: Informazioni collezione iniziale
        print("\n📊 Informazioni collezione iniziale...")
        info = client.get_collection_info()
        if info['success']:
            print(f"📄 Documenti: {info['info']['count']}")
            print(f"🤖 Modello: {info['info']['model']}")
        
        # Test 3: Crea e carica un documento di esempio
        print("\n📄 Creazione documento di esempio...")
        example_content = """
        Claude è un assistente AI sviluppato da Anthropic. 
        
        Caratteristiche di Claude:
        - Conversazioni naturali e utili
        - Ragionamento avanzato
        - Analisi di testi e documenti
        - Programmazione e problem solving
        - Sicurezza e allineamento AI
        
        Claude è disponibile in diverse versioni:
        - Claude 3 Haiku: Veloce ed efficiente
        - Claude 3 Sonnet: Bilanciato tra velocità e capacità
        - Claude 3 Opus: Massime prestazioni
        
        Anthropic si concentra sulla ricerca per la sicurezza dell'AI.
        """
        
        # Crea file temporaneo
        temp_file = Path("temp_claude_info.txt")
        temp_file.write_text(example_content, encoding='utf-8')
        
        # Carica il file
        print("📤 Caricamento file...")
        upload_result = client.upload_file(str(temp_file))
        if upload_result['success']:
            print(f"✅ {upload_result['message']}")
            print(f"📊 Documenti aggiunti: {upload_result['documents_added']}")
        else:
            print(f"❌ Errore: {upload_result['message']}")
        
        # Pulisci file temporaneo
        temp_file.unlink()
        
        # Test 4: Query di esempio
        print("\n❓ Test query...")
        questions = [
            "Chi ha sviluppato Claude?",
            "Quali sono le versioni di Claude disponibili?",
            "Cosa fa Anthropic?",
            "Quali sono le caratteristiche di Claude?"
        ]
        
        for question in questions:
            print(f"\n🔍 Domanda: {question}")
            response = client.query(question)
            
            if response['success']:
                print(f"💬 Risposta: {response['answer']}")
                print(f"⏱️ Tempo: {response['response_time_seconds']:.2f}s")
                if response.get('sources'):
                    print(f"📚 Fonti: {response['num_sources']}")
            else:
                print(f"❌ Errore: {response.get('message', 'Errore sconosciuto')}")
            
            time.sleep(1)  # Pausa tra le query
        
        # Test 5: Ricerca documenti simili
        print("\n🔎 Test ricerca documenti simili...")
        similar_result = client.search_similar("assistente AI", k=3)
        
        if similar_result['success']:
            print(f"📋 Trovati {len(similar_result['documents'])} documenti")
            for i, doc in enumerate(similar_result['documents'], 1):
                print(f"\n{i}. Score: {doc['similarity_score']:.4f}")
                print(f"   Contenuto: {doc['content'][:150]}...")
        
        # Test 6: Informazioni finali
        print("\n📊 Informazioni finali collezione...")
        final_info = client.get_collection_info()
        if final_info['success']:
            info_data = final_info['info']
            print(f"📄 Documenti totali: {info_data['count']}")
            print(f"🤖 Modello: {info_data['model']}")
            print(f"🔧 Configurazione chunk: {info_data['chunk_size']}")
        
        # Test LangChain Agent functionality
        print("\n=== Testing LangChain Agents ===")
        
        # Test conversation agent
        agent_result = client.agent_query(
            "Analizza i documenti caricati e dimmi quali sono i temi principali",
            session_id="test_session",
            agent_type="conversation"
        )
        print(f"Conversation Agent result: {agent_result}")
        
        # Test research agent
        research_result = client.agent_query(
            "Fai una ricerca approfondita sui contenuti dei documenti",
            session_id="test_session",
            agent_type="research"
        )
        print(f"Research Agent result: {research_result}")
        
        # Test session management
        print("\n=== Testing Session Management ===")
        sessions = client.get_sessions()
        print(f"Active sessions: {sessions}")
        
        # Get conversation history
        history = client.get_conversation_history("test_session")
        print(f"Conversation history: {history}")
        
        # Test custom chain
        print("\n=== Testing Custom Chain ===")
        custom_prompt = """
        Sei un esperto analista di documenti. Analizza il seguente contesto e rispondi alla domanda in modo dettagliato:
        
        Contesto: {context}
        Domanda: {input}
        
        Risposta dettagliata:
        """
        
        custom_result = client.custom_chain_query(
            prompt_template=custom_prompt,
            query="Quali sono le informazioni più importanti nei documenti?",
            session_id="custom_session"
        )
        print(f"Custom chain result: {custom_result}")
        
        # Test clearing conversation history
        print("\n=== Testing History Clear ===")
        clear_history = client.clear_conversation_history("test_session")
        print(f"Clear history result: {clear_history}")
        
        print("\n🎉 Test API completato con successo!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Errore: Impossibile connettersi all'API")
        print("💡 Assicurati che il server sia in esecuzione su http://localhost:8000")
        return 1
    except Exception as e:
        print(f"❌ Errore durante il test: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)