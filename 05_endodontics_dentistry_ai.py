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

@cl.password_auth_callback
def login(username:str, password:str):
    if (username, password) == ("zhangsan", "123456"):
        return cl.User(
            identifier="zhangsan", metadata={"role":"normal", "level":"3"}
        )
    elif (username, password) == ("lisi", "123456"):
        return cl.User(
            identifier="lisi", metadata={"role":"admin", "level":"1"}
        )
    else:
        return None

async def x_p_search(tooth_position: str) -> str:
    """根据用户牙位号获取CT影像信息"""
    app_user = cl.user_session.get("user")
    print(f"模拟查询{app_user.identifier}的{tooth_position}牙片数据")
    if tooth_position == "46":
        return "牙根尖处有阴影，疑似感染，需要进一步分析诊断"    #假设以前已经拍过片子了
    else:
        return f"{tooth_position}无影像"        #没有拍过片子

assistant_agent = AssistantAgent(
    "assistant",
    model_client=model_client,
    tools=[x_p_search],
    system_message="你是一个牙体牙髓科的病情诊断机器人，负责对用户输入的症状描述分析原因，在分析病因前先询问出用户是具体哪一颗牙齿需要治疗。"
                   "在知道了具体的牙位号后，再调用x_p_search工具进行问题回答，传入给x_p_search工具的参数需要自动转为牙位号，如:28"
                   "如果用户的问题与病情咨询无关，回答：“您的描述与症状无关，暂不支持”")

team = RoundRobinGroupChat(participants=[assistant_agent], max_turns=1)

@cl.on_chat_start
async def main():
    await cl.Message(content="您好，这里是超级无敌大医院，有什么可以帮您？").send()

async def run_team(query: str):
    response_stream = team.run_stream(task=query)
    async for msg in response_stream:
        if hasattr(msg, "source") and (msg.type == "ToolCallExecutionEvent" or msg.type == "ToolCallRequestEvent"):
            # functionCall事件消息不显示给用户
            continue
        if hasattr(msg, "source") and msg.source != "user" and hasattr(msg, "content"):
            if msg.content.endswith("无影像"):
                # 给出拍片的建议
                result = await cl.AskActionMessage(
                    content=f"{msg.content}, 是否需要帮你申请排CT",
                    actions=[
                        cl.Action(name="yes", payload={"value":"申请"}, label="✅ 申请"),
                        cl.Action(name="no", payload={"value": "取消"}, label="❌ 申请")
                    ]
                ).send()
                if result and result.get("payload").get("value")=="申请":
                    await cl.Message(content="牙片申请已经提交， 等待确认， 请在第三影像室门口等待！", author="Agent Team").send()
            else:
                await cl.Message(content=msg.content, author="Agent Team").send()

@cl.on_message
async def main(message: cl.Message):
    await run_team(message.content)