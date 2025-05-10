import os
import shutil
import uuid
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.background import BackgroundTask
from PIL import Image
from PyPDF2 import PdfMerger
from pdf2image import convert_from_path
from jinja2 import Template

app = FastAPI()
BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


def cleanup_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)


TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sukant Sondhi's File Conversion Tool (Web)</title>
    <style>
        body { font-family: Segoe UI, Arial, sans-serif; background: #f4f6fa; color: #2d415a; }
        .container { max-width: 900px; margin: 30px auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px #0001; padding: 24px; }
        h1 { color: #2d415a; }
        .file-list { margin: 16px 0; }
        .preview { margin: 16px 0; }
        .preview img { max-width: 320px; max-height: 320px; border: 1px solid #e9eef6; background: #e9eef6; }
        .footer { color: #8a99b3; margin-top: 32px; }
        .btn { font-family: Segoe UI, Arial, sans-serif; font-size: 15px; padding: 8px 18px; border-radius: 5px; border: none; background: #2d415a; color: #fff; margin: 2px; cursor: pointer; }
        .btn:disabled { background: #ccc; }
        .row { display: flex; gap: 10px; }
        .panel { flex: 1; }
        .panel-list { background: #fafdff; border: 1px solid #e9eef6; border-radius: 5px; padding: 10px; min-height: 340px; }
        .panel-preview { background: #e9eef6; border-radius: 5px; min-height: 340px; display: flex; align-items: center; justify-content: center; }
        .panel-preview img { display: block; margin: auto; }
        .panel-list ul { list-style: none; padding: 0; margin: 0; }
        .panel-list li { padding: 4px 0; }
        .panel-list .selected { background: #e9eef6; }
        .controls { margin: 18px 0 0 0; }
        .controls label { margin-right: 8px; }
        .controls input[type=text] { font-size: 15px; padding: 5px; border-radius: 4px; border: 1px solid #ccc; width: 220px; }
    </style>
    <script>
        function selectFile(idx, type) {
            document.getElementById('selected_idx_' + type + '_' + idx).form.submit();
        }
    </script>
</head>
<body>
<div class="container">
    <h1>Sukant Sondhi's File Conversion Tool (Web)</h1>
    <form action="/upload" method="post" enctype="multipart/form-data" style="margin-bottom: 0;">
        <input type="hidden" name="session_id" value="{{ session_id }}">
        <input type="file" name="files" multiple>
        <button class="btn" type="submit">Upload Images/PDFs</button>
        <a href="/clear/{{ session_id }}" class="btn" style="background:#b33;">Clear All</a>
    </form>
    <div class="row">
        <div class="panel panel-list">
            <b>Uploaded Files</b>
            <ul>
                {% for img in images or [] %}
                    {% set idx = loop.index0 %}
                    <li {% if selected_type=='image' and selected_idx==idx %}class="selected"{% endif %}>
                        <form action="/session/{{ session_id }}" method="get" style="display:inline;">
                            <input type="hidden" id="selected_idx_image_{{ idx }}" name="selected_idx" value="{{ idx }}">
                            <input type="hidden" name="selected_type" value="image">
                            <a href="javascript:selectFile({{ idx }}, 'image');">{{ img }}</a>
                        </form>
                    </li>
                {% endfor %}
                {% for pdf in pdfs or [] %}
                    {% set idx = loop.index0 %}
                    <li {% if selected_type=='pdf' and selected_idx==idx %}class="selected"{% endif %}>
                        <form action="/session/{{ session_id }}" method="get" style="display:inline;">
                            <input type="hidden" id="selected_idx_pdf_{{ idx }}" name="selected_idx" value="{{ idx }}">
                            <input type="hidden" name="selected_type" value="pdf">
                            <a href="javascript:selectFile({{ idx }}, 'pdf');">{{ pdf }}</a>
                        </form>
                    </li>
                {% endfor %}
            </ul>
        </div>
        <div class="panel panel-preview">
            {% if preview_url %}
                <img src="{{ preview_url }}" alt="Preview">
            {% else %}
                <span style="color:#8a99b3;">No preview available</span>
            {% endif %}
        </div>
    </div>
    <form class="controls" action="/convert" method="post">
        <input type="hidden" name="session_id" value="{{ session_id }}">
        <label>Output format:</label>
        <select name="output_format">
            <option value="PDF" {% if output_format=='PDF' %}selected{% endif %}>PDF</option>
            <option value="JPG" {% if output_format=='JPG' %}selected{% endif %}>JPG</option>
            <option value="PNG" {% if output_format=='PNG' %}selected{% endif %}>PNG</option>
        </select>
        <label>Output file name:</label>
        <input type="text" name="pdf_name" value="{{ pdf_name or '' }}" placeholder="output.pdf">
        <button class="btn" type="submit" name="action" value="images_to_pdf">Images to PDF</button>
        <button class="btn" type="submit" name="action" value="convert_images">Convert Images</button>
        <button class="btn" type="submit" name="action" value="pdf_to_images">PDF to Images</button>
        <button class="btn" type="submit" name="action" value="merge_pdfs">Merge PDFs</button>
    </form>
    <div class="footer">
        Created with ❤️ by Sukant Sondhi
    </div>
</div>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    html = Template(TEMPLATE).render(
        session_id=session_id,
        images=[],
        pdfs=[],
        preview_url=None,
        selected_idx=None,
        selected_type=None,
        output_format="PDF",
        pdf_name="",
    )
    return HTMLResponse(html)


@app.get("/clear/{session_id}")
async def clear_all(session_id: str):
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir)
    return RedirectResponse("/", status_code=303)


@app.post("/upload")
async def upload(
    request: Request, session_id: str = Form(...), files: list[UploadFile] = File(...)
):
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".png", ".jpg", ".jpeg", ".heic", ".pdf"]:
            continue
        dest = os.path.join(session_dir, file.filename)
        with open(dest, "wb") as f:
            f.write(await file.read())
    return RedirectResponse(f"/session/{session_id}", status_code=303)


@app.get("/session/{session_id}", response_class=HTMLResponse)
async def session_view(
    request: Request,
    session_id: str,
    selected_idx: int = None,
    selected_type: str = None,
):
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    files = os.listdir(session_dir) if os.path.exists(session_dir) else []
    images = [
        f
        for f in files
        if os.path.splitext(f)[1].lower() in [".png", ".jpg", ".jpeg", ".heic"]
    ]
    pdfs = [f for f in files if f.lower().endswith(".pdf")]
    preview_url = None
    if (
        selected_type == "image"
        and selected_idx is not None
        and 0 <= int(selected_idx) < len(images)
    ):
        preview_url = f"/preview/{session_id}/{images[int(selected_idx)]}"
    elif (
        selected_type == "pdf"
        and selected_idx is not None
        and 0 <= int(selected_idx) < len(pdfs)
    ):
        preview_url = f"/preview/{session_id}/{pdfs[int(selected_idx)]}"
    elif images:
        preview_url = f"/preview/{session_id}/{images[0]}"
        selected_type = "image"
        selected_idx = 0
    elif pdfs:
        preview_url = f"/preview/{session_id}/{pdfs[0]}"
        selected_type = "pdf"
        selected_idx = 0
    html = Template(TEMPLATE).render(
        session_id=session_id,
        images=images,
        pdfs=pdfs,
        preview_url=preview_url,
        selected_idx=int(selected_idx) if selected_idx is not None else None,
        selected_type=selected_type,
        output_format="PDF",
        pdf_name="",
    )
    return HTMLResponse(html)


@app.get("/preview/{session_id}/{filename}")
async def preview_file(session_id: str, filename: str):
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    file_path = os.path.join(session_dir, filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext in [".png", ".jpg", ".jpeg", ".heic"]:
        return FileResponse(file_path)
    elif ext == ".pdf":
        # Render first page as PNG
        images = convert_from_path(file_path, first_page=1, last_page=1)
        if images:
            preview_path = os.path.join(session_dir, f"preview_{filename}.png")
            images[0].save(preview_path, "PNG")
            return FileResponse(preview_path)
    return FileResponse(file_path)


@app.post("/convert")
async def convert(
    request: Request,
    session_id: str = Form(...),
    action: str = Form(...),
    output_format: str = Form(...),
    pdf_name: str = Form("output.pdf"),
):
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    files = os.listdir(session_dir)
    images = [
        f
        for f in files
        if os.path.splitext(f)[1].lower() in [".png", ".jpg", ".jpeg", ".heic"]
    ]
    pdfs = [f for f in files if f.lower().endswith(".pdf")]
    result_path = None

    if action == "images_to_pdf" and images:
        imgs = [Image.open(os.path.join(session_dir, f)).convert("RGB") for f in images]
        result_path = os.path.join(
            session_dir, pdf_name if pdf_name.endswith(".pdf") else pdf_name + ".pdf"
        )
        imgs[0].save(result_path, save_all=True, append_images=imgs[1:])
    elif action == "convert_images" and images:
        out_dir = os.path.join(session_dir, "converted")
        os.makedirs(out_dir, exist_ok=True)
        for imgf in images:
            img = Image.open(os.path.join(session_dir, imgf)).convert("RGB")
            base = os.path.splitext(imgf)[0]
            out_path = os.path.join(out_dir, f"{base}.{output_format.lower()}")
            img.save(out_path, format=output_format.upper())
        result_path = out_dir
    elif action == "pdf_to_images" and pdfs:
        out_dir = os.path.join(session_dir, "pdf_images")
        os.makedirs(out_dir, exist_ok=True)
        for pdff in pdfs:
            pages = convert_from_path(os.path.join(session_dir, pdff))
            for i, page in enumerate(pages, 1):
                page.save(
                    os.path.join(out_dir, f"{os.path.splitext(pdff)[0]}_page_{i}.png"),
                    "PNG",
                )
        result_path = out_dir
    elif action == "merge_pdfs" and len(pdfs) > 1:
        result_path = os.path.join(
            session_dir, pdf_name if pdf_name.endswith(".pdf") else pdf_name + ".pdf"
        )
        merger = PdfMerger()
        for pdf in pdfs:
            merger.append(os.path.join(session_dir, pdf))
        merger.write(result_path)
        merger.close()

    if result_path and os.path.isfile(result_path):
        return FileResponse(
            result_path,
            filename=os.path.basename(result_path),
            background=BackgroundTask(cleanup_dir, session_dir),
        )
    elif result_path and os.path.isdir(result_path):
        # For folders, zip and return
        import zipfile

        zip_path = result_path + ".zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for root, _, files in os.walk(result_path):
                for f in files:
                    zf.write(os.path.join(root, f), arcname=f)
        return FileResponse(
            zip_path,
            filename=os.path.basename(zip_path),
            background=BackgroundTask(cleanup_dir, session_dir),
        )
    else:
        return RedirectResponse(f"/session/{session_id}", status_code=303)


# Clean up uploads directory on server restart (optional)
@app.on_event("startup")
def cleanup_uploads():
    for d in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, d)
        if os.path.isdir(path):
            shutil.rmtree(path)
