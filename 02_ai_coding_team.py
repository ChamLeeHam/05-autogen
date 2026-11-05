import asyncio
import os

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat
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
pm = AssistantAgent(
    name="Product_Manager",
    model_client=model_client,
    system_message="你是一位专业的产品经理，分析用户的需求，输出和性功能点，完成后@Programer"
)
programer = AssistantAgent(
    name="Programer",
    model_client=model_client,
    system_message="你是一位专业的程序员，根据需求编写Python代码，代码要符合规范要求，完成后@Tester"
)
tester = AssistantAgent(
    name="Tester",
    model_client=model_client,
    system_message="你是一位专业的测试程序员，检查代码核心逻辑是否存在问题，如果有问题@Programmer重新编写，如果没有问题则说终止"
)

termination = TextMentionTermination("终止") | MaxMessageTermination(10)

team = RoundRobinGroupChat(
    participants=[pm, programer, tester],
    termination_condition=termination
)


async def test():
    #task = "写一个计算斐波那契数列第n项的函数"
    task = "请完成鸡兔同笼的算法"
    print(f"\n【任务】{task}\n")

    async  for msg in team.run_stream(task=task):
        if hasattr(msg, "content") and msg.source!="user":
            print(f"[{msg.source}]: {msg.content}\n")
            print("-"*50)


if __name__ == "__main__":
    asyncio.run(test())