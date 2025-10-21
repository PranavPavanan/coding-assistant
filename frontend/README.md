# RAG GitHub Assistant - Frontend

A pure HTML, CSS, and JavaScript frontend for the RAG GitHub Assistant application.

## Features

- **Repository Search**: Search and select GitHub repositories
- **Repository Indexing**: Index repositories for AI-powered queries
- **AI Chat Interface**: Ask questions about indexed code with context awareness
- **Conversation Management**: Multiple chat conversations with tabbed interface
- **Real-time Progress**: Live indexing progress updates
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Mode Support**: Automatic dark mode based on system preference

## Quick Start

### Option 1: Python HTTP Server (Recommended)
```bash
cd frontend
python -m http.server 5173
```
Open http://localhost:5173 in your browser.

### Option 2: Node.js HTTP Server
```bash
cd frontend
npx http-server -p 5173
```

### Option 3: Any Static File Server
Serve the `frontend/` directory with any static file server.

## File Structure

```
frontend/
├── index.html          # Main HTML file
├── styles.css          # All CSS styles
├── app.js             # JavaScript application logic
├── package.json       # Package configuration
└── README.md          # This file
```

## API Integration

The frontend communicates with the backend API at `/api` endpoints:

- `GET /api/health` - Health check
- `POST /api/search/repositories` - Search GitHub repositories
- `POST /api/index/start` - Start repository indexing
- `GET /api/index/status/{task_id}` - Get indexing status
- `GET /api/index/stats` - Get index statistics
- `DELETE /api/index/current` - Clear current index
- `POST /api/chat/query` - Send chat query

## Browser Support

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Development

No build process required! Just edit the files and refresh your browser.

### Key Components

- **RAGApp Class**: Main application controller
- **State Management**: Centralized state in `this.state`
- **API Client**: Built-in fetch-based API client
- **UI Updates**: Direct DOM manipulation for performance

### Adding Features

1. Add HTML structure to `index.html`
2. Add styles to `styles.css`
3. Add functionality to `app.js` in the `RAGApp` class

## Production Deployment

1. Copy all files to your web server
2. Ensure the backend API is accessible at `/api`
3. Configure CORS if needed
4. Set up HTTPS for production use

## License

MIT License - see LICENSE file for details.