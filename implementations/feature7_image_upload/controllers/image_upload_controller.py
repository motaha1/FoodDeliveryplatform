import os
import threading
from io import BytesIO
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from implementations.extensions import db
from implementations.feature7_image_upload.models import ImageJob
from PIL import Image
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

load_dotenv()
image_upload_bp = Blueprint('image_upload', __name__, static_folder='../static')

# ---- Azure Blob Storage Configuration ----
AZURE_CONNECTION_STRING = os.environ.get(
    'AZURE_STORAGE_CONNECTION_STRING'
)
CONTAINER_NAME = os.environ.get('AZURE_CONTAINER', 'menu-images')
ACCOUNT_NAME = 'gsg'
BLOB_BASE_URL = f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}"

_blob_service = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
_container_client = _blob_service.get_container_client(CONTAINER_NAME)
try:
    _container_client.create_container()
except Exception:
    pass

# In-memory mapping for blob names (original / processed)
_image_blobs = {}  # job_id -> {original: ..., processed: ...}

ALLOWED_EXT = {'.jpg', '.jpeg', '.png', '.webp'}

# -------- Image Processing Logic ---------

def _remove_background_make_white(img: Image.Image) -> Image.Image:
    if img.mode not in ('RGBA', 'LA'):
        img = img.convert('RGBA')
    white_bg = Image.new('RGB', img.size, (255, 255, 255))
    white_bg.paste(img, mask=img.split()[3])
    return white_bg

def _upload_blob(blob_name: str, data: bytes, content_type: str):
    blob_client = _blob_service.get_blob_client(container=CONTAINER_NAME, blob=blob_name)
    blob_client.upload_blob(data, overwrite=True, content_settings=ContentSettings(content_type=content_type))

def _process_job(job_id: int):
    with current_app.app_context():
        job = ImageJob.query.get(job_id)
        if not job:
            return
        job.status = 'processing'
        db.session.commit()
        blob_info = _image_blobs.get(job_id)
        if not blob_info:
            job.status = 'failed'
            job.error = 'Missing original blob info'
            db.session.commit()
            return
        try:
            orig_blob = blob_info['original']
            blob_client = _blob_service.get_blob_client(CONTAINER_NAME, orig_blob)
            stream = blob_client.download_blob()
            original_bytes = stream.readall()
            img = Image.open(BytesIO(original_bytes))
            processed_img = _remove_background_make_white(img)
            out_buf = BytesIO()
            processed_img.save(out_buf, format='JPEG', quality=90)
            out_buf.seek(0)
            processed_blob = f"processed/job{job.id}.jpg"
            _upload_blob(processed_blob, out_buf.read(), 'image/jpeg')
            blob_info['processed'] = processed_blob
            job.status = 'completed'
            job.error = None
        except Exception as e:  # noqa
            job.status = 'failed'
            job.error = str(e)[:200]
        finally:
            db.session.commit()

# -------- Routes ---------

@image_upload_bp.route('/feature7/upload')
def upload_page():
    # static folder path relative change; serve file from feature static
    static_dir = os.path.join(os.path.dirname(__file__), '..', 'static')
    return send_from_directory(os.path.abspath(static_dir), 'upload_client.html')

@image_upload_bp.route('/api/v1/image-jobs', methods=['POST'])
def create_job():
    if 'file' not in request.files:
        return jsonify({'error': 'file required'}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'error': 'empty filename'}), 400
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        return jsonify({'error': 'unsupported extension'}), 400

    job = ImageJob(filename=f.filename, status='pending')
    db.session.add(job)
    db.session.commit()

    orig_blob = f"original/job{job.id}{ext}"
    data = f.read()
    content_type = 'image/jpeg' if ext in ('.jpg', '.jpeg') else 'image/png'
    _upload_blob(orig_blob, data, content_type)
    _image_blobs[job.id] = {'original': orig_blob}

    threading.Thread(target=_process_job, args=(job.id,), daemon=True).start()
    return jsonify({'job_id': job.id, 'status': job.status})
#here is the short polling to check the status of the image  job
@image_upload_bp.route('/api/v1/image-jobs/<int:job_id>', methods=['GET'])
def job_status(job_id):
    job = ImageJob.query.get(job_id)
    if not job:
        return jsonify({'error': 'not found'}), 404
    payload = {'job_id': job.id, 'status': job.status, 'error': job.error}
    blob_info = _image_blobs.get(job_id)
    if blob_info:
        if 'original' in blob_info:
            payload['original_url'] = f"{BLOB_BASE_URL}/{blob_info['original']}"
        if job.status == 'completed' and blob_info.get('processed'):
            payload['processed_url'] = f"{BLOB_BASE_URL}/{blob_info['processed']}"
    return jsonify(payload)

@image_upload_bp.route('/api/v1/image-jobs/health')
def health():
    return {'status': 'ok'}

