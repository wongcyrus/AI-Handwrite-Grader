# Vertex AI Express Mode Setup Guide

This project uses **Vertex AI Express Mode** with API key authentication for simplified access to Google's Generative AI models.

## Quick Start

### 1. Get Your API Key

Visit [Google AI Studio](https://aistudio.google.com/apikey) and:
- Sign in with your Google account
- Click "Get API Key" or "Create API Key"
- Copy the generated API key

### 2. Configure Environment Variables

Edit the `.env` file in the project root and add your API key:

```bash
# Vertex AI Express Mode API Key
GOOGLE_GENAI_API_KEY=YOUR_ACTUAL_API_KEY_HERE
```

**Note:** Project ID and location are not needed when using API key authentication.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Notebook

Open `notebbooks/question_annotations_gemini.ipynb` and run the cells in order.

## Migration from OAuth to API Key

### What Changed?

| Before (OAuth/ADC) | After (Express Mode) |
|-------------------|----------------------|
| `pip install google-cloud-aiplatform` | `pip install google-genai` |
| `vertexai.init(project=..., location=...)` | `genai.Client(vertexai=True, api_key=...)` |
| Requires gcloud CLI authentication | Only needs API key |
| Service account JSON files | Simple API key string |
| `GOOGLE_APPLICATION_CREDENTIALS` env var | `GOOGLE_GENAI_API_KEY` env var |

### Code Comparison

**Before:**
```python
import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project=project_id, location="us-central1")
model = GenerativeModel("gemini-1.5-pro-002")
```

**After:**
```python
from google import genai
import os

API_KEY = os.getenv("GOOGLE_GENAI_API_KEY")
client = genai.Client(vertexai=True, api_key=API_KEY)

# Use client.models.generate_content() or generate_content_stream()
```

## Troubleshooting

### Error: "Please set your GOOGLE_GENAI_API_KEY"

**Solution:** Make sure you've added your API key to the `.env` file:
```bash
GOOGLE_GENAI_API_KEY=AIzaSy...your-key-here
```

### Error: "Invalid API key"

**Solutions:**
1. Verify your API key is correct (no extra spaces or quotes)
2. Check that the API key is active at https://aistudio.google.com/apikey
3. Ensure you have the correct permissions/quota enabled

### Error: "Module 'google.genai' not found"

**Solution:** Install the package:
```bash
pip install google-genai
```

## Security Best Practices

1. **Never commit `.env` file** - It's already in `.gitignore`
2. **Never hardcode API keys** - Always use environment variables
3. **Rotate keys regularly** - Generate new keys periodically
4. **Use separate keys** - Different keys for dev/staging/production
5. **Restrict API key usage** - Configure API restrictions in Google Cloud Console

## Resources

- [Vertex AI Express Mode Documentation](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/express-mode/vertex-ai-express-mode-api-quickstart)
- [Google AI Studio](https://aistudio.google.com/)
- [API Key Management](https://aistudio.google.com/apikey)

## Support

For issues with:
- **API keys**: Visit [Google AI Studio](https://aistudio.google.com/apikey)
- **Billing/Quota**: Check [Google Cloud Console](https://console.cloud.google.com/)
- **Code issues**: Review the notebook cells and error messages
