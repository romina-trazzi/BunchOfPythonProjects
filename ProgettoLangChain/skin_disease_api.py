from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import requests
from typing import Dict, Any, Optional


class SkinDiseaseInput(BaseModel):
    """Input for skin disease detection."""
    image_url: str = Field(..., description="URL of the skin image to analyze")


class SkinDiseaseAPI(BaseTool):
    """Tool that uses the Skin Disease Detection API."""
    name = "skin_disease_detector"
    description = "Useful for detecting skin diseases from images."
    
    def _run(self, image_url: str) -> Dict[str, Any]:
        """Run the skin disease detection on the provided image URL."""
        url = "https://detect-skin-disease1.p.rapidapi.com/skin-disease"
        
        payload = {"url": image_url}
        headers = {
            "x-rapidapi-key": "653b32e85fmsh8c6fdd614fd109bp15c804jsn8b3353fa29f0",
            "x-rapidapi-host": "detect-skin-disease1.p.rapidapi.com",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            response = requests.post(url, data=payload, headers=headers)
            response.raise_for_status()  # Raise exception for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    async def _arun(self, image_url: str) -> Dict[str, Any]:
        """Run the skin disease detection asynchronously."""
        # For simplicity, we're using the synchronous version
        return self._run(image_url)