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

# async def x_p_search(tooth_position: str) -> str:
#     """根据用户牙位号获取CT影像信息"""
#     app_user = cl.user_session.get("user")
#     print(f"模拟查询{app_user.identifier}的{tooth_position}牙片数据")
#     if tooth_position == "46":
#         return "牙根尖处有阴影，疑似感染，需要进一步分析诊断"    #假设以前已经拍过片子了
#     else:
#         return f"{tooth_position}无影像"        #没有拍过片子

async def tcm_constitution_check(symptoms: str) -> str:
    """根据症状查询中医体质类型"""
    app_user = cl.user_session.get("user")
    print(f"[系统日志] 用户 {app_user.identifier} 正在查询体质，症状：{symptoms}")

    # 模拟逻辑：包含特定关键词返回特定体质
    if "怕冷" in symptoms or "手脚冰凉" in symptoms:
        return "体质辨识结果：阳虚质。建议：温补阳气，忌食生冷。"
    elif "口干" in symptoms or "手心发热" in symptoms:
        return "体质辨识结果：阴虚质。建议：滋阴清热，早睡早起。"
    elif "肥胖" in symptoms or "痰多" in symptoms:
        return "体质辨识结果：痰湿质。建议：健脾祛湿，清淡饮食。"
    else:
        return "体质辨识结果：平和质。建议：保持现有良好生活习惯，定期锻炼。"


assistant_agent = AssistantAgent(
    "assistant",
    model_client=model_client,
    tools=[tcm_constitution_check],
    system_message="你是一名中医体质辨识与健康顾问。"
    "请通过多轮对话了解用户的身体症状，可以主动询问症状细节和持续时间。"
    "最多追问两轮；如果用户希望直接查看结果，就停止追问。"
    "然后调用tcm_constitution_check工具，"
    "将用户在本次对话中描述的相关症状汇总传入symptoms参数。"
    "必须在回复中明确写出工具返回的体质名称，并根据工具结果提供简洁建议。"
    "工具结果是关键词匹配的演示，不能作为医学诊断。"
    "与健康咨询无关的问题，回答：您的描述与健康咨询无关，暂不支持。"
    )

team = RoundRobinGroupChat(participants=[assistant_agent], max_turns=1)

@cl.on_chat_start
async def main():
    await cl.Message(content="您好，这里是超级无敌大中医院，有什么可以帮您？").send()

async def run_team(query: str):
    response_stream = team.run_stream(task=query)

    async for msg in response_stream:
        if hasattr(msg, "source") and (
            msg.type == "ToolCallExecutionEvent"
            or msg.type == "ToolCallRequestEvent"
        ):
            # 工具调用事件不直接显示给用户
            continue

        if (hasattr(msg, "source") and msg.source != "user" and isinstance(getattr(msg, "content", None), str)):
            if any(
                constitution in msg.content
                for constitution in ("阳虚质", "阴虚质", "痰湿质")
            ):
                result = await cl.AskActionMessage(
                    content=f"{msg.content}\n是否需要预约专家问诊？",
                    actions=[
                        cl.Action(name="yes",payload={"value": "预约"},label="✅ 预约专家"),
                        cl.Action(name="no",payload={"value": "取消"},label="❌ 暂不预约")
                    ]
                ).send()

                if result and (result.get("payload") or {}).get("value") == "预约":
                    await cl.Message(content="已记录您的预约意向，等待工作人员联系。", author="Agent Team").send()
            else:
                await cl.Message(content=msg.content,author="Agent Team").send()

@cl.on_message
async def main(message: cl.Message):
    await run_team(message.content)