# Quick Start Guide: RAG-Powered GitHub Repository Assistant

## Prerequisites

- **Python 3.9+** (Backend)
- **Node.js 18+** and npm/yarn (Frontend)
- **16GB RAM minimum** (32GB recommended for large repos)
- **50GB free disk space**
- **Git installed**
- **GitHub Personal Access Token** with `public_repo` scope

## Installation

### 1. Clone and Setup Repository
```bash
git clone <repository-url>
cd rag-github-assistant
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment
Create `backend/config.yaml` 
```yaml

model:
  name: "pranav-pvnn/codellama-7b-python-ai-assistant-F16-GGUF"
  max_context: 16384
  temperature: 0.7

indexing:
  max_files: 10000
  max_size_mb: 500
  chunk_size: 800
  chunk_overlap: 100

retrieval:
  top_k: 10
  hybrid_weight: 0.5
```

### 4. Frontend Setup
```bash
cd ../frontend
npm install
# or
yarn install
```

### 5. Configure Frontend Environment
Create `frontend/.env`:
```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Running the Application

### Start Backend
```bash
cd backend
# Activate virtual environment if not already
uvicorn main:app --reload --port 8000
```

### Start Frontend
```bash
cd frontend
npm run dev
# or
yarn dev
```

### Access Application
Open `http://localhost:3000` in your browser.

## First Use

1. **Repository Search Tab** (default view)
   - Enter: "Python HTTP library"
   - Click "Search Repositories"
   - Review top 3 matches
   - Click "Select" on desired repository

2. **Indexing Process**
   - Wait for indexing to complete (3-8 minutes)
   - Progress shown in real-time

3. **Chat Interface**
   - Switch to "Chat Interface" tab
   - Ask: "How does the Session class work?"
   - View AI-generated response with code examples

## Validation Tests

### Repository Search
- [ ] Search returns relevant repositories
- [ ] Repository details display correctly
- [ ] URL validation works for direct links

### Indexing
- [ ] Indexing completes without errors
- [ ] Progress updates in real-time
- [ ] Repository appears in chat context

### Chat Queries
- [ ] Questions return relevant responses
- [ ] Code snippets included in answers
- [ ] Follow-up questions maintain context

## Troubleshooting

### Backend Issues
- **Import errors**: Ensure all packages installed: `pip install -r requirements.txt`
- **Model loading fails**: Check RAM (16GB+ required), try smaller model
- **GitHub API errors**: Verify access token and rate limits

### Frontend Issues
- **Build fails**: Clear node_modules: `rm -rf node_modules && npm install`
- **API connection fails**: Check backend is running on port 8000
- **WebSocket errors**: Ensure backend supports WebSocket connections

### Performance Issues
- **Slow indexing**: Reduce max_files in config, use smaller repositories
- **Slow queries**: Check RAM usage, close other applications
- **Out of memory**: Reduce chunk_size or use CPU-only FAISS

## Development Mode

### Backend Development
```bash
cd backend
uvicorn main:app --reload --port 8000
# API docs available at http://localhost:8000/docs
```

### Frontend Development
```bash
cd frontend
npm run dev
# Hot reload enabled, changes reflect immediately
```

### Testing
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Configuration Options

### Model Selection
- **Default**: CodeLlama-7B (14GB RAM, best quality)
- **Lightweight**: CodeLlama-7B quantized (4GB RAM, reduced quality)
- **Custom**: Any GGUF format model (update config.yaml)

### Indexing Options
- **max_files**: Limit repository size (default: 10000)
- **max_size_mb**: Size limit in MB (default: 500)
- **chunk_size**: Token count per chunk (default: 800)
- **chunk_overlap**: Overlap between chunks (default: 100)

### Retrieval Options
- **top_k**: Number of chunks to retrieve (default: 10)
- **hybrid_weight**: Balance between BM25/FAISS (0.0-1.0, default: 0.5)