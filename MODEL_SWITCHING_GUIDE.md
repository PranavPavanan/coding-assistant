# Model Switching Guide

## Easy Model Switching

You can now easily switch between different models by changing just one line!

### Current Setup

Your model `Q4_K_M-00001-of-00001.gguf` is configured as the default "phi3-mini" model.

### How to Switch Models

#### Method 1: Edit config.py (Recommended)

In `backend/src/config.py`, change line 58:

```python
# Change this to switch models easily
DEFAULT_MODEL = "phi3-mini"  # Current model
```

Available options:
- `"phi3-mini"` - Your current model (Q4_K_M-00001-of-00001.gguf)
- `"codellama-7b"` - CodeLlama 7B model
- `"llama3.1-8b"` - Llama 3.1 8B model

#### Method 2: Use Environment Variable

Create a `backend/.env` file:

```env
MODEL_NAME=phi3-mini
```

### Adding New Models

To add a new model:

1. **Add model configuration** in `backend/src/config.py`:

```python
MODEL_CONFIGS = {
    "your-model-name": {
        "filename": "your-model-file.gguf",
        "context_length": 4096,
        "max_tokens": 256,
        "temperature": 0.7,
        "top_p": 0.95,
        "n_threads": 4,
        "n_gpu_layers": 0,
        "system_prompt": "Your custom system prompt...",
        "stop_tokens": ["</s>", "[INST]", "<|endoftext|>"]
    },
    # ... existing models
}
```

2. **Download the model** and place it in `backend/models/`

3. **Switch to the model** by changing `DEFAULT_MODEL` or `MODEL_NAME`

### Current Model Configuration

Your current model is configured with:
- **Context Length**: 4096 tokens
- **Max Tokens**: 256
- **Threads**: 4
- **Temperature**: 0.7
- **Top-p**: 0.95

### Testing the Setup

1. **Start the backend**:
   ```bash
   cd backend
   python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Check the logs** - you should see:
   ```
   Loading phi3-mini model from backend/models/Q4_K_M-00001-of-00001.gguf...
   SUCCESS: phi3-mini model loaded successfully!
   ```

3. **Test a query** to verify contextual awareness is working

### Benefits

- ✅ **Easy switching**: Change one line to switch models
- ✅ **Optimized settings**: Each model has its own optimal configuration
- ✅ **Contextual awareness**: All models support conversation management
- ✅ **Memory efficient**: Smaller models prevent system hangs
- ✅ **Flexible**: Easy to add new models

### Troubleshooting

If you get "Model file not found":
1. Check the filename in `MODEL_CONFIGS` matches your actual file
2. Make sure the file is in `backend/models/`
3. Verify the model name is correct

If the backend hangs:
1. Try a smaller model (reduce context_length)
2. Use fewer threads
3. Check available system memory
