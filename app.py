import os
import json
import anthropic
from flask import Flask, request, jsonify, render_template, Response, stream_with_context

app = Flask(__name__)

PROMPT_TEMPLATE = """You are an expert teacher. The user has provided this input: "{topic}"

1. Infer the domain of knowledge (e.g. history, biology, literature, programming, philosophy...).
2. Generate exactly 20 multiple-choice questions to test knowledge on that subject.

Respond with ONLY a valid JSON object (no markdown, no commentary) in this exact structure:
{{
  "domain": "<inferred domain>",
  "subject": "<concise subject title>",
  "questions": [
    {{
      "question": "<question text>",
      "options": {{
        "A": "<option A>",
        "B": "<option B>",
        "C": "<option C>",
        "D": "<option D>"
      }},
      "correct": "<A|B|C|D>",
      "explanation": "<one-sentence explanation of the correct answer>"
    }}
  ]
}}

Requirements:
- All 20 questions must be unique and cover different aspects of the subject.
- One and only one option is correct per question.
- Options should be plausible; avoid obviously wrong distractors.
- Questions should range from easy to challenging.
"""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json()
    topic = (data or {}).get("topic", "").strip()
    if not topic:
        return jsonify({"error": "Please enter a topic."}), 400

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"error": "ANTHROPIC_API_KEY is not configured on the server."}), 500

    def event_stream():
        client = anthropic.Anthropic(api_key=api_key)
        full_text = ""
        try:
            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(topic=topic)}],
            ) as stream:
                for text in stream.text_stream:
                    full_text += text
                    yield ": ping\n\n"  # SSE keepalive — prevents proxy/nginx timeouts
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return

        try:
            quiz = json.loads(full_text)
        except json.JSONDecodeError:
            start = full_text.find("{")
            end = full_text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    quiz = json.loads(full_text[start:end])
                except Exception:
                    yield f"data: {json.dumps({'error': 'Failed to parse quiz. Please try again.'})}\n\n"
                    return
            else:
                yield f"data: {json.dumps({'error': 'Failed to parse quiz. Please try again.'})}\n\n"
                return

        yield f"data: {json.dumps(quiz)}\n\n"

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
