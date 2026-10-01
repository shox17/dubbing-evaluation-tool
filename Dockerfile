# Dubbing QA Studio: the Streamlit app (default) or the REST API, CPU only.
#   docker build -t dubbing-qa .
#   docker run -p 8501:8501 -v dubbing-qa-data:/data --env-file .env dubbing-qa                 # app
#   docker run --rm -v dubbing-qa-data:/data --env-file .env dubbing-qa python qa.py "<link>"    # CLI (files in /data/output)
#   docker run -p 8000:8000 -v dubbing-qa-data:/data -e DUBBING_QA_API_TOKEN=... dubbing-qa \
#              python qa.py serve --host 0.0.0.0                                                  # API
FROM python:3.14-slim

# OpenCV and MediaPipe need GL/EGL and GLib; MediaPipe 1.x also imports sounddevice (PortAudio);
# ffmpeg comes with imageio-ffmpeg.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgl1 libegl1 libgles2 libglib2.0-0 libportaudio2 \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 PYTHONUTF8=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DUBBING_QA_DATA=/data DUBBING_QA_OUT=/data/output \
    XDG_CACHE_HOME=/home/app/.cache DUBBING_QA_MODELS=/home/app/.cache/dubbing-qa

# /data must exist and belong to the app user before VOLUME, or new volumes are created root-owned and unwritable.
RUN useradd --create-home --uid 1000 app && mkdir -p /data /app && chown app:app /data /app
WORKDIR /app

# CPU-only PyTorch first: the default Linux wheel brings ~2.5 GB of GPU libraries this tool never uses.
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch
COPY requirements.txt .
# The pins were verified on macOS arm64 and Linux x86_64. MediaPipe 0.10.x has no Linux ARM wheel for Python 3.14,
# so there (e.g. Docker on Apple Silicon) the MediaPipe pin is relaxed to the 1.x line, which keeps the same API.
RUN pip install -r requirements.txt \
 || (sed 's/^mediapipe==[^ ]*/mediapipe/' requirements.txt > /tmp/requirements.txt && pip install -r /tmp/requirements.txt)

COPY --chown=app:app . .
USER app

# Models baked in so the container works offline: Whisper base (~145 MB) and the speaker model (26 MB, SHA-256 checked).
RUN python -c "import whisper; whisper.load_model('base')" \
 && python -c "from src import speaker; speaker.model_path()"

VOLUME /data
EXPOSE 8501 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
  CMD python -c "import urllib.request,sys; [urllib.request.urlopen(u, timeout=3) for u in sys.argv[1:2]]" \
      "http://127.0.0.1:8501/_stcore/health" || exit 1
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
