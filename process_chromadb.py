import chromadb
import time
from transformers import AutoTokenizer, AutoModel
import torch
import pdfplumber
import os
import uuid
import logging
from docx import Document  # إضافة دعم لملفات Word

# إعداد الـ logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting the script...")

# تحميل النموذج والتوكينيزر
tokenizer = AutoTokenizer.from_pretrained("Omartificial-Intelligence-Space/Arabic-Triplet-Matryoshka-V2")
model = AutoModel.from_pretrained("Omartificial-Intelligence-Space/Arabic-Triplet-Matryoshka-V2")

# دالة لتوليد الـ embeddings
def generate_embeddings(texts):
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1)
    return embeddings.tolist()

# دالة لتحميل النصوص من ملفات PDF
def load_documents_from_pdfs(directory):
    documents = []
    metadatas = []
    for filename in os.listdir(directory):
        if filename.endswith('.pdf'):
            with pdfplumber.open(os.path.join(directory, filename)) as pdf:
                text = ''
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                if text:
                    documents.append(text)
                    metadatas.append({"source": filename})
    return documents, metadatas

# دالة لتحميل النصوص من ملفات Word (docx)
def load_documents_from_docx(directory):
    documents = []
    metadatas = []
    for filename in os.listdir(directory):
        if filename.endswith('.docx'):
            doc = Document(os.path.join(directory, filename))
            text = '\n'.join([para.text for para in doc.paragraphs])
            if text:
                documents.append(text)
                metadatas.append({"source": filename})
    return documents, metadatas

# الاتصال بـ ChromaDB
chroma_client = chromadb.HttpClient(host='localhost', port=8000)
logging.info("Chroma Server Heartbeat: %s", chroma_client.heartbeat())

collection_name = "test-collection"

# التحقق من وجود الـ collection وإنشاؤها إذا لم تكن موجودة
try:
    collection = chroma_client.get_collection(name=collection_name)
    logging.info(f"Collection '{collection_name}' already exists.")
except Exception as e:
    logging.info(f"Collection '{collection_name}' does not exist. Creating it...")
    collection = chroma_client.create_collection(name=collection_name)
    logging.info(f"Collection '{collection_name}' created.")

# تحميل النصوص من ملفات PDF و Word
pdf_documents, pdf_metadatas = load_documents_from_pdfs('/home/omar/Desktop/Test-files')
docx_documents, docx_metadatas = load_documents_from_docx('/home/omar/Desktop/Test-files')

# دمج النصوص من ملفات PDF و Word
documents = pdf_documents + docx_documents
metadatas = pdf_metadatas + docx_metadatas

# إضافة metadata إضافية مثل تاريخ الرفع
for metadata in metadatas:
    metadata["upload_date"] = "2024-01-01"  # تاريخ افتراضي
    metadata["category"] = "example_category"  # تصنيف افتراضي

# توليد الـ embeddings
embeddings = generate_embeddings(documents)
ids = [str(uuid.uuid4()) for _ in range(len(documents))]

# إضافة البيانات إلى ChromaDB
try:
    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    logging.info(f"Added {len(documents)} documents to the collection.")
except Exception as e:
    logging.error(f"Error adding documents: {e}")

if documents:
    query_text = "لفض البديلة الوسائل المنازعات"  # النص الجديد الذي تريد البحث عنه
    query_embedding = generate_embeddings([query_text])

    start_time = time.time()
    results = collection.query(query_embeddings=query_embedding, n_results=10, include=["embeddings", "metadatas", "documents"])
    end_time = time.time()

    logging.info("Query Results: %s", results)
    logging.info(f"Query took {end_time - start_time:.4f} seconds")
else:
    logging.warning("No documents found to query.")
