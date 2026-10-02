import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import shutil
import tempfile
import base64
import uuid
from typing import Optional
from fastapi import FastAPI, Request, Form, UploadFile, File, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import pymupdf
from amzqr.amzqr import run as generate_qr

app = FastAPI(title="Gerador de QR Code e Folhas de Display")

# Make static and templates directories accessible on Vercel and locally
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
templates_dir = os.path.join(current_dir, "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=templates_dir)

# Simple in-memory cache for recent sheet downloads (limits memory usage to last 10 sheets)
SHEET_CACHE = {}
SHEET_CACHE_KEYS = []

def cache_sheet(pdf_bytes: bytes, png_bytes: bytes) -> str:
    sheet_id = str(uuid.uuid4())
    SHEET_CACHE[sheet_id] = {"pdf": pdf_bytes, "png": png_bytes}
    SHEET_CACHE_KEYS.append(sheet_id)
    if len(SHEET_CACHE_KEYS) > 10:
        oldest_id = SHEET_CACHE_KEYS.pop(0)
        SHEET_CACHE.pop(oldest_id, None)
    return sheet_id


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
        _, ext = os.path.splitext(logo.filename)
        fd, logo_path = tempfile.mkstemp(suffix=ext)
        with os.fdopen(fd, "wb") as f:
            shutil.copyfileobj(logo.file, f)

    try:
        temp_dir = tempfile.gettempdir()
        save_name = f"qr_{os.urandom(4).hex()}.png"
        ver, ecl, qr_name = generate_qr(
            words=words,
            level="H",
            save_name=save_name,
            save_dir=temp_dir,
            rounded=rounded,
            logo=logo_path,
            transparent=transparent,
            fg_color=fg_color
        )
        
        with open(qr_name, "rb") as img_file:
            b64_string = base64.b64encode(img_file.read()).decode('utf-8')
            data_url = f"data:image/png;base64,{b64_string}"
            
        if os.path.exists(qr_name):
            os.remove(qr_name)
            
        return {"success": True, "image_url": data_url}
    except Exception as e:
        err_msg = str(e)
        if "Wrong words" in err_msg:
            err_msg = "Texto ou URL contém caracteres não suportados. Utilize letras de A-Z, números e pontuações comuns."
        elif "Wrong logo" in err_msg:
            err_msg = "Arquivo de logo inválido ou corrompido."
        else:
            err_msg = "Ocorreu um erro ao gerar o QR Code. Tente novamente."
        return {"success": False, "error": err_msg}
    finally:
        if logo_path and os.path.exists(logo_path):
            os.remove(logo_path)


@app.post("/generate-sheet")
async def generate_sheet_endpoint(
    words_left: str = Form(...),
    words_right: Optional[str] = Form(None),
    same_qr: bool = Form(True),
    use_google_logo: bool = Form(True),
    rounded: bool = Form(True),
    fg_color: str = Form("#000000"),
    custom_logo: UploadFile = File(None),
    logo_type: Optional[str] = Form(None)
):
    custom_logo_path = None
    temp_files = []

    if custom_logo and custom_logo.filename:
        _, ext = os.path.splitext(custom_logo.filename)
        fd, custom_logo_path = tempfile.mkstemp(suffix=ext)
        with os.fdopen(fd, "wb") as f:
            shutil.copyfileobj(custom_logo.file, f)
        temp_files.append(custom_logo_path)

    try:
        # Determine which logo to use in the QR code
        effective_logo = None
        if logo_type == "custom":
            effective_logo = custom_logo_path
        elif logo_type == "google":
            google_logo = os.path.join(static_dir, "assets", "google_logo.png")
            if os.path.exists(google_logo):
                effective_logo = google_logo
        elif logo_type == "none":
            effective_logo = None
        else:
            if custom_logo_path:
                effective_logo = custom_logo_path
            elif use_google_logo:
                google_logo = os.path.join(static_dir, "assets", "google_logo.png")
                if os.path.exists(google_logo):
                    effective_logo = google_logo

        w_left = words_left.strip()
        w_right = w_left if same_qr or not words_right or not words_right.strip() else words_right.strip()

        temp_dir = tempfile.gettempdir()
        
        # 1. Generate Left QR Code
        qr_l_name = f"qr_sheet_l_{os.urandom(4).hex()}.png"
        _, _, qr_left_path = generate_qr(
            words=w_left,
            level="H",
            save_name=qr_l_name,
            save_dir=temp_dir,
            rounded=rounded,
            logo=effective_logo,
            fg_color=fg_color
        )
        temp_files.append(qr_left_path)

        # 2. Generate Right QR Code
        if w_right == w_left:
            qr_right_path = qr_left_path
        else:
            qr_r_name = f"qr_sheet_r_{os.urandom(4).hex()}.png"
            _, _, qr_right_path = generate_qr(
                words=w_right,
                level="H",
                save_name=qr_r_name,
                save_dir=temp_dir,
                rounded=rounded,
                logo=effective_logo,
                fg_color=fg_color
            )
            temp_files.append(qr_right_path)

        # 3. Open Sheet Template and Insert Images
        template_pdf_path = os.path.join(static_dir, "templates", "sheet_template.pdf")
        if not os.path.exists(template_pdf_path):
            raise FileNotFoundError("Arquivo de template 'sheet_template.pdf' não encontrado.")

        doc = pymupdf.open(template_pdf_path)
        page = doc[0]

        with open(qr_left_path, "rb") as f:
            qr_l_bytes = f.read()
        with open(qr_right_path, "rb") as f:
            qr_r_bytes = f.read()

        # Exact bounding boxes from design:
        # Left card QR: (381.0, 1479.0, 821.0, 1919.0)
        # Right card QR: (2113.0, 1479.0, 2553.0, 1919.0)
        page.insert_image(pymupdf.Rect(381.0, 1479.0, 821.0, 1919.0), stream=qr_l_bytes)
        page.insert_image(pymupdf.Rect(2113.0, 1479.0, 2553.0, 1919.0), stream=qr_r_bytes)

        # PDF output
        pdf_bytes = doc.tobytes()
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        pdf_data_url = f"data:application/pdf;base64,{pdf_b64}"

        # PNG Preview (100 DPI is fast and crisp for screen preview)
        preview_pix = page.get_pixmap(dpi=100)
        preview_bytes = preview_pix.tobytes("png")
        preview_b64 = base64.b64encode(preview_bytes).decode("utf-8")
        preview_data_url = f"data:image/png;base64,{preview_b64}"

        # High-res PNG (200 DPI for ultra quality print download)
        highres_pix = page.get_pixmap(dpi=200)
        highres_bytes = highres_pix.tobytes("png")
        highres_b64 = base64.b64encode(highres_bytes).decode("utf-8")
        highres_data_url = f"data:image/png;base64,{highres_b64}"

        # Cache for direct download URLs
        sheet_id = cache_sheet(pdf_bytes, highres_bytes)

        return {
            "success": True,
            "sheet_id": sheet_id,
            "preview_url": preview_data_url,
            "pdf_url": pdf_data_url,
            "png_url": highres_data_url,
            "pdf_download_url": f"/download/pdf/{sheet_id}",
            "png_download_url": f"/download/png/{sheet_id}"
        }

    except Exception as e:
        err_msg = str(e)
        if "Wrong words" in err_msg:
            err_msg = "Texto ou URL contém caracteres não suportados. Utilize letras de A-Z, números e pontuações comuns."
        elif "Wrong logo" in err_msg:
            err_msg = "Arquivo de imagem inválido ou não suportado."
        else:
            err_msg = "Não foi possível gerar a folha. Verifique os dados e tente novamente."
        return {"success": False, "error": err_msg}
    finally:
        for p in temp_files:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


@app.get("/download/pdf/{sheet_id}")
async def download_sheet_pdf(sheet_id: str):
    sheet = SHEET_CACHE.get(sheet_id)
    if not sheet or "pdf" not in sheet:
        return Response(content="Arquivo expirado ou não encontrado.", status_code=404)
    return Response(
        content=sheet["pdf"],
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="folha_display_google_a4.pdf"'}
    )


@app.get("/download/png/{sheet_id}")
async def download_sheet_png(sheet_id: str):
    sheet = SHEET_CACHE.get(sheet_id)
    if not sheet or "png" not in sheet:
        return Response(content="Arquivo expirado ou não encontrado.", status_code=404)
    return Response(
        content=sheet["png"],
        media_type="image/png",
        headers={"Content-Disposition": 'attachment; filename="folha_display_google_a4.png"'}
    )


# For local development compatibility
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
