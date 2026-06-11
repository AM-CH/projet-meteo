#!/usr/bin/env python3
import os
import json
import sys
import anthropic

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


def generate_quiz(topic: str) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("\nGenerating your quiz, please wait...\n")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(topic=topic)}],
    )

    raw = message.content[0].text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON if wrapped in backticks
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(raw[start:end])
        print("Error: Could not parse the quiz response. Please try again.")
        sys.exit(1)


def print_separator():
    print("-" * 60)


def run_quiz(quiz: dict):
    domain = quiz.get("domain", "Unknown")
    subject = quiz.get("subject", "Unknown")
    questions = quiz.get("questions", [])

    print(f"Domain  : {domain}")
    print(f"Subject : {subject}")
    print(f"Questions: {len(questions)}")
    print_separator()
    input("Press Enter to start the quiz...")
    print()

    score = 0
    for i, q in enumerate(questions, 1):
        print(f"Question {i}/{len(questions)}")
        print(f"{q['question']}\n")
        for letter, text in q["options"].items():
            print(f"  {letter}. {text}")
        print()

        while True:
            answer = input("Your answer (A/B/C/D): ").strip().upper()
            if answer in ("A", "B", "C", "D"):
                break
            print("Please enter A, B, C, or D.")

        correct = q["correct"].upper()
        if answer == correct:
            print("Correct!\n")
            score += 1
        else:
            print(f"Wrong. The correct answer is {correct}.")
            print(f"Explanation: {q['explanation']}\n")

        print_separator()

    total = len(questions)
    percentage = round(score / total * 100)
    print(f"\nQuiz complete! Your score: {score}/{total} ({percentage}%)\n")

    if percentage >= 80:
        print("Excellent work!")
    elif percentage >= 60:
        print("Good effort — keep studying to improve!")
    else:
        print("Keep going — practice makes perfect!")


def main():
    print("=== Learning Quiz App ===\n")
    print("Enter a topic, a book title, or a question to get started.")
    topic = input("Topic / Book / Question: ").strip()
    if not topic:
        print("Please enter a topic.")
        sys.exit(1)

    quiz = generate_quiz(topic)
    run_quiz(quiz)


if __name__ == "__main__":
    main()
