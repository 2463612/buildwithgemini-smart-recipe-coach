import json
import os
import re
import urllib.parse
import urllib.request
import uuid
from typing import Any

from google.adk.tools import ToolContext
from google.cloud import firestore, storage
from google.genai import Client, types

# IMPORTANT: Hardcoded Project ID string (do not derive from GOOGLE_CLOUD_PROJECT or google.auth.default())
PROJECT_ID = "qwiklabs-gcp-02-e7f21cc0568b"
BUCKET_NAME = "smart-recipe-coach-b73a"


def get_firestore_client() -> firestore.Client:
    """Returns a Firestore client initialized with hardcoded project ID."""
    return firestore.Client(project=PROJECT_ID)


def search_recipes(query: str = "", dietary_tag: str = "") -> str:
    """Search for recipes in the Firestore database by title/description query or dietary tag.

    Args:
        query: Keywords to search for in recipe title or description (e.g. 'chicken', 'salmon', 'bowl').
        dietary_tag: Filter by dietary tag (e.g. 'vegan', 'high-protein', 'gluten-free', 'keto-friendly').

    Returns:
        A list of matching recipe summaries.
    """
    db = get_firestore_client()
    recipes_ref = db.collection("recipes")
    docs = recipes_ref.stream()

    matches = []
    query_clean = query.lower().strip() if query else ""
    tag_clean = dietary_tag.lower().strip() if dietary_tag else ""

    for doc in docs:
        data = doc.to_dict()
        recipe_id = doc.id
        title = data.get("title", "")
        description = data.get("description", "")
        dietary_tags = [t.lower() for t in data.get("dietary_tags", [])]
        ingredients = " ".join(data.get("ingredients", [])).lower()

        # Check tag match
        if tag_clean and tag_clean not in dietary_tags:
            continue

        # Check query match
        if query_clean:
            searchable_text = f"{title.lower()} {description.lower()} {ingredients}"
            if query_clean not in searchable_text:
                continue

        macros = data.get("macros", {})
        matches.append({
            "id": recipe_id,
            "title": title,
            "description": description,
            "dietary_tags": data.get("dietary_tags", []),
            "calories": macros.get("calories"),
            "protein_g": macros.get("protein"),
            "carbs_g": macros.get("carbs"),
            "fat_g": macros.get("fat")
        })

    if not matches:
        return f"No recipes found matching query='{query}' tag='{dietary_tag}'."

    output = f"Found {len(matches)} recipe(s):\n"
    for r in matches:
        output += f"- ID: {r['id']} | Title: {r['title']}\n"
        output += f"  Tags: {', '.join(r['dietary_tags'])}\n"
        output += f"  Macros: {r['calories']} kcal, {r['protein_g']}g protein, {r['carbs_g']}g carbs, {r['fat_g']}g fat\n"
        output += f"  Description: {r['description']}\n\n"

    return output.strip()


def get_recipe_details(recipe_id: str) -> str:
    """Retrieve full details for a specific recipe from Firestore.

    Args:
        recipe_id: The document ID or slug of the recipe (e.g. 'mediterranean-quinoa-bowl', 'lemon-herb-grilled-chicken').

    Returns:
        Formatted recipe details including ingredients, instructions, and macros.
    """
    db = get_firestore_client()
    doc_ref = db.collection("recipes").document(recipe_id.strip())
    doc = doc_ref.get()

    if not doc.exists:
        # Try searching by exact title if doc ID missed
        all_docs = db.collection("recipes").stream()
        for d in all_docs:
            data = d.to_dict()
            if data.get("title", "").lower() == recipe_id.lower().strip():
                doc = d
                break

    if not doc.exists:
        return f"Recipe with ID or title '{recipe_id}' not found."

    data = doc.to_dict()
    macros = data.get("macros", {})

    output = f"=== {data.get('title')} ===\n"
    output += f"ID: {doc.id}\n"
    output += f"Description: {data.get('description', '')}\n"
    output += f"Prep Time: {data.get('prep_time_minutes', 0)} mins | Cook Time: {data.get('cook_time_minutes', 0)} mins | Servings: {data.get('servings', 1)}\n"
    output += f"Dietary Tags: {', '.join(data.get('dietary_tags', []))}\n\n"

    output += "Nutritional Macros (per serving):\n"
    output += f"- Calories: {macros.get('calories', 'N/A')} kcal\n"
    output += f"- Protein: {macros.get('protein', 'N/A')} g\n"
    output += f"- Carbs: {macros.get('carbs', 'N/A')} g\n"
    output += f"- Fat: {macros.get('fat', 'N/A')} g\n\n"

    output += "Ingredients:\n"
    for ing in data.get("ingredients", []):
        output += f"- {ing}\n"

    output += "\nInstructions:\n"
    for idx, step in enumerate(data.get("instructions", []), 1):
        output += f"{idx}. {step}\n"

    return output.strip()


