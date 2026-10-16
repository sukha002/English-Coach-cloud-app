# Quick smoke test
- Home page loads.
- Enter `Yesterday I go to work`, click Check grammar; fallback should suggest `Yesterday I went to work`.
- Save to cloud, refresh history; the transcript should appear.
- Click Delete my history; refresh should show no saved transcripts.
- With `OPENAI_API_KEY` configured, grammar analysis should use the AI provider; otherwise fallback is expected.
