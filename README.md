<<<<<<< HEAD
# RAG Chatbot

A Retrieval-Augmented Generation chatbot that answers questions using only
uploaded PDF, Word, and text documents.

Stack: FastAPI · ChromaDB · SentenceTransformers · Ollama (Llama 3.x) · vanilla HTML/JS

## 1. Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running locally

Pull the model once:
```bash
ollama pull llama3.1
```
Make sure Ollama is running (it usually runs as a background service after install;
if not, start it with `ollama serve`).

## 2. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

The API will be live at `http://localhost:8000`.
Interactive API docs (Swagger UI) at `http://localhost:8000/docs`.

First run will download the `all-MiniLM-L6-v2` embedding model (~90MB) —
this happens once and is cached locally.

## 3. Frontend setup

No build step needed — it's a single static HTML file.

```bash
cd frontend
python3 -m http.server 5500
```

Then open `http://localhost:5500` in your browser.

(If you open `index.html` directly via `file://`, some browsers block the
fetch calls to `localhost:8000` due to CORS — serving it over `http://`
avoids that.)

## 4. Using it

1. Upload a `.pdf`, `.docx`, or `.txt` file in the left sidebar.
2. Wait for the "indexed (N chunks)" confirmation.
3. Ask a question in the chat box.
4. Each answer shows the source document(s) and lets you expand the
   retrieved chunks that were used to generate it.

## 5. Configuration

Edit `backend/.env` to change:

| Variable | Purpose |
|---|---|
| `OLLAMA_MODEL` | which local model to use (default `llama3.1`) |
| `EMBEDDING_MODEL` | SentenceTransformers model name |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | text splitting parameters |
| `TOP_K` | number of chunks retrieved per query |

## 6. Project structure

```
rag-chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app + routes registration
│   │   ├── config.py                # env-driven settings
│   │   ├── api/                     # route handlers
│   │   ├── core/                    # document loading, chunking, embeddings, vector store, retriever, LLM
│   │   ├── models/                  # Pydantic schemas
│   │   ├── services/                # RAG pipeline orchestration, chat history
│   │   └── db/                      # SQLite chat history persistence
│   ├── data/
│   │   ├── uploads/                 # raw uploaded files
│   │   └── chroma_db/               # persisted vector store
│   ├── requirements.txt
│   ├── .env
│   └── run.py
└── frontend/
    └── index.html                   # upload UI + chat UI (self-contained)
```

## 7. Troubleshooting

- **"Could not connect to Ollama"** → Ollama isn't running, or the model
  hasn't been pulled. Run `ollama list` to check installed models.
- **CORS errors in browser console** → make sure you're serving the frontend
  via `http://localhost:5500` (not `file://`), and that `FRONTEND_ORIGIN=*`
  is set in `.env` (default).
- **Slow first upload** → the embedding model downloads on first use; after
  that it's cached and fast.
- **"No extractable text found"** → likely a scanned/image-only PDF with no
  text layer. This basic pipeline doesn't do OCR.
=======
# custom_rag_engine
>>>>>>> 25f5f05643be3dcf73276232f9c1d093e4bd2c0e
