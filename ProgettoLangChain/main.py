from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from skin_disease_api import SkinDiseaseAPI
import uvicorn

app = FastAPI(
    title="Servizio di Rilevamento Malattie della Pelle",
    description="Un servizio REST che utilizza LangChain per rilevare malattie della pelle da immagini",
    version="1.0.0"
)

class ImageRequest(BaseModel):
    image_url: str

@app.post("/detect-skin-disease/")
async def detect_skin_disease(request: ImageRequest):
    """
    Rileva malattie della pelle da un'immagine utilizzando l'API tramite LangChain.
    
    - **image_url**: URL dell'immagine da analizzare
    
    Restituisce i risultati dell'analisi dell'immagine.
    """
    try:
        # Utilizziamo il tool LangChain per chiamare l'API
        skin_disease_tool = SkinDiseaseAPI()
        result = await skin_disease_tool._arun(request.image_url)
        
        # Verifichiamo se c'è stato un errore
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """
    Endpoint di benvenuto che fornisce informazioni sul servizio.
    """
    return {
        "message": "Benvenuto nel servizio di rilevamento malattie della pelle",
        "usage": "Invia una richiesta POST a /detect-skin-disease/ con un URL di un'immagine"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)