# Asana Opus - AI-Powered Meeting Transcript to Task Converter

Transform your meeting transcripts into actionable Asana tasks using AI. Upload a PDF transcript from Grain, Gong, Otter, or similar tools, and let AI analyze it to extract action items and automatically create tasks in your Asana projects.

## Features

- 📄 **PDF Transcript Processing**: Extract text from meeting transcript PDFs
- 🤖 **AI-Powered Analysis**: Uses Google Gemini to identify action items, participants, and key decisions
- ✅ **Automatic Task Creation**: Creates tasks directly in your Asana projects
- 🎯 **Customer/Project Mapping**: Organize tasks by customer or project
- 🚀 **Simple Web Interface**: User-friendly Streamlit application

## Prerequisites

- Python 3.8 or higher
- Asana account with Personal Access Token
- Google Gemini API key
- Meeting transcripts in PDF format

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Atiwari330/asana_test1.git
cd asana_test1
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys:
# - ASANA_ACCESS_TOKEN: Your Asana Personal Access Token
# - GEMINI_API_KEY: Your Google Gemini API key
```

4. **Configure customers:**
Edit `customers.json` to add your customers/projects and their Asana project IDs:
```json
{
  "customers": {
    "Your Customer Name": {
      "asana_project_id": "YOUR_ASANA_PROJECT_ID",
      "aliases": ["Alternative Name"],
      "description": "Customer description"
    }
  }
}
```

## Getting API Keys

### Asana Personal Access Token
1. Log into Asana and go to Settings → Apps → Manage Developer Apps
2. Click "+ Create new token"
3. Enter a description and click "Create token"
4. Copy the token (you'll only see it once!)

### Google Gemini API Key
1. Visit [Google AI Studio](https://ai.google.dev)
2. Sign in with your Google account
3. Click "Get API key" → "Create API key"
4. Copy your API key

### Finding Asana Project IDs
1. Open your Asana project in a web browser
2. The URL will be: `https://app.asana.com/0/PROJECT_ID/...`
3. Copy the PROJECT_ID number

## Usage

1. **Start the application:**
```bash
streamlit run app.py
```

2. **Open your browser:**
Navigate to `http://localhost:8501`

3. **Use the application:**
   - Select a customer/project from the dropdown
   - Upload a PDF transcript
   - Review the extracted action items
   - Click "Create Tasks in Asana" to create the tasks

## Application Workflow

1. **Upload**: Select customer and upload PDF transcript
2. **Extract**: Text is automatically extracted from the PDF
3. **Analyze**: AI analyzes the transcript to identify:
   - Action items with titles and descriptions
   - Meeting participants
   - Key decisions made
   - Meeting summary
4. **Create**: Tasks are created in the specified Asana project

## Project Structure

```
asana_opus/
├── app.py                  # Main Streamlit application
├── src/
│   ├── pdf_processor.py    # PDF text extraction
│   ├── gemini_analyzer.py  # AI transcript analysis
│   └── asana_client.py     # Asana API integration
├── customers.json          # Customer/project configuration
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── docs/                  # Documentation
```

## Configuration

### customers.json
Maps customer names to Asana project IDs:
```json
{
  "customers": {
    "Customer Name": {
      "asana_project_id": "1234567890123456",
      "aliases": ["Alt Name"],
      "description": "Description"
    }
  }
}
```

### Environment Variables
- `ASANA_ACCESS_TOKEN`: Your Asana Personal Access Token
- `GEMINI_API_KEY`: Your Google Gemini API key
- `DEBUG_MODE`: Set to "true" for debug logging (optional)
- `MAX_FILE_SIZE_MB`: Maximum PDF file size in MB (default: 50)

## Troubleshooting

### "Missing API keys" error
- Ensure you've created a `.env` file (not `.env.example`)
- Check that your API keys are correctly added to `.env`

### "Invalid PDF file" error
- Ensure the file is a valid PDF
- Check that the file size is under the limit (default 50MB)

### No tasks created
- Verify the Asana project ID in `customers.json`
- Check that your Asana token has write permissions
- Review the action items extracted by AI

### Connection test fails
- Verify your API keys are correct
- Check your internet connection
- Ensure your Asana token hasn't expired

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Adding New Customers
1. Edit `customers.json`
2. Add the customer with their Asana project ID
3. Restart the application

### Customizing AI Prompts
Edit `src/gemini_analyzer.py` to modify how the AI analyzes transcripts.

## Security Notes

- Never commit your `.env` file to version control
- Keep your API keys secure and rotate them regularly
- The `.gitignore` file is configured to exclude sensitive files

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues or questions, please create an issue on GitHub.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io)
- Powered by [Google Gemini](https://ai.google.dev)
- Integrated with [Asana](https://asana.com)

---

Made with ❤️ for Opus Behavioral Health