
import os
from pathlib import Path

# منع محاولة تحميل ملفات من الإنترنت
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from sentence_transformers import SentenceTransformer

# تحديد مسار الموديل
PROJECT_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_DIR / "knowledge_base" / "models" / "multilingual-e5-small"

print("Loading local model...")

model = SentenceTransformer(
    str(MODEL_DIR),
    trust_remote_code=False
)

print("Model loaded successfully!")

# اختبار تحويل نصوص إلى Embeddings
texts = [
    "query: What are the risk factors for breast cancer?",
    "passage: Breast cancer risk can be influenced by age and family history."
]

embeddings = model.encode(
    texts,
    normalize_embeddings=True
)

print("Embeddings generated successfully!")
print("Shape:", embeddings.shape)
print("First 5 values:", embeddings[0][:5])
