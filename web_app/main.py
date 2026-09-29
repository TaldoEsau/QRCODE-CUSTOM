import os
import shutil
import tempfile
import base64
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from amzqr.amzqr import run as generate_qr

app = FastAPI()

# Make static and templates directories accessible on Vercel
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
templates_dir = os.path.join(current_dir, "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=templates_dir)

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
        # Generate QR in a temporary directory (Vercel allows writing to /tmp)
        temp_dir = tempfile.gettempdir()
        save_name = f"qr_{os.urandom(4).hex()}.png"
        ver, ecl, qr_name = generate_qr(
            words=words,
            level="H", # Always use H level for logos
            save_name=save_name,
            save_dir=temp_dir,
            rounded=rounded,
            logo=logo_path,
            transparent=transparent,
            fg_color=fg_color
        )
        
        # Read the generated image and convert to Base64
        with open(qr_name, "rb") as img_file:
            b64_string = base64.b64encode(img_file.read()).decode('utf-8')
            data_url = f"data:image/png;base64,{b64_string}"
            
        # Clean up the generated file from /tmp
        if os.path.exists(qr_name):
            os.remove(qr_name)
            
        return {"success": True, "image_url": data_url}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        # Clean up temp logo
        if logo_path and os.path.exists(logo_path):
            os.remove(logo_path)

# For local development compatibility
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
