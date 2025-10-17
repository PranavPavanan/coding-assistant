# CodeLlama-7B Setup Guide

This guide will help you set up the CodeLlama-7B model for the RAG GitHub Assistant.

## Quick Setup Steps

### 1. Download the Model

You're downloading from: https://huggingface.co/pranav-pvnn/codellama-7b-python-ai-assistant-F16-GGUF

### 2. Place the Model File

Once downloaded, move the `.gguf` file to:
```
backend/models/
```

Example:
```
backend/models/codellama-7b-python.F16.gguf
```

### 3. Update Configuration

Edit `backend/.env` and update the `MODEL_PATH` to match your filename:

```bash
MODEL_PATH=./models/codellama-7b-python.F16.gguf
```

**Important:** Make sure the filename in `.env` exactly matches your downloaded file!

### 4. Install Python Dependencies

Make sure llama-cpp-python is installed:

```bash
cd backend
pip install llama-cpp-python
```

Or install all requirements:

```bash
cd backend
pip install -r requirements.txt
```

### 5. Start the Backend Server

```bash
cd backend
python -m uvicorn src.main:app --reload --port 8000
```

### 6. Verify Model Loading

When the server starts, you should see:

```
============================================================
🚀 Starting RAG GitHub Assistant...
============================================================

📍 Model path: backend\models\codellama-7b-python.F16.gguf
Loading CodeLlama model from backend/models/codellama-7b-python.F16.gguf...
This may take a few minutes on first load...
✓ CodeLlama model loaded successfully!

✅ RAG Service initialized successfully!
   CodeLlama model is ready for queries.

============================================================
```

## Troubleshooting

### Model Not Loading

If you see "⚠️ RAG Service running in MOCK mode":

1. **Check file exists:**
   ```bash
   ls backend/models/
   ```

2. **Verify filename matches `.env`:**
   - Look at the actual filename in `backend/models/`
   - Update `MODEL_PATH` in `backend/.env` to match exactly

3. **Check file permissions:**
   - Make sure the file is readable
   - Not corrupted during download

### Performance Tips

**CPU-Only Setup:**
- The model will run on CPU by default
- First query may take 10-30 seconds to load
- Subsequent queries are faster (2-5 seconds)

**GPU Acceleration (Optional):**
Edit `backend/src/services/rag_service.py` line ~67:
```python
n_gpu_layers=35,  # Increase for GPU (was 0 for CPU)
```

Requires GPU-enabled llama-cpp-python:
```bash
pip uninstall llama-cpp-python
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python
```

### Memory Requirements

- **F16 Model:** ~14GB RAM required
- **Q4 Model:** ~4-6GB RAM (recommended for most systems)
- **Q8 Model:** ~7-9GB RAM (good balance)

If you have memory issues, download a quantized version (Q4_K_M or Q8_0).

## Testing the Model

1. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

2. Navigate to http://localhost:3000

3. Go to the "Chat" tab

4. Ask a question like:
   - "Explain how this codebase works"
   - "What are the main components?"
   - "Show me the API endpoints"

5. You should get AI-generated responses from CodeLlama!

## Model Information

- **Model:** CodeLlama-7B Python Assistant
- **Format:** GGUF (optimized for llama.cpp)
- **Specialization:** Python code analysis and explanation
- **Context Window:** 4096 tokens
- **License:** Llama 2 Community License

## Next Steps

Once the model is working:

1. **Index a repository** in the "Search" tab
2. **Ask questions** about the code in the "Chat" tab
3. The model will analyze the code and provide intelligent responses

Enjoy your AI-powered code assistant! 🚀
