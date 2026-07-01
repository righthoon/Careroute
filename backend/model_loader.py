import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

def load_model(model_id: str = MODEL_ID):
    print(f"[INFO] 모델 로딩 중: {model_id}")

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float16,   # 4-bit 대신 float16으로 로드
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    print("[INFO] 모델 로드 완료")
    return tokenizer, model