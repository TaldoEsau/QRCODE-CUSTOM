import os
import shutil
import tempfile
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from amzqr.amzqr import run as generate_qr

app = FastAPI(title="QR Code Generator")

# Create required directories
os.makedirs("web_app/static", exist_ok=True)
os.makedirs("web_app/templates", exist_ok=True)
os.makedirs("generated_qrs", exist_ok=True)

app.mount("/static", StaticFiles(directory="web_app/static"), name="static")
app.mount("/generated_qrs", StaticFiles(directory="generated_qrs"), name="generated_qrs")

templates = Jinja2Templates(directory="web_app/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/generate")
async def generate(
    words: str = Form(...),
    rounded: bool = Form(False),
    transparent: bool = Form(False),
    fg_color: str = Form("#000000"),
    logo: UploadFile = File(None)
):
    logo_path = None
    if logo and logo.filename:
        # Save logo to temporary location
        _, ext = os.path.splitext(logo.filename)
        fd, logo_path = tempfile.mkstemp(suffix=ext)
        with os.fdopen(fd, "wb") as f:
            shutil.copyfileobj(logo.file, f)

    try:
        # Generate QR
        save_name = f"qr_{os.urandom(4).hex()}.png"
        ver, ecl, qr_name = generate_qr(
            words=words,
            level="H", # Always use H level for logos
            save_name=save_name,
            save_dir="generated_qrs",
            rounded=rounded,
            logo=logo_path,
            transparent=transparent,
            fg_color=fg_color
        )
        return {"success": True, "image_url": f"/generated_qrs/{save_name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        # Clean up temp logo
        if logo_path and os.path.exists(logo_path):
            os.remove(logo_path)

if __name__ == "__main__":
    import uvicorn
    import sys
    # Muda o diretório atual para a pasta raiz "amazing-qr"
    root_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
    os.chdir(root_dir)
    sys.path.insert(0, root_dir)
    uvicorn.run("web_app.main:app", host="0.0.0.0", port=8080)
