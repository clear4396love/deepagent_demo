import os

from tavily import TavilyClient
from langchain_core.tools import tool
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from deepagents import RubricMiddleware, create_deep_agent
from langchain_core.messages import HumanMessage

load_dotenv()

DEEPSEEK_API_KEY=os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASEURL=os.getenv("DEEPSEEK_BASE_URL")
TAVILY_API_KEY=os.getenv("TAVILY_API_KEY")

model=init_chat_model(
    model="deepseek-v4-flash",
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASEURL,
    extra_body={"thinking": {"type": "disabled"}},
)

tavily_client=TavilyClient(api_key=TAVILY_API_KEY)


@tool
def find_route(
        question:str,
        max_results:int=2
    ) :
    """搜索公共交通路线、班次、票价和耗时信息，返回可供核对的网页结果。"""
    return tavily_client.search(
        query=question,
        max_results=max_results
    )


ROUTE_RUBRIC = """
- 根据本轮用户问题验收最终回复；路线问题须覆盖起点、终点及用户明确提出的时间、交通方式等约束。
- 如果回复给出班次、票价、耗时或其他可能变化的具体事实，评分前须调用 find_route 核对；搜索结果不支持的事实必须标为未核实，不能当作确定信息。
- 不得声称完成了对话记录中没有成功执行的查询。
""".strip()

evaluations = []


def record_evaluation(evaluation) -> None:
    evaluations.append(evaluation)
    print(f"[验收 {evaluation['iteration'] + 1}] {evaluation['result']}")
    for criterion in evaluation["criteria"]:
        if not criterion["passed"]:
            print(f"  未通过：{criterion['name']}：{criterion.get('gap', '')}")


# 评分接口不接受服务端 response_format，单独关闭评分模型的原生结构化输出能力。
grader_model = model.model_copy(update={"profile": {**model.profile, "structured_output": False}})

rubric_middleware = RubricMiddleware(
    model=grader_model,
    tools=[find_route],
    max_iterations=3,
    on_evaluation=record_evaluation,
)

agent=create_deep_agent(
    model=model,
    tools=[find_route],
    middleware=[rubric_middleware],
    system_prompt=(
        "你是一个出行规划助手，负责给用户规划路线。简单路线问题用常识直接回答；"
        "需要查班次、票价、耗时，或做多种交通方式对比时，调用 find_route 查询。"
        "给出实时班次、票价、耗时时说明查询来源；无法核实时明确说明。"
    ),
)

if __name__ == "__main__":
    while True:
        question = input("您想输入的内容是：")
        if question == "q":
            break

        evaluation_start = len(evaluations)
        result = agent.invoke({
            "messages": [HumanMessage(content=question)],
            "rubric": ROUTE_RUBRIC,
        })

        run_evaluations = evaluations[evaluation_start:]
        final_evaluation = run_evaluations[-1] if run_evaluations else None
        if final_evaluation and final_evaluation["result"] == "satisfied":
            print(result["messages"][-1].text)
        else:
            status = final_evaluation["result"] if final_evaluation else "未收到评审结果"
            print(f"[未放行] 本轮回复未通过验收：{status}")
