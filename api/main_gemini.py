from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from PIL import Image
import json
import io
import base64

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

API_KEY = "AIzaSyAtOT_ggwWMPvr9b8oCyswDDB9G53SFv2A"
client = genai.Client(api_key=API_KEY)
MODEL = "gemini-2.5-flash"

class GenerateRequest(BaseModel):
    description: str
    iteration: int = 0
    previous_data: dict = None
    feedback: str = None

class AnalyzeRequest(BaseModel):
    image_base64: str
    current_data: dict

@app.post("/generate")
async def generate_kitchen(request: GenerateRequest):
    try:
        # Jos on palautetta, käytä sitä
        feedback_context = ""
        if request.feedback and request.previous_data:
            feedback_context = f"""
EDELLINEN VERSIO JA PALAUTE:
{json.dumps(request.previous_data, indent=2, ensure_ascii=False)}

Käyttäjän palaute/edellisen version ongelmat:
{request.feedback}

Korjaa yllä olevaan keittiöön mainitut ongelmat. Säilytä toimivat osat.
"""
        
        prompt = f"""
Luo keittiösuunnitelma JSON-muodossa.

{feedback_context if feedback_context else f"Käyttäjän kuvaus: {request.description}"}

Vastaa VAIN JSON:

{{
  "nimi": "Keittiön nimi",
  "iteraatio": {request.iteration + 1},
  "mitat": {{"leveys_mm": 4000, "syvyys_mm": 3000, "korkeus_mm": 2700}},
  "parannukset": "Mitä parannettiin tähän versioon",
  "kaapit": [...],
  "kodinkoneet": [...]
}}
"""
        
        response = client.models.generate_content(model=MODEL, contents=prompt)
        
        # Puhdista JSON
        text = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        else:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                text = text[start:end]
        
        data = json.loads(text)
        
        # Varmista kentät
        if "kaapit" not in data: data["kaapit"] = []
        if "kodinkoneet" not in data: data["kodinkoneet"] = []
        if "mitat" not in data: data["mitat"] = {"leveys_mm": 4000, "syvyys_mm": 3000}
        if "parannukset" not in data: data["parannukset"] = f"Iteraatio {request.iteration + 1}"
        
        # Lisää sijainnit
        x_pos = 0
        for k in data["kaapit"]:
            if "x" not in k: 
                k["x"] = x_pos
                k["z"] = 0
                k["rotation"] = 0
                if "y" not in k: k["y"] = 0
            x_pos += k.get("leveys_mm", 600)
        
        x_pos = 0
        for k in data["kodinkoneet"]:
            if "x" not in k:
                k["x"] = x_pos
                k["z"] = 600
                k["rotation"] = 0
                if "y" not in k: k["y"] = 0
            x_pos += k.get("leveys_mm", 600)
        
        return {"status": "success", "data": data, "model": MODEL, "iteration": request.iteration}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_kitchen(request: AnalyzeRequest):
    """Gemini analysoi 3D-kuvan ja antaa parannusehdotukset"""
    try:
        # Dekoodaa kuva
        image_bytes = base64.b64decode(request.image_base64.split(",")[1])
        image = Image.open(io.BytesIO(image_bytes))
        
        prompt = f"""
Analysoi tämä keittiön 3D-malli. 

Nykyinen suunnitelma:
{json.dumps(request.current_data, indent=2, ensure_ascii=False)}

Tarkista:
1. Toimiiko työkolmio (jääkaappi-liesi-allas)?
2. Onko tilaa liikkua?
3. Onko kaapit sijoitettu loogisesti?
4. Puuttuuko jotain tärkeää?

Vastaa JSON:
{{
  "toimiva": true/false,
  "ongelmat": ["lista ongelmista"],
  "parannusehdotukset": "Mitä pitää muuttaa",
  "seuraava_askel": "Tarkka kuvaus miten korjata"
}}
"""
        
        response = client.models.generate_content(model=MODEL, contents=[prompt, image])
        
        # Parsi JSON
        text = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        else:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                text = text[start:end]
        
        analysis = json.loads(text)
        
        return {
            "status": "success", 
            "analysis": analysis,
            "model": MODEL
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Kitchen 3D AI - Iterative", "model": MODEL}