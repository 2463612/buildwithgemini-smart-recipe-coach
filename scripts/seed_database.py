from google.cloud import firestore

# IMPORTANT: Hardcoded Project ID string (do not derive from GOOGLE_CLOUD_PROJECT or google.auth.default())
PROJECT_ID = "qwiklabs-gcp-02-e7f21cc0568b"

SEEDED_RECIPES = [
    {
        "id": "mediterranean-quinoa-bowl",
        "title": "Mediterranean Quinoa Bowl",
        "description": "A fresh, protein-packed Mediterranean bowl with fluffy quinoa, chickpeas, cucumbers, and feta.",
        "ingredients": [
            "1 cup cooked quinoa",
            "1/2 cup canned chickpeas, rinsed",
            "1/2 cup diced cucumber",
            "1/4 cup cherry tomatoes, halved",
            "2 tbsp crumbled feta cheese",
            "1 tbsp extra virgin olive oil",
            "1 tbsp lemon juice",
            "Salt and black pepper to taste"
        ],
        "instructions": [
            "Cook quinoa according to package directions and let cool slightly.",
            "In a bowl, combine quinoa, chickpeas, cucumber, and cherry tomatoes.",
            "Drizzle with olive oil and lemon juice, then toss gently.",
            "Top with crumbled feta cheese, salt, and black pepper before serving."
        ],
        "macros": {
            "calories": 420,
            "protein": 15,
            "carbs": 58,
            "fat": 14
        },
        "dietary_tags": ["vegetarian", "gluten-free", "high-fiber"],
        "prep_time_minutes": 10,
        "cook_time_minutes": 15,
        "servings": 1
    },
    {
        "id": "lemon-herb-grilled-chicken",
        "title": "Lemon Herb Grilled Chicken Breast",
        "description": "Juicy grilled chicken breast marinated in garlic, lemon, oregano, and olive oil.",
        "ingredients": [
            "2 boneless, skinless chicken breasts (approx 6 oz each)",
            "2 tbsp olive oil",
            "2 tbsp fresh lemon juice",
            "2 cloves garlic, minced",
            "1 tsp dried oregano",
            "1/2 tsp salt",
            "1/4 tsp black pepper"
        ],
        "instructions": [
            "Whisk together olive oil, lemon juice, garlic, oregano, salt, and pepper.",
            "Marinate chicken breasts in the mixture for at least 20 minutes.",
            "Preheat grill or grill pan to medium-high heat.",
            "Grill chicken for 6-8 minutes per side until internal temperature reaches 165°F (74°C).",
            "Rest for 5 minutes before slicing."
        ],
        "macros": {
            "calories": 310,
            "protein": 42,
            "carbs": 2,
            "fat": 14
        },
        "dietary_tags": ["high-protein", "keto-friendly", "gluten-free", "low-carb"],
        "prep_time_minutes": 10,
        "cook_time_minutes": 15,
        "servings": 2
    },
    {
        "id": "creamy-avocado-spinach-smoothie",
        "title": "Creamy Avocado & Spinach Protein Smoothie",
        "description": "A nutrient-rich green smoothie packed with healthy fats, spinach, and plant protein.",
        "ingredients": [
            "1/2 ripe avocado",
            "1 cup fresh spinach leaves",
            "1 scoop plant-based vanilla protein powder",
            "1 cup unsweetened almond milk",
            "1/2 frozen banana",
            "1 tbsp chia seeds"
        ],
        "instructions": [
            "Add all ingredients to a high-speed blender.",
            "Blend on high for 60 seconds until completely smooth.",
            "Pour into a tall glass and enjoy immediately."
        ],
        "macros": {
            "calories": 350,
            "protein": 24,
            "carbs": 30,
            "fat": 18
        },
        "dietary_tags": ["vegan", "dairy-free", "high-protein", "gluten-free"],
        "prep_time_minutes": 5,
        "cook_time_minutes": 0,
        "servings": 1
    },
    {
        "id": "one-pan-salmon-and-asparagus",
        "title": "One-Pan Garlic Butter Salmon & Asparagus",
        "description": "Oven-baked salmon fillet paired with crisp tender asparagus in garlic butter.",
        "ingredients": [
            "2 salmon fillets (6 oz each)",
            "1 bunch asparagus, trimmed",
            "2 tbsp melted butter",
            "2 cloves garlic, minced",
            "1 tbsp lemon juice",
            "Salt and pepper to taste"
        ],
        "instructions": [
            "Preheat oven to 400°F (200°C) and line a baking sheet with parchment paper.",
            "Place salmon fillets and trimmed asparagus on the baking sheet.",
            "Mix melted butter, garlic, and lemon juice; drizzle evenly over salmon and asparagus.",
            "Season with salt and pepper.",
            "Bake for 12-15 minutes until salmon flakes easily with a fork."
        ],
        "macros": {
            "calories": 480,
            "protein": 38,
            "carbs": 6,
            "fat": 32
        },
        "dietary_tags": ["keto-friendly", "high-protein", "gluten-free", "low-carb", "pescatarian"],
        "prep_time_minutes": 10,
        "cook_time_minutes": 15,
        "servings": 2
    }
]


def seed_recipes():
    print(f"Connecting to Firestore with project ID: '{PROJECT_ID}'...")
    db = firestore.Client(project=PROJECT_ID)
    recipes_ref = db.collection("recipes")

    for recipe in SEEDED_RECIPES:
        doc_id = recipe["id"]
        doc_ref = recipes_ref.document(doc_id)
        doc_ref.set(recipe)
        print(f"Seeded recipe: '{recipe['title']}' (ID: {doc_id})")

    print("Firestore seeding completed successfully!")


if __name__ == "__main__":
    seed_recipes()
