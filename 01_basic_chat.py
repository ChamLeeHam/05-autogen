import asyncio
import os

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
from openai.types.beta import Assistant

load_dotenv()

model_client = OpenAIChatCompletionClient(
    model = "gpt-4o",
    api_key = os.getenv("OPENAI_API_KEY"),
    base_url = os.getenv("OPENAI_BASE_URL"),
    model_info={
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "structured_output": True,
        "family": "unknown"
    }
)

# 构建一个智能体
assistant = AssistantAgent(
    name="Assistant",
    model_client=model_client,
    system_message="你是一个IT程序员专家，精通各种编程，熟悉业务和技术架构，有多年实战开发经验！当用户问题解决了后请输出“终止”表示结束。"
)

async def test():
    question = "什么是python?"
    msg = TextMessage(content=question, source="user")

    token = CancellationToken()

    try:
        response = await asyncio.wait_for(
            assistant.on_messages([msg], token),
            timeout=20
        )
        print(f"模型恢复结果为: {response.chat_message.content}")
    except asyncio.TimeoutError:
        token.cancel()
        print("请求超时")
if __name__ == "__main__":
    asyncio.run(test())
