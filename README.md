# HR Interview Assistant

A professional AI-powered HR interview application with real-time speech-to-text, resume analysis, and automated candidate evaluation.

## Features

- **Camera Integration**: Live video feed during interviews
- **Resume Analysis**: AI-powered PDF resume parsing and question generation
- **Speech-to-Text**: Real-time on-device speech recognition
- **Smart Q&A Flow**: Initial questions → Follow-up questions → Final rating
- **Candidate Rating**: Comprehensive evaluation based on resume and responses

## File Structure

```
hr-interview-app/
├── main.py                 # FastAPI backend application
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables
├── static/
│   └── index.html         # Frontend application
└── README.md              # Setup instructions
```

## Setup Instructions

### 1. Create Project Directory
```bash
mkdir hr-interview-app
cd hr-interview-app
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file and add your OpenAI API key:
```bash
OPENAI_API_KEY=your_actual_openai_api_key_here
HOST=0.0.0.0
PORT=8000
```

### 5. Create Static Directory
```bash
mkdir static
```

### 6. Add the HTML File
Place the `index.html` file in the `static/` directory.

### 7. Run the Application
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 8. Access the Application
Open your browser and navigate to: `http://localhost:8000`

## Usage Guide

1. **Start Camera**: Click "Start Camera" to enable video feed
2. **Upload Resume**: Upload a PDF resume for AI analysis
3. **Answer Questions**: Use speech-to-text or type responses
4. **Complete Interview**: Answer all initial and follow-up questions
5. **View Rating**: Get comprehensive candidate evaluation

## Technical Details

### Backend (FastAPI)
- Real-time WebSocket communication
- OpenAI GPT-4 integration for question generation and evaluation
- PDF processing with PyPDF2
- RESTful API endpoints for all operations

### Frontend (Vanilla JavaScript)
- Web Speech API for real-time speech recognition
- WebRTC for camera access
- Clean, professional UI with minimal design
- Responsive layout for different screen sizes

### Key Features
- **On-device Speech Recognition**: No audio data sent to servers
- **Progressive Interview Flow**: Structured Q&A process
- **Comprehensive Rating**: Multi-dimensional candidate evaluation
- **Professional Design**: Clean, minimal interface with blue accent color

## Browser Requirements

- Modern browsers supporting:
  - Web Speech API (Chrome, Edge, Safari)
  - WebRTC for camera access
  - ES6+ JavaScript features

## Security Notes

- OpenAI API keys are stored server-side only
- Audio processing happens entirely on-device
- No persistent storage of sensitive data (implement database for production)

## Production Considerations

- Add user authentication
- Implement proper database storage
- Add rate limiting and API protection
- Configure HTTPS and security headers
- Add comprehensive error handling and logging