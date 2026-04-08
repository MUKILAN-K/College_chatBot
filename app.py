from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from groq import Groq
import edge_tts
import asyncio
import os

app = FastAPI()

# DEBUG: Show errors in browser
@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    return PlainTextResponse(f"DEBUG ERROR: {str(exc)}", status_code=500)

# Get the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mount static files (using absolute path)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Setup templates (using absolute path)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# 🔑 Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load college data
def load_data():
    file_path = os.path.join(BASE_DIR, "college_data.txt")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

college_data = load_data()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_text = data.get("text", "")

    prompt = f"""
You are Campus Thozhan, a helpful and friendly college assistant.

STRICT RULES:
- Answer ONLY from given data
- Answer in ONE short, friendly sentence
- DO NOT say "meow", "mew", or any forced cat sounds
- If not found, say "I'm sorry, I don't have that information. Could you please ask again?"

DATA:
{college_data}

QUESTION:
{user_text}

ANSWER:
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    answer = response.choices[0].message.content.strip()
    return {"answer": answer}

@app.get("/voice")
async def voice(text: str):
    # Use high quality female neural voice (Ava is extremely clear and feminine)
    output_file = "static/temp_voice.mp3"
    communicate = edge_tts.Communicate(text, "en-US-AvaNeural")
    await communicate.save(output_file)
    return FileResponse(output_file, media_type="audio/mpeg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