def add_recipe(
    title: str,
    description: str,
    ingredients: list[str],
    instructions: list[str],
    calories: int,
    protein: int,
    carbs: int,
    fat: int,
    dietary_tags: list[str],
    prep_time_minutes: int = 15,
    cook_time_minutes: int = 20,
    servings: int = 2
) -> str:
    """Add a new recipe to the Firestore database.

    Args:
        title: Title of the recipe.
        description: Short overview or description of the dish.
        ingredients: List of ingredient strings with measurements.
        instructions: Step-by-step cooking instructions list.
        calories: Total calories per serving.
        protein: Protein grams per serving.
        carbs: Carbohydrates grams per serving.
        fat: Fat grams per serving.
        dietary_tags: List of dietary tags (e.g. ['high-protein', 'vegan', 'gluten-free']).
        prep_time_minutes: Preparation time in minutes.
        cook_time_minutes: Cooking time in minutes.
        servings: Number of servings produced.

    Returns:
        Confirmation message with the generated recipe ID.
    """
    db = get_firestore_client()
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

    recipe_data = {
        "id": slug,
        "title": title,
        "description": description,
        "ingredients": ingredients,
        "instructions": instructions,
        "macros": {
            "calories": calories,
            "protein": protein,
            "carbs": carbs,
            "fat": fat
        },
        "dietary_tags": dietary_tags,
        "prep_time_minutes": prep_time_minutes,
        "cook_time_minutes": cook_time_minutes,
        "servings": servings
    }

    db.collection("recipes").document(slug).set(recipe_data)

    return f"Successfully saved recipe '{title}' to Firestore with ID '{slug}'."


def get_ingredient_nutrition_facts(ingredient_name: str) -> str:
    """Fetch real-world nutrition facts per 100g for an ingredient or packaged food item from Open Food Facts API.

    Args:
        ingredient_name: The ingredient or food product name to look up (e.g. 'rolled oats', 'greek yogurt', 'peanut butter', 'tofu').

    Returns:
        Nutritional information per 100g (calories, protein, carbs, fat, fiber, Nutri-Score) for matching products.
    """
    clean_name = ingredient_name.strip()
    if not clean_name:
        return "Please provide an ingredient or product name to search."

    # Read optional API key from environment variable if provided
    api_key = os.getenv("OPEN_FOOD_FACTS_KEY", "")

    encoded_query = urllib.parse.quote(clean_name)
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={encoded_query}&search_simple=1&action=process&json=1&page_size=3"

    headers = {"User-Agent": "SmartRecipeCoach/1.0 (contact@example.com)"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            products = data.get("products", [])

        if not products:
            return f"No nutritional data found on Open Food Facts for '{ingredient_name}'."

        results = [f"=== Open Food Facts Results for '{ingredient_name}' ==="]
        for idx, p in enumerate(products[:3], 1):
            name = p.get("product_name") or p.get("generic_name") or "Unknown Product"
            brand = p.get("brands", "Generic")
            nutriments = p.get("nutriments", {})
            nutriscore = p.get("nutriscore_grade", "N/A").upper()

            calories = nutriments.get("energy-kcal_100g", "N/A")
            protein = nutriments.get("proteins_100g", "N/A")
            carbs = nutriments.get("carbohydrates_100g", "N/A")
            fat = nutriments.get("fat_100g", "N/A")
            fiber = nutriments.get("fiber_100g", "N/A")

            results.append(
                f"{idx}. {name} (Brand: {brand})\n"
                f"   Nutri-Score: {nutriscore}\n"
                f"   Per 100g: {calories} kcal | Protein: {protein}g | Carbs: {carbs}g | Fat: {fat}g | Fiber: {fiber}g"
            )

        return "\n\n".join(results)
    except Exception as e:
        return f"Error fetching nutrition data for '{ingredient_name}': {str(e)}"


def generate_recipe_image(prompt: str, tool_context: ToolContext) -> str:
    """Generate a high-quality food image for a dish or recipe using gemini-3.1-flash-lite-image model in the global region.

    Args:
        prompt: Description of the dish or recipe to generate an image for (e.g. 'Garlic Butter Salmon with Asparagus').
        tool_context: ADK ToolContext injected by runtime to save artifacts.

    Returns:
        The public HTTPS URL of the generated image uploaded to Cloud Storage (https://storage.googleapis.com/smart-recipe-coach-b73a/<object>).
    """
    client = Client(vertexai=True, project=PROJECT_ID, location="global")

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=f"Professional food photography of {prompt}, appetizing presentation, high resolution",
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )

    if not response.candidates or not response.candidates[0].content.parts:
        return f"Failed to generate image for prompt: '{prompt}'."

    image_part = None
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            image_part = part
            break

    if not image_part or not image_part.inline_data or not image_part.inline_data.data:
        return f"No image data returned for prompt: '{prompt}'."

    image_bytes = image_part.inline_data.data
    mime_type = image_part.inline_data.mime_type or "image/jpeg"

    # 1. Save artifact with tool_context.save_artifact for Playground Artifacts panel
    filename = f"recipe_{uuid.uuid4().hex[:8]}.jpg"
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload image bytes directly to public GCS bucket smart-recipe-coach-b73a
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
    return public_url
