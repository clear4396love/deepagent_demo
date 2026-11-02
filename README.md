# Deep Agents 路线规划练习

这是一个基于 [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) 的命令行练习：用 DeepSeek 回答出行路线问题，必要时通过 Tavily 搜索网页，并用 `RubricMiddleware` 对回复进行验收和修订。

## 功能与流程

1. 在终端输入路线问题。简单问题可由模型直接回答；涉及班次、票价、耗时或交通方式对比时，代理可调用 `find_route` 搜索网页。
2. `RubricMiddleware` 按 `ROUTE_RUBRIC` 检查回复是否覆盖起终点和用户约束，以及变化中的事实是否经过查询支持。评分模型也可调用 `find_route` 核对。
3. 未满足标准时，代理会根据反馈修订；评分最多进行 3 次。终端打印每次验收结果和未通过的条目。
4. 最后一轮结果为 `satisfied` 时打印回答；否则显示 `[未放行]` 及状态。

代码入口是 [`main.py`](main.py)。每次输入都会新建一次 `agent.invoke` 调用，当前脚本没有保存跨问题的对话历史。

## 运行

需要 Python 3.11 或更高版本，以及可用的 DeepSeek 和 Tavily API Key。

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS / Linux: source .venv/bin/activate
python -m pip install deepagents langchain langchain-deepseek tavily-python python-dotenv
```

在 `main.py` 同目录创建 `.env`，填入自己的配置：

```dotenv
DEEPSEEK_API_KEY=你的_DeepSeek_API_Key
DEEPSEEK_BASE_URL=你的_DeepSeek_API_地址
TAVILY_API_KEY=你的_Tavily_API_Key
```

不要将 `.env` 或真实 API Key 提交到 GitHub。模型 ID 在 `main.py` 中固定为 `deepseek-v4-flash`；如果所用服务不支持该 ID，需要在代码中改成服务实际提供的模型 ID。

启动交互式程序：

```bash
python main.py
```

例如输入 `从上海虹桥站到杭州东站，明天上午有哪些高铁？票价和耗时是多少？`。输入 `q` 退出。脚本目前只从终端交互读取问题，不支持把问题作为命令行参数传入。

## 代码要点

| 位置 | 作用 |
| --- | --- |
| `find_route` | 将用户问题交给 Tavily，返回网页搜索结果；默认最多 2 条。 |
| `ROUTE_RUBRIC` | 定义路线回复的验收条件，要求核对可能变化的具体事实。 |
| `grader_model` | 基于回答模型创建评分模型副本，关闭原生结构化输出能力，以适配当前评分接口。 |
| `record_evaluation` | 记录并打印每次验收的结果与未通过原因。 |
| `create_deep_agent` | 组装模型、搜索工具、评分中间件和出行助手提示词。 |

这是学习示例。搜索结果和模型评分仍可能有误；实际出行前应以交通运营方的实时信息为准。调用模型和 Tavily API 可能产生费用。

## 参考

- [Deep Agents 文档](https://docs.langchain.com/oss/python/deepagents/overview)
- [RubricMiddleware 文档](https://docs.langchain.com/oss/python/deepagents/rubric)
- [Tavily Python SDK](https://pypi.org/project/tavily-python/)
