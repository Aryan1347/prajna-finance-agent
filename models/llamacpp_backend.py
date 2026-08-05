import os
from models.base_model import BaseModel

class LlamaCppBackend(BaseModel):
    def __init__(self):
        self.model_path = os.getenv(
            "LLAMACPP_MODEL_PATH",
            os.path.expanduser("~/models/phi-3-mini-q4.gguf")
        )
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            from llama_cpp import Llama
            self._llm = Llama(
                model_path=self.model_path,  # path to your .gguf file
                n_ctx=4096,                  # context window — max tokens it can "see" at once
                n_gpu_layers=-1,
                n_threads=os.cpu_count(),    # use all CPU cores for inference
                use_mmap=True,               # memory-mapped file: weights stay on disk, OS pages them into RAM only as needed — so a 4GB model doesn't need 4GB RAM upfront
                use_mlock=False,             # mlock pins RAM pages so OS can't swap them out. False = OS can swap if needed (safer on low RAM)
                verbose=False,               # suppress llama.cpp's wall of startup logs
            )
        return self._llm

    def is_available(self) -> bool:
        return os.path.exists(self.model_path)

    def generate(self, prompt: str, schema: dict | None = None) -> str:
        llm = self._get_llm()
        # llama-cpp-python doesn't support JSON schema natively here;
        # we inject a schema hint into the prompt instead
        if schema:
            prompt += f"\n\nRespond ONLY with valid JSON matching this schema:\n{schema}"
        out = llm(
            prompt,
            max_tokens=150,
            temperature=0.1,
            stop=["</s>", "<|end|>", "<|endoftext|>", "<|assistant|>"],
        )
        return out["choices"][0]["text"].strip()