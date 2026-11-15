# Qwen3-TTS (VoiceDesign + Base clone) for the generate-voice-lines skill.
# faster-whisper + librosa run the word check (check_takes.py) in the same container (CPU).
# CUDA 12.8 torch is needed for RTX 50xx (Blackwell, sm_120). ~19 GB image; weights (~4 GB each
# for VoiceDesign and Base) download into the hf-cache volume on first use.
FROM nvidia/cuda:12.8.1-runtime-ubuntu24.04
ENV DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1 HF_HOME=/hf-cache
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-venv python3-pip libsndfile1 sox ffmpeg git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /venv
ENV PATH=/venv/bin:$PATH
RUN pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128 \
 && pip install qwen-tts soundfile faster-whisper librosa
WORKDIR /work
