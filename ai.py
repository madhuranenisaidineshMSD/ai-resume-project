from google import genai
from google.genai import types
import json
import os

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def analyze_resume(resume_text, user_goal):

    prompt = f"""
    You are a senior software engineer and hiring manager.

    Evaluate the resume based on the user's goal.

    User goal: "{user_goal}"

    STRICT RULES:
    - Ignore personal information such as phoneNumber, email, location, etc.
    - Extract only relevant skills for this goal
    - Remove irrelevant tools [excel for backend, etc]
    - Identify real gaps
    - Generate roadmap only for missing fields
    - Make output DIFFERENT based on goal

    Return only JSON:

    {{
        "skills": [],
        "missing_skills": [],
        "roadmap": [],
        "interview_questions": []
    }}

    Resume:
    {resume_text}
    """

    try:

        models = [
            "gemini-3.8-flash",
            "gemini-3.7-flash",
            "gemini-3.5-flash-lite",
            "gemini-2.5-flash"
        ]

        for model in models:

            try:

                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3
                    )
                )

                content = response.text.strip()

                start = content.find("{")
                end = content.rfind("}") + 1

                return json.loads(
                    content[start:end]
                )

            except Exception:
                continue

        raise Exception("All Gemini models failed")

    except Exception as e:

        return {
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "error": str(e)
        }