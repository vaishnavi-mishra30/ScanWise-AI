
import os
import json
import re

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai


# ==========================================
# 1. APP SETUP
# ==========================================

app = Flask(__name__)
CORS(app)

# Load environment variables from backend/.env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

client = genai.Client(api_key=API_KEY) if API_KEY else None


# ==========================================
# 2. HOME ROUTE
# ==========================================

@app.route("/")
def home():
    return jsonify({
        "message": "ScanWise AI backend is running!",
        "gemini_configured": client is not None
    })


# ==========================================
# 3. PROFILE NORMALIZATION
# ==========================================

def normalize_profile(profile):

    profile = profile if isinstance(profile, dict) else {}

    conditions = profile.get("conditions", [])

    if isinstance(conditions, str):
        conditions = [conditions]

    if not conditions:
        condition = profile.get("condition", "")
        conditions = [condition] if condition else []

    other_conditions = profile.get("otherConditions", [])

    if isinstance(other_conditions, str):
        other_conditions = [other_conditions]

    conditions = conditions + other_conditions

    allergies = profile.get("allergies", [])
    goals = profile.get("goals", [])

    if isinstance(allergies, str):
        allergies = [allergies]

    if isinstance(goals, str):
        goals = [goals]

    return {
        "name": profile.get("name", ""),
        "age": profile.get("age", ""),
        "gender": profile.get("gender", ""),
        "conditions": conditions,
        "allergies": allergies,
        "goals": goals
    }


# ==========================================
# 4. PYTHON-BASED FOOD SCORING
# ==========================================

def calculate_score(ingredients, profile):

    text = ingredients.lower()

    score = 100
    risk_flags = []
    positive_indicators = []

    conditions = " ".join(profile["conditions"]).lower()
    allergies = [str(a).lower() for a in profile["allergies"]]

    # Risk ingredients

    risk_rules = {
        "trans fats": [
            "partially hydrogenated",
            "hydrogenated vegetable oil"
        ],
        "artificial sweeteners": [
            "aspartame",
            "sucralose",
            "saccharin",
            "acesulfame potassium"
        ],
        "preservatives": [
            "bha",
            "bht",
            "tbhq"
        ],
        "refined oils": [
            "palm oil",
            "refined soybean oil",
            "refined sunflower oil"
        ],
        "high-sodium additives": [
            "sodium nitrate",
            "sodium nitrite",
            "monosodium glutamate",
            "msg"
        ]
    }

    deductions = {
        "trans fats": 30,
        "artificial sweeteners": 20,
        "preservatives": 20,
        "refined oils": 10,
        "high-sodium additives": 15
    }

    for category, keywords in risk_rules.items():

        if any(word in text for word in keywords):
            score -= deductions[category]
            risk_flags.append(category)

    # Sugar detection

    sugar_words = [
        "sugar",
        "glucose syrup",
        "corn syrup",
        "fructose",
        "invert syrup",
        "sucrose"
    ]

    contains_sugar = any(word in text for word in sugar_words)

    if contains_sugar:
        risk_flags.append("added-sugar ingredient detected")

    # Sodium detection

    sodium_words = [
        "sodium",
        "salt",
        "sodium chloride"
    ]

    contains_sodium = any(word in text for word in sodium_words)

    if contains_sodium:
        risk_flags.append("sodium ingredient detected")

    # Condition-based rules

    if "diabetes" in conditions and contains_sugar:
        score = min(score, 49)

    score = max(0, min(100, score))
    risk_flags.append("sugar may be relevant to diabetes")

    if "hypertension" in conditions and contains_sodium:
        score -= 15
        risk_flags.append("sodium may be relevant to hypertension")

    # Allergy matching

    allergy_matches = []

    for allergy in allergies:
        if allergy and re.search(
            r"(?<![a-z])" + re.escape(allergy) + r"(?![a-z])",
            text
        ):
            allergy_matches.append(allergy)

    if allergy_matches:
        score = min(score, 20)
        risk_flags.append("possible allergy ingredient match")

    # Multiple risk flags

    if len(risk_flags) >= 3:
        score -= 10

    # Positive indicators

    positive_rules = {
        "fiber": ["fiber", "dietary fibre", "dietary fiber"],
        "whole grains": ["whole grain", "whole wheat", "oats"],
        "protein": ["protein", "whey protein"],
        "nuts": ["almonds", "walnuts", "peanuts"]
    }

    bonuses = {
        "fiber": 10,
        "whole grains": 10,
        "protein": 8,
        "nuts": 8
    }

    for category, keywords in positive_rules.items():

        if any(word in text for word in keywords):
            score += bonuses[category]
            positive_indicators.append(category)
        # Final condition-based score cap
    if "diabetes" in conditions and contains_sugar:
        score = min(score, 49)    

    score = max(0, min(100, score))

    # Prototype category

    if score >= 80:
        rating = "GREEN"
    elif score >= 50:
        rating = "YELLOW"
    else:
        rating = "RED"

    return {
        "score": score,
        "rating": rating,
        "risk_flags": risk_flags,
        "positive_indicators": positive_indicators,
        "allergy_matches": allergy_matches
    }


