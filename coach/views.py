import json, os, re, time
from collections import Counter
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from .models import Transcript

def home(request):
    return render(request, "coach/index.html")

def valid_owner(value):
    return isinstance(value, str) and 12 <= len(value) <= 80 and re.fullmatch(r"[a-zA-Z0-9_-]+", value) is not None

def fallback_grammar(text):
    corrected = text
    rules = [
        (r"\bI am agree\b", "I agree", "verb form", "Use “agree” as a verb; do not add “am”."),
        (r"\bI didn't went\b", "I didn't go", "past tense", "After “didn't”, use the base form of the verb."),
        (r"\bI didn't saw\b", "I didn't see", "past tense", "After “didn't”, use the base form: “see”, not “saw”."),
        (r"\byesterday I go\b", "yesterday I went", "past tense", "Use the past tense for a completed action yesterday."),
        (r"\blast week I go\b", "last week I went", "past tense", "Use the past tense for a completed action last week."),
        (r"\bhe don't\b", "he doesn't", "subject-verb agreement", "Use “doesn't” with he, she, or it."),
        (r"\bshe don't\b", "she doesn't", "subject-verb agreement", "Use “doesn't” with he, she, or it."),
        (r"\bit don't\b", "it doesn't", "subject-verb agreement", "Use “doesn't” with he, she, or it."),
        (r"\bhe go to\b", "he goes to", "subject-verb agreement", "In the present simple, add -s/-es with he, she, or it."),
        (r"\bshe go to\b", "she goes to", "subject-verb agreement", "In the present simple, add -s/-es with he, she, or it."),
        (r"\bmore better\b", "better", "comparatives", "“Better” already expresses comparison; avoid “more better”."),
        (r"\bdiscuss about\b", "discuss", "word choice", "“Discuss” takes a direct object: “discuss the issue”."),
    ]
    found = []
    for pattern, replacement, category, explanation in rules:
        if re.search(pattern, corrected, flags=re.I):
            corrected = re.sub(pattern, replacement, corrected, flags=re.I)
            found.append({"category": category, "explanation": explanation, "suggestion": replacement})
    corrected = re.sub(r"\s+", " ", corrected).strip()
    if corrected and corrected[-1] not in ".!?":
        corrected += "."
    return {"corrected_text": corrected, "corrections": found,
            "note": "Starter rule-based analysis. Add OPENAI_API_KEY for full AI grammar feedback."}

def openai_grammar(text):
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.responses.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
        input=[
            {"role": "system", "content": (
                "You are a careful spoken-English tutor. Analyze the user's English transcript. "
                "Do not invent errors; distinguish genuine grammar errors from optional style suggestions. "
                "Preserve meaning and conversational voice. Return valid JSON only with keys "
                "corrected_text (string), corrections (array of objects with category, original, "
                "suggestion, explanation), and daily_tip (short string). Do not diagnose pronunciation "
                "from text. If the sentence is correct, say so."
            )},
            {"role": "user", "content": text},
        ],
    )
    raw = response.output_text
    # Responses are requested as JSON in the instruction; tolerate fenced output.
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I)
    data = json.loads(raw)
    if not isinstance(data.get("corrected_text"), str) or not isinstance(data.get("corrections"), list):
        raise ValueError("Unexpected AI response format")
    data.setdefault("daily_tip", "Review one corrected sentence and say it aloud.")
    return data

@csrf_exempt
@require_POST
def analyze(request):
    # Lightweight per-IP throttle; production should use a shared cache/rate limiter.
    ip = request.META.get("REMOTE_ADDR", "unknown")
    key = "analyze:" + ip
    count = cache.get(key, 0)
    if count >= 30:
        return JsonResponse({"error": "Rate limit reached. Try again later."}, status=429)
    cache.set(key, count + 1, 3600)
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    text = payload.get("text", "")
    if not isinstance(text, str) or not text.strip() or len(text) > 12000:
        return JsonResponse({"error": "Enter a sentence or passage up to 12,000 characters."}, status=400)
    if os.environ.get("OPENAI_API_KEY"):
        try:
            result = openai_grammar(text.strip())
            result["engine"] = "AI"
            return JsonResponse(result)
        except Exception:
            # Do not expose provider errors or secrets to public users.
            result = fallback_grammar(text.strip())
            result["note"] = "AI service unavailable; showing starter rule-based suggestions."
            result["engine"] = "Fallback"
            return JsonResponse(result)
    result = fallback_grammar(text.strip())
    result["engine"] = "Fallback"
    return JsonResponse(result)

@csrf_exempt
@require_http_methods(["GET", "POST", "DELETE"])
def transcripts(request):
    if request.method == "GET":
        owner = request.GET.get("owner", "")
    else:
        try:
            payload = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        owner = payload.get("owner", "")
    if not valid_owner(owner):
        return JsonResponse({"error": "A valid browser key is required."}, status=400)
    if request.method == "GET":
        qs = Transcript.objects.filter(owner_key=owner)[:100]
        items = [{"id": x.id, "original_text": x.original_text, "corrected_text": x.corrected_text,
                  "corrections": x.corrections, "created_at": x.created_at.isoformat()} for x in qs]
        return JsonResponse({"transcripts": items})
    if request.method == "POST":
        original = payload.get("original_text", "")
        corrected = payload.get("corrected_text", "")
        corrections = payload.get("corrections", [])
        if not isinstance(original, str) or not isinstance(corrected, str) or not original.strip() or len(original) > 12000 or len(corrected) > 12000:
            return JsonResponse({"error": "Transcript text is invalid or too long."}, status=400)
        if not isinstance(corrections, list):
            corrections = []
        obj = Transcript.objects.create(owner_key=owner, original_text=original.strip(),
            corrected_text=corrected.strip(), corrections=corrections[:100])
        return JsonResponse({"id": obj.id, "created_at": obj.created_at.isoformat()}, status=201)
    delete_id = payload.get("id")
    qs = Transcript.objects.filter(owner_key=owner)
    if delete_id is not None:
        try:
            delete_id = int(delete_id)
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid transcript id."}, status=400)
        qs.filter(id=delete_id).delete()
    else:
        qs.delete()
    return JsonResponse({"ok": True})
