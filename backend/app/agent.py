import json
from typing import Any


class PomodoroAdvisorAgent:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def generate(self, usage_context: dict[str, Any], extra_prompt: str | None = None) -> dict[str, Any]:
        try:
            from langchain_core.output_parsers import JsonOutputParser
            from langchain_core.prompts import ChatPromptTemplate
            from pydantic import BaseModel, Field
            from langchain_openai import ChatOpenAI
        except Exception as exc:
            raise RuntimeError("LangChain dependencies are missing. Please install backend requirements.") from exc

        class AdviceSection(BaseModel):
            title: str = Field(description="固定四个之一：核心观察、今日调整建议、未来7天策略、风险提醒")
            bullets: list[str] = Field(description="2-5条可执行建议，纯文本，不要Markdown")

        class TaskTuningSuggestion(BaseModel):
            todo_id: int | None = Field(default=None, description="待办ID，若无法匹配可为null")
            current_title: str = Field(description="当前待办名")
            suggested_title: str = Field(description="推荐待办名")
            current_focus_minutes: int = Field(description="当前专注时长")
            suggested_focus_minutes: int = Field(description="推荐专注时长，范围1~180")
            reason: str = Field(description="建议原因，简洁可执行")

        class AdviceOutput(BaseModel):
            headline: str = Field(description="一句话总结")
            sections: list[AdviceSection] = Field(description="严格4个分区，顺序固定")
            task_tuning_suggestions: list[TaskTuningSuggestion] = Field(
                description="任务级建议，最多5条。请给出任务命名优化和时长调整建议。"
            )

        llm_kwargs: dict[str, Any] = {
            "model": self.config["model"],
            "api_key": self.config["api_key"],
            "temperature": float(self.config["temperature"]),
            "max_tokens": int(self.config["max_tokens"]),
            "timeout": float(self.config.get("request_timeout_seconds", 45)),
        }
        base_url = (self.config.get("base_url") or "").strip()
        if base_url:
            llm_kwargs["base_url"] = base_url

        llm = ChatOpenAI(**llm_kwargs)
        parser = JsonOutputParser(pydantic_object=AdviceOutput)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是一名番茄钟效率教练。请基于使用数据给出专业、可执行建议。"
                    " 输出必须为纯JSON，不要Markdown，不要代码块，不要额外解释。"
                    " sections 必须严格包含并且仅包含以下顺序：核心观察、今日调整建议、未来7天策略、风险提醒。"
                    " 每个 bullets 2-5条，语句简洁，可执行。"
                    " task_tuning_suggestions 至少给出1条、最多5条。"
                    " 对每条建议都要包含 suggested_title 和 suggested_focus_minutes。"
                    " suggested_focus_minutes 必须是 1 到 180 的整数。"
                ),
                (
                    "human",
                    "用户番茄钟使用画像(JSON):\n{usage_json}\n\n用户额外需求：{extra_prompt}\n\n输出格式要求：{format_instructions}",
                ),
            ]
        )
        chain = prompt | llm | parser
        output = chain.invoke(
            {
                "usage_json": json.dumps(usage_context, ensure_ascii=False, indent=2),
                "extra_prompt": (extra_prompt or "无"),
                "format_instructions": parser.get_format_instructions(),
            }
        )
        return dict(output)
