import chainlit as cl


# 1. 聊天开始时触发（类似于初始化）
@cl.on_chat_start
async def on_start():
    cl.user_session.set("count", 0)
    await cl.Message(content="👋 您好！我是您的 AI 助手，有什么可以帮您？").send()

@cl.action_callback("action_button")
async def action_button(action:cl.Action):
    # 按钮触发的动作
    value = action.payload.get("value")
    await cl.Message(content=f"按钮被点击了，当前值为：{value}").send()

# 2. 收到用户消息时触发（核心逻辑入口）
@cl.on_message
async def on_message(message: cl.Message):
    count = cl.user_session.get("count") + 1
    cl.user_session.set("count",count)
    # 获取用户输入
    user_input = message.content
    # 模拟思考或调用大模型
    response = f"您刚才说的是：{user_input}，我正在处理...,现在是第{count}次会话"
    # 发送回复
    await cl.Message(
        content=response,
        actions=[
            cl.Action(
                name="action_button",
                payload={"value": "1"},  # ✅ payload 必须是字典
                label="点击我1",
            ),
            cl.Action(
                name="action_button",
                payload={"value": "2"},  # ✅ payload 必须是字典
                label="点击我2",
            ),
            cl.Action(
                name="action_button",
                payload={"value": "3"},  # ✅ payload 必须是字典
                label="点击我2",
            ),
        ]
    ).send()