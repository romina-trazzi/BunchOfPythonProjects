# tools/check_imports.py
mods = [
    "fastapi", "uvicorn", "python_multipart",
    "langchain", "langchain_community", "langchain_text_splitters", "langchain_experimental",
    "langchain_anthropic", "anthropic",
    "chromadb", "sentence_transformers",
    "duckduckgo_search",
    "pypdf", "docx2txt",
    "pydantic", "pydantic_settings", "dotenv",
]
missing = []
for m in mods:
    try:
        __import__(m)
    except Exception as e:
        missing.append((m, type(e).__name__, str(e)))
print("MISSING:", [m for m,_,_ in missing])
for m, t, msg in missing:
    print(f"- {m}: {t} -> {msg}")