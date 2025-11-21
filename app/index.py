import os
import requests
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

API_URL = "https://router.huggingface.co/hf-inference/models/nlptown/bert-base-multilingual-uncased-sentiment"
HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
}

def query(commentaire:str):
    payload = {"inputs": commentaire}  
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    result=response.json()
    
    if isinstance(result, dict) and "error" in result:
        return {"error": "HuggingFace model error", "details": result["error"]}

    # Vérifier si le format attendu existe
    if not isinstance(result, list) or len(result) == 0:
        return {"error": "Unexpected response format", "details": result}

    # Récupération du meilleur label
    best_label = max(result[0], key=lambda x: x["score"])

    return {
        "label": best_label["label"],
        "score": best_label["score"]
    }
