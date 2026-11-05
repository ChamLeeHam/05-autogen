import chainlit as cl
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.teams import  SelectorGroupChat
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

planning_agent = AssistantAgent("PlanningAgent",
                                description="当用户的问题比较复杂是，先根据用户问题继续规划，然后继续子任务委派",
                                model_client=model_client,
                                system_message="""
                                你是一个任务规划智能体。
                                你的工作是将复杂的任务分解为更小的、可管理的子任务。
                                你的团队成员有3个，分别是：
                                    DentalPulpAgent: 牙体牙髓科智能体
                                    RestorativeAgent: 牙齿修复科智能体
                                    DentalImplantAgent: 牙齿种植科智能体

                                你只计划和委派任务，而不自己执行它们

                                分配任务时，请使用此格式:
                                1. <agent> : <task>

                                当所有智能体把任务完成后，再总结结果以"TERMINATE"结束。                        
                                """
                                )

dental_pulp_agent = AssistantAgent("DentalPulpAgent",
                                   description="牙体牙髓科智能体",
                                   model_client=model_client,
                                   system_message="""
                                你是一个口腔医院的牙体牙髓科智能体。
                                你可以解答关于牙体牙髓科中患者提出的问题，你的解答非常专业，且可靠。回答完成后：TERMINATE
                                """
                                   )

restorative_agent = AssistantAgent("RestorativeAgent",
                                   description="牙齿修复科智能体",
                                   model_client=model_client,
                                   system_message="""
                                你是一个口腔医院的牙齿修复科智能体。
                                你可以解答关于牙齿修复中患者提出的问题，比如牙冠、烤瓷牙、嵌体修复等。你的解答非常专业，且可靠。回答完成后：TERMINATE
                                """
                                   )

dental_implant_agent = AssistantAgent("DentalImplantAgent",
                                      description="牙齿种植科智能体",
                                      model_client=model_client,
                                      system_message="""
                                你是一个口腔医院的牙齿种植科的智能体。
                                你可以解答关于牙齿种植科中患者提出的问题，你的解答非常专业，且可靠。回答完成后：TERMINATE
                                """ )

@cl.on_chat_start
async def main():
    await cl.Message(content="您好，这是口腔医院的专家团队，有什么可以帮您？").send()


termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(20)

team = SelectorGroupChat(
    [planning_agent,dental_pulp_agent,restorative_agent,dental_implant_agent],
    model_client=model_client,
    termination_condition=termination
)

async def run_team(query: str):
    response_stream = team.run_stream(task=query)
    async for msg in response_stream:
        if hasattr(msg, "source") and msg.source != "user" and hasattr(msg, "content"):
            await cl.Message(content=f"[{msg.source}]:{msg.content}", author=msg.source).send()

@cl.on_message
async def main(message: cl.Message):
    await run_team(message.content)

