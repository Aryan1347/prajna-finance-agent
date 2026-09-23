# llamacpp_backend.py

import os
from models.base_model import BaseModel

def get_optimal_gpu_layers() -> int:
    """
    Dynamically select n_gpu_layers based on available VRAM.
    Tested values during Prajna development:
      0 layers  -> 48-60s (pure CPU)
      8 layers  -> 35-40s (VRAM ~1.8GB)
      16 layers -> 22-28s (VRAM ~2.8GB)
      24 layers -> 14-18s (VRAM ~3.4GB)
      28 layers -> 12-15s (VRAM ~3.7GB)
      -1 layers -> 8-12s  (VRAM ~3.9GB, all 33 layers on GPU)
    Final value: -1 on RTX 3050 4GB with Q4_K_M quant (2.3GB model).
    """
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3
        )
        free_vram_mb = int(result.stdout.strip().split("\n")[0])

        if free_vram_mb >= 3500:
            return -1    # full offload, all 33 layers
        elif free_vram_mb >= 3000:
            return 28
        elif free_vram_mb >= 2500:
            return 24
        elif free_vram_mb >= 2000:
            return 16
        elif free_vram_mb >= 1000:
            return 8
        else:
            return 0     # CPU fallback

    except Exception:
        # nvidia-smi not found or no GPU -- full CPU
        return 0


class LlamaCppBackend(BaseModel):
    def __init__(self):
        self.model_path = os.getenv(
            "LLAMACPP_MODEL_PATH",
            os.path.expanduser("~/models/phi-3-mini-q4.gguf")
        )
        self._llm = None
        self._gpu_layers = get_optimal_gpu_layers()

    def _get_llm(self):
        if self._llm is None:
            from llama_cpp import Llama
            self._llm = Llama(
                model_path=self.model_path, # path to your .gguf file
                n_ctx=4096,   # context window — max tokens it can "see" at once
                n_gpu_layers=self._gpu_layers,   
                n_threads=os.cpu_count(),  # use all CPU cores for inference
                use_mmap=True,    # memory-mapped file: weights stay on disk, OS pages them into RAM only as needed — so a 4GB model doesn't need 4GB RAM upfront
                use_mlock=False,   # mlock pins RAM pages so OS can't swap them out. False = OS can swap if needed (safer on low RAM)
                verbose=False,   # suppress llama.cpp's wall of startup logs
            )
            print(f"[LlamaCpp] Loaded with n_gpu_layers={self._gpu_layers}")
        return self._llm

    def is_available(self) -> bool:
        return os.path.exists(self.model_path)

    def generate(self, prompt: str, schema: dict | None = None, max_tokens: int = 150) -> str:
        llm = self._get_llm()
        if schema:
            prompt += f"\n\nRespond ONLY with valid JSON matching this schema:\n{schema}"
        out = llm(
            prompt,
            max_tokens=max_tokens,
            temperature=0.1,
            stop=["</s>", "<|end|>", "<|endoftext|>", "<|assistant|>"],
        )
        return out["choices"][0]["text"].strip()
