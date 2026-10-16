# English Coach Cloud MVP

A responsive Django web app for Android and desktop. Includes browser speech recognition where supported, editable transcripts, grammar analysis, cloud transcript storage, and daily summary.

## What works in this MVP
- Responsive browser UI.
- Speech-to-text through the browser Web Speech API where available.
- Editable transcript before analysis.
- Grammar analysis through OpenAI Responses API when `OPENAI_API_KEY` is configured.
- Rule-based fallback when no API key is configured or the AI service fails.
- Cloud database transcript history scoped by a browser-generated owner key.
- Delete-all history control.
- Audio is not uploaded by this app's backend and no audio file is stored by this app.

## Important privacy and public-access warning
The website is publicly reachable and has no login, as requested. Transcript data is stored in the cloud and separated using a random browser key in local storage. This is a lightweight MVP convenience, **not secure authentication**: if someone obtains the key, they could access that browser's records. Do not use this for sensitive conversations. Before production use, add real authentication, per-user authorization, robust rate limiting, retention controls, monitoring, and a privacy notice. Browser speech recognition may transmit audio to the browser provider for recognition; this app does not control that service. Do not record other people without appropriate consent.

## Run locally on Windows
1. Install Python 3.11+ from https://www.python.org/downloads/ (select "Add Python to PATH").
2. Extract this ZIP.
3. Open PowerShell in the extracted `english_coach_cloud` folder.
4. Run:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   py manage.py migrate
   py manage.py runserver
   ```
5. Open http://127.0.0.1:8000. Browser speech recognition generally requires HTTPS or localhost; microphone access varies by browser.

## Configure AI
Set `OPENAI_API_KEY` in the environment where Django runs. Optional `OPENAI_MODEL` defaults to `gpt-4.1-mini`. Keep the API key server-side; never place it in JavaScript or commit it to Git.

PowerShell for the current session:
```powershell
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_MODEL="gpt-4.1-mini"
py manage.py runserver
```
Without a key, the app uses a small rule-based fallback and should not be mistaken for full AI grammar checking.

## Deploy (example: Render + PostgreSQL)
1. Create a private GitHub repository and upload these project files.
2. In Render, create a PostgreSQL database and a Python web service connected to that repository.
3. Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
4. Start command: `gunicorn config.wsgi:application`
5. Set environment variables:
   - `DJANGO_SECRET_KEY`: a long random secret
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: your Render hostname, e.g. `your-service.onrender.com`
   - `CSRF_TRUSTED_ORIGINS`: `https://your-service.onrender.com`
   - `DATABASE_URL`: Render's internal PostgreSQL connection URL
   - `OPENAI_API_KEY`: your API key (optional for fallback)
   - `OPENAI_MODEL`: `gpt-4.1-mini` (optional)
6. Deploy. Check logs and test on desktop and Android Chrome.
7. Before inviting others, implement login and user-level authorization. Public access to the website must not mean public access to users' transcript records.

Django production guidance: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

## API endpoints
- `POST /api/analyze/` body `{ "text": "..." }`
- `GET /api/transcripts/?owner=<browser-key>`
- `POST /api/transcripts/` body `{ "owner": "...", "original_text": "...", "corrected_text": "...", "corrections": [] }`
- `DELETE /api/transcripts/` body `{ "owner": "..." }` to delete all; add `"id": 123` to delete one

## Next steps toward wearable support
1. Keep the wearable as a separate audio source; do not couple the grammar engine to a specific device.
2. Start with a commercial microphone that works with Android/desktop browser input.
3. For custom hardware, use a development board with supported audio capture and Wi-Fi/Bluetooth capabilities, with a physical mute switch and recording indicator.
4. Add a consent-based short-session upload flow. If sending audio to a transcription API, stream it only for processing and delete temporary buffers. The current MVP does not accept audio uploads from a wearable.