# ==========================================
# 5. GEMINI AI ANALYSIS
# ==========================================

def analyze_with_gemini(ingredients, profile, score_data):

    if client is None:
        raise ValueError("Gemini API key is not configured.")

    prompt = f"""
You are ScanWise AI, a food ingredient and nutrition information assistant.

Analyze the supplied ingredient list in relation to the user's profile.

INGREDIENTS:
{ingredients}

USER PROFILE:
{json.dumps(profile)}

PYTHON PRELIMINARY ANALYSIS:
{json.dumps(score_data)}

Return ONLY valid JSON using these keys:

{{
    "why": "Explain the preliminary rating.",
    "benefits": ["Potential nutritional benefits"],
    "risks": ["Potential ingredient-related concerns"],
    "condition_impact": "Explain relevant considerations for the user's conditions.",
    "advice": "Give practical, balanced food guidance.",
    "ingredients_detected": ["Ingredients identified"],
    "nutrition_analysis": "Explain what can and cannot be inferred nutritionally.",
    "uncertainty_notes": ["Important limitations or missing information"]
}}

IMPORTANT RULES:

1. Do not diagnose or claim to treat any medical condition.
2. Do not invent ingredient quantities or nutritional values.
3. Do not assume that an ingredient is present if it is not listed.
4. Do not claim a food is completely safe.
5. Pay special attention to the user's listed allergies.
6. Explain that an ingredient list alone cannot establish exact nutritional quantities.
7. Use the Python preliminary rating and score. Do not change them.
8. If information is insufficient, clearly mention the uncertainty.
9. Give general nutrition information, not medical advice.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={
            "response_mime_type": "application/json"
        }
    )

    return json.loads(response.text)


# ==========================================
# 6. MAIN ANALYZE ROUTE
# ==========================================

@app.route("/analyze", methods=["POST"])
def analyze():

    try:

        data = request.get_json(silent=True) or {}

        ingredients = data.get("ingredients", "")

        if not isinstance(ingredients, str) or not ingredients.strip():
            return jsonify({
                "error": "Please provide an ingredient list."
            }), 400

        profile = normalize_profile(data.get("profile", {}))

        # Python analysis

        score_data = calculate_score(ingredients, profile)

        # Gemini analysis

        try:

            ai_result = analyze_with_gemini(
                ingredients,
                profile,
                score_data
            )

        except Exception as ai_error:

            print("Gemini error:", ai_error)

            ai_result = {
                "why": "The preliminary score was calculated, but AI explanation is currently unavailable.",
                "benefits": [],
                "risks": score_data["risk_flags"],
                "condition_impact": "AI condition-specific analysis is unavailable.",
                "advice": "Review the ingredient list and consult a qualified healthcare professional for personal dietary advice.",
                "ingredients_detected": [],
                "nutrition_analysis": "Exact nutritional values cannot be determined from the ingredient list alone.",
                "uncertainty_notes": [
                    "Gemini analysis could not be completed."
                ]
            }

        # Final response

        result = {
            "status": "success",
            "rating": score_data["rating"],
            "score": score_data["score"],
            "compromise_level": score_data["rating"],
            "why": ai_result.get("why", ""),
            "benefits": ai_result.get("benefits", []),
            "risks": ai_result.get("risks", []),
            "condition_impact": ai_result.get("condition_impact", ""),
            "advice": ai_result.get("advice", ""),
            "ingredients_detected": ai_result.get("ingredients_detected", []),
            "nutrition_analysis": ai_result.get("nutrition_analysis", ""),
            "uncertainty_notes": ai_result.get("uncertainty_notes", []),
            "risk_flags": score_data["risk_flags"],
            "positive_indicators": score_data["positive_indicators"],
            "confidence": "Not scientifically validated",
            "disclaimer": (
                "ScanWise AI provides general food and nutrition information, "
                "not medical advice or a guarantee of food safety."
            )
        }

        return jsonify(result), 200

    except Exception as error:

        print("Backend error:", error)

        return jsonify({
            "status": "error",
            "error": "Something went wrong while analyzing the ingredients."
        }), 500


# ==========================================
# 7. START SERVER
# ==========================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
