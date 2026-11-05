import chainlit as cl
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
import os
from dotenv import load_dotenv

load_dotenv()

model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_URL"),
    model_info={
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "structured_output": True,
        "family": "unknown"
    }
)

assistant_agent = AssistantAgent(
    "assistant",
    model_client=model_client,
    system_message="你是一所口腔医院的导诊台机器人，负责解答用户的挂号问题，用户描述症状需求，你回答应该挂的科室。"
                    "在本医院中有以下科室：牙体牙髓科、口腔修复科、口腔外科、口腔种植科、儿童口腔专科。"
                    "如果用户的问题与挂号咨询不符合，回答：“您的描述与症状无关，暂不支持”")

team = RoundRobinGroupChat(participants=[assistant_agent], max_turns=1)

@cl.on_chat_start
async def main():
    await cl.Message(content="您好，这里是超级无敌大医院，有什么可以帮您？").send()

async def run_team(query: str):
    response_stream = team.run_stream(task=query)
    async for msg in response_stream:
        if hasattr(msg, "source") and msg.source != "user" and hasattr(msg, "content"):
            await cl.Message(content=msg.content, author="Agent Team").send()

@cl.on_message
async def main(message: cl.Message):
    await run_team(message.content)