"""
Script di avvio rapido per il motore RAG
"""
import os
import sys
import subprocess
from pathlib import Path


def check_requirements():
    """Verifica i requisiti di sistema"""
    print("🔍 Verifica requisiti di sistema...")
    
    # Verifica Docker
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker installato")
        else:
            print("❌ Docker non trovato")
            return False
    except FileNotFoundError:
        print("❌ Docker non installato")
        return False
    
    # Verifica Docker Compose
    try:
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker Compose installato")
        else:
            print("❌ Docker Compose non trovato")
            return False
    except FileNotFoundError:
        print("❌ Docker Compose non installato")
        return False
    
    return True


def setup_environment():
    """Configura l'ambiente"""
    print("\n🔧 Configurazione ambiente...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📋 Copia .env.example in .env...")
        env_file.write_text(env_example.read_text())
        print("✅ File .env creato")
        print("⚠️  IMPORTANTE: Configura ANTHROPIC_API_KEY nel file .env")
        return False
    elif env_file.exists():
        print("✅ File .env già presente")
        
        # Verifica chiave API
        env_content = env_file.read_text()
        if "your_anthropic_api_key_here" in env_content:
            print("⚠️  ATTENZIONE: Configura ANTHROPIC_API_KEY nel file .env")
            return False
        else:
            print("✅ Chiave API configurata")
            return True
    else:
        print("❌ File .env.example non trovato")
        return False


def create_directories():
    """Crea le directory necessarie"""
    print("\n📁 Creazione directory...")
    
    directories = ["data", "logs", "uploads"]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)
        print(f"✅ Directory {dir_name}/ creata")


def start_services():
    """Avvia i servizi Docker"""
    print("\n🚀 Avvio servizi Docker...")
    
    try:
        # Build e avvio
        result = subprocess.run(
            ['docker-compose', 'up', '--build', '-d'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Servizi avviati con successo!")
            print("\n🌐 Servizi disponibili:")
            print("   • API RAG: http://localhost:8000")
            print("   • Documentazione: http://localhost:8000/docs")
            print("   • File Browser: http://localhost:8080")
            print("\n📊 Per visualizzare i logs:")
            print("   docker-compose logs -f")
            return True
        else:
            print(f"❌ Errore durante l'avvio: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        return False


def show_usage():
    """Mostra esempi di utilizzo"""
    print("\n📖 Esempi di utilizzo:")
    print("\n1. Test Health Check:")
    print("   curl http://localhost:8000/health")
    
    print("\n2. Query di esempio:")
    print('   curl -X POST "http://localhost:8000/query" \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"question": "Ciao, come funzioni?", "include_sources": true}\'')
    
    print("\n3. Upload documento:")
    print('   curl -X POST "http://localhost:8000/upload/file" \\')
    print('     -F "file=@documento.pdf"')
    
    print("\n4. Test con script Python:")
    print("   cd examples")
    print("   python test_api.py")


def main():
    """Funzione principale"""
    print("🤖 RAG Engine con Claude Sonnet - Setup Automatico")
    print("=" * 50)
    
    # Verifica requisiti
    if not check_requirements():
        print("\n❌ Requisiti di sistema non soddisfatti")
        print("💡 Installa Docker e Docker Compose prima di continuare")
        return 1
    
    # Configura ambiente
    env_ready = setup_environment()
    
    # Crea directory
    create_directories()
    
    if not env_ready:
        print("\n⚠️  Configura la chiave API prima di continuare:")
        print("   1. Apri il file .env")
        print("   2. Sostituisci 'your_anthropic_api_key_here' con la tua chiave API")
        print("   3. Esegui nuovamente questo script")
        return 1
    
    # Avvia servizi
    if start_services():
        show_usage()
        print("\n🎉 Setup completato con successo!")
        return 0
    else:
        print("\n❌ Errore durante l'avvio dei servizi")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)