# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from pathlib import Path

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.tools import (
    add_recipe,
    generate_recipe_image,
    get_ingredient_nutrition_facts,
    get_recipe_details,
    search_recipes,
)

# Read metadata from deployment_metadata.json
metadata_file = Path(__file__).parent.parent / "deployment_metadata.json"
agent_engine_resource_name = None
sandbox_resource_name = None
memory_bank_id = "8385506793094119424"

if metadata_file.exists():
    try:
        with open(metadata_file, "r") as f:
            data = json.load(f)
            remote_id = data.get("remote_agent_runtime_id")
            if remote_id and remote_id != "None":
                agent_engine_resource_name = remote_id
                memory_bank_id = remote_id.split("/")[-1]
            sandbox_id = data.get("sandbox_resource_name")
            if sandbox_id and sandbox_id != "None":
                sandbox_resource_name = sandbox_id
    except Exception:
        pass

if sandbox_resource_name:
    code_executor = AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=sandbox_resource_name
    )
else:
    code_executor = AgentEngineSandboxCodeExecutor(
        agent_engine_resource_name=agent_engine_resource_name
    )


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback triggered after each turn to extract and store durable facts in Memory Bank."""
    await callback_context.add_session_to_memory()
    return None


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are the Smart Recipe & Meal Coach AI. You assist users in discovering recipes, "
        "planning healthy meals, calculating nutritional macros, organizing their pantry, and executing Python code for math/data analysis."
    ),
    workflow_description=(
        "Analyze the user request and return structured UI when appropriate. You remember user preferences, dietary restrictions, favorite foods, and facts stated across sessions.\n"
        "- Use search_recipes, get_recipe_details, and add_recipe to manage and query the recipe database.\n"
        "- Use get_ingredient_nutrition_facts to look up real-world nutrition data per 100g for ingredients from Open Food Facts.\n"
        "- Use generate_recipe_image to generate appetizing food photos for dishes/recipes.\n"
        "- When asked to perform complex math, unit conversions, or data calculations, write Python code blocks to execute in your sandbox."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=code_executor,
    tools=[
        PreloadMemoryTool(),
        search_recipes,
        get_recipe_details,
        add_recipe,
        get_ingredient_nutrition_facts,
        generate_recipe_image,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
