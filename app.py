import os
import json
import anthropic
from flask import Flask, request, jsonify, render_template

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

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(topic=topic)}],
    )

    raw = message.content[0].text.strip()
    try:
        quiz = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            quiz = json.loads(raw[start:end])
        else:
            return jsonify({"error": "Failed to parse quiz response. Please try again."}), 500

    return jsonify(quiz)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
