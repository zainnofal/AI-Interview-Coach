# AI Interview Coach

A fully voice-based agentic interviewer that:
- Speaks interview questions
- Listens to your answers
- Understands and evaluates your responses
- Gives spoken feedback — just like a real mock interview

## Features

- Modern React UI with a professional dark theme
- Job-specific interview questions for any role
- Voice-based interaction using OpenAI Text-to-Speech for realistic voices
- Speech-to-text transcription using OpenAI Whisper
- AI-powered response evaluation and feedback using GPT-3.5
- Manual recording controls for precise answer timing

![AI Interview Coach Screenshot](https://via.placeholder.com/800x450/1E1E1E/FFFFFF?text=AI+Interview+Coach)

## Requirements

- Python 3.8+
- OpenAI API key
- Required Python packages (see installation)

## Installation

1. Clone this repository
2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```
3. Update the `config.py` file with your API keys:
   ```python
   OPENAI_API_KEY = "your-openai-api-key"
   ```
4. Build the React frontend:
   ```
   cd frontend
   npm install
   npm run build
   ```

### Apple Silicon (M1/M2/M3) Compatibility

If you're using an Apple Silicon Mac, you might encounter compatibility issues with some packages:

1. **Sound Recording**: The application uses sounddevice and scipy for recording, which should be compatible with most systems, but may need special installation on Apple Silicon:
   ```
   conda create -n interview-coach python=3.9
   conda activate interview-coach
   pip install -r requirements.txt
   ```

## Usage

1. Run the Flask backend:
   ```
   python app.py
   ```
2. Open your browser and navigate to `http://localhost:5000`
3. Select a job role to start the interview
4. Listen to the question and click "Record Answer" when ready to respond
5. Speak your answer and click "Stop Recording" when finished
6. Listen to AI feedback and the next question

## Development

If you want to work on the React frontend:

1. Start the Flask backend:
   ```
   python app.py
   ```

2. In a new terminal, start the React development server:
   ```
   cd frontend
   npm install
   npm start
   ```

3. The React dev server will start on `http://localhost:3000` and proxy API requests to the Flask backend at `http://localhost:5000`

## Customization

### Changing the Theme

You can customize the dark theme by editing `frontend/src/theme.js`. The application uses Material UI, which makes it easy to adjust colors, typography, and component styling.

### Adding New Features

The React frontend is organized with components in the `frontend/src/components` directory and API services in `frontend/src/services`.

## License

MIT 