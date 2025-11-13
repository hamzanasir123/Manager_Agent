from agents import Agent, RunConfig, OpenAIChatCompletionsModel, Runner
from dotenv import load_dotenv
from openai import AsyncOpenAI
import os
import chainlit as cl
from datetime import datetime
from Agents.Format_Agents import format_agent

# --- Load environment variables ---
load_dotenv()

with open("Instructions/manager_agent.md", "r") as file:
    mangager_agent_instructions = file.read()

# --- Gemini API Keys ---
GEMINI_KEYS = [
    os.getenv("GEMINI_API_KEY1"),
    os.getenv("GEMINI_API_KEY2"),
    os.getenv("GEMINI_API_KEY3")
]

if not any(GEMINI_KEYS) or GEMINI_KEYS == [""]:
    raise ValueError("No Gemini API keys found in .env file.")

current_key_index = 0
api_key = GEMINI_KEYS[current_key_index].strip()

external_client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash",
    openai_client=external_client
)

config = RunConfig(
    model=model,
    model_provider=external_client
)

# --- Define contextual info for handoffs ---
RESTAURANT_NAME = "McDonald's – Corniche"
OC_NAME = "Shujaat Hussain"
RM_NAME = "Usama Mateen"

manager_agent = Agent(
    name="Manager Agent",
    instructions=mangager_agent_instructions,
    handoffs=[format_agent],
    model=model,
)

# --- Chat start ---
@cl.on_chat_start
async def start():
    await cl.Message(content="""
                     👋 Hi! The Manager Agent is ready.
                        To Generate a Format SMS, please provide the subject with SUBJECT Keyword.
                        For example: SUBJECT: Meeting Reminder
                     """).send()


# --- Handle user messages ---
@cl.on_message
async def main(message: cl.Message):
    user_input = message.content.strip()
    today = datetime.now().strftime("%d-%b-%Y")

    # Detect SUBJECT-based message (handoff trigger)
    if user_input.startswith("SUBJECT:"):
        # Add contextual info before handoff
        enriched_input = f"""
Date: {today}
Restaurant: {RESTAURANT_NAME}
OC: {OC_NAME}
RM: {RM_NAME}

{user_input}
"""
        # Run with enriched info (handoff to Format Agent)
        response = await Runner.run(
            starting_agent=manager_agent,
            run_config=config,
            input=enriched_input
        )
    else:
        # Normal message handled directly by Manager Agent
        response = await Runner.run(
            starting_agent=manager_agent,
            run_config=config,
            input=user_input
        )

    # Send back the final response
    await cl.Message(content=response.final_output).send()
