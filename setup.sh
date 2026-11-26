#!/bin/bash
# One-time per container: install render deps and TTS models.
set -e
python3 -c "import cairo, kokoro_onnx" 2>/dev/null || pip install -q pycairo kokoro-onnx soundfile
mkdir -p /tmp/ss/models /tmp/ss/prev /tmp/ss/out
cd /tmp/ss/models
[ -s kokoro.onnx ] || curl -sSL -o kokoro.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
[ -s voices.bin ] || curl -sSL -o voices.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
echo setup ok
