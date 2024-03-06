FROM nvcr.io/nvidia/pytorch:23.10-py3

WORKDIR /app

COPY requirements.txt /app

RUN python -m pip install -r requirements.txt && python -m pip uninstall -y transformer-engine

COPY warmer.py .

ENV MODEL=meetkai/functionary-small-v2.2

RUN python warmer.py $MODEL

COPY . /app

EXPOSE 8000

ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:256

CMD python server_vllm.py --model $MODEL --host 0.0.0.0  --dtype=half --max-model-len=1024 --gpu-memory-utilization=1.0

