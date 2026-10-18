"""The tool-calling loop is tested with a fake client: no network, scripted answers."""

import asyncio
import copy
import json
from types import SimpleNamespace

import httpx2
import openai
import pytest

from novoya_api.shared.infrastructure.llm.errors import LLMError, ToolError
from novoya_api.shared.infrastructure.llm.orchestrator import Orchestrator, Tool

MODELS = ["model-a", "model-b", "model-c"]
USER_MESSAGES = [{"role": "user", "content": "Plan a weekend in Lisbon."}]


class FakeCompletions:
    def __init__(self, script: list) -> None:
        self.script = list(script)
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        kwargs["messages"] = copy.deepcopy(kwargs["messages"])
        self.calls.append(kwargs)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeClient:
    def __init__(self, *script) -> None:
        self.completions = FakeCompletions(list(script))
        self.chat = SimpleNamespace(completions=self.completions)


def answer(content):
    message = SimpleNamespace(content=content, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def tool_calls(*calls, content=None):
    message = SimpleNamespace(
        content=content,
        tool_calls=[
            SimpleNamespace(
                id=call_id,
                type="function",
                function=SimpleNamespace(name=name, arguments=arguments),
            )
            for call_id, name, arguments in calls
        ],
    )
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def no_choices():
    return SimpleNamespace(choices=[])


def connection_error():
    request = httpx2.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    return openai.APIConnectionError(request=request)


class RecordingHandler:
    def __init__(self, result) -> None:
        self.result = result
        self.calls: list[dict] = []

    async def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


async def failing_handler(**kwargs):
    raise RuntimeError("weather service down")


WEATHER_PARAMETERS = {
    "type": "object",
    "properties": {"city": {"type": "string"}},
    "required": ["city"],
}


def weather_tool(handler) -> Tool:
    return Tool(
        name="get_weather",
        description="Weather forecast for a city.",
        parameters=WEATHER_PARAMETERS,
        handler=handler,
    )


def test_tool_definition_is_an_openai_function():
    tool = weather_tool(RecordingHandler({}))

    assert tool.definition() == {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Weather forecast for a city.",
            "parameters": WEATHER_PARAMETERS,
        },
    }


async def test_plain_answer_is_returned():
    client = FakeClient(answer("Go to Belem."))

    result = await Orchestrator(client, MODELS).run(USER_MESSAGES)

    assert result == "Go to Belem."


async def test_plain_answer_makes_one_call_with_first_model_and_messages():
    client = FakeClient(answer("Go to Belem."))

    await Orchestrator(client, MODELS).run(USER_MESSAGES)

    assert len(client.completions.calls) == 1
    assert client.completions.calls[0]["model"] == "model-a"
    assert client.completions.calls[0]["messages"] == USER_MESSAGES


async def test_without_tools_the_tools_argument_is_not_sent():
    client = FakeClient(answer("Go to Belem."))

    await Orchestrator(client, MODELS).run(USER_MESSAGES)

    assert "tools" not in client.completions.calls[0]


async def test_tool_definitions_are_sent():
    client = FakeClient(answer("Go to Belem."))
    tool = weather_tool(RecordingHandler({}))

    await Orchestrator(client, MODELS).run(USER_MESSAGES, tools=[tool])

    assert client.completions.calls[0]["tools"] == [tool.definition()]


async def test_tool_call_awaits_handler_with_decoded_arguments():
    client = FakeClient(
        tool_calls(("call-1", "get_weather", '{"city": "Lisbon"}')),
        answer("Sunny, go to Belem."),
    )
    handler = RecordingHandler({"forecast": "sunny"})

    await Orchestrator(client, MODELS).run(USER_MESSAGES, tools=[weather_tool(handler)])

    assert handler.calls == [{"city": "Lisbon"}]


async def test_tool_call_returns_final_answer():
    client = FakeClient(
        tool_calls(("call-1", "get_weather", '{"city": "Lisbon"}')),
        answer("Sunny, go to Belem."),
    )
    handler = RecordingHandler({"forecast": "sunny"})

    result = await Orchestrator(client, MODELS).run(USER_MESSAGES, tools=[weather_tool(handler)])

    assert result == "Sunny, go to Belem."
    assert len(client.completions.calls) == 2


async def test_tool_call_sends_assistant_message_and_tool_result_back():
    client = FakeClient(
        tool_calls(("call-1", "get_weather", '{"city": "Lisbon"}'), content="Checking."),
        answer("Sunny, go to Belem."),
    )
    handler = RecordingHandler({"forecast": "sunny"})

    await Orchestrator(client, MODELS).run(USER_MESSAGES, tools=[weather_tool(handler)])

    assert client.completions.calls[1]["messages"] == [
        *USER_MESSAGES,
        {
            "role": "assistant",
            "content": "Checking.",
            "tool_calls": [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {"name": "get_weather", "arguments": '{"city": "Lisbon"}'},
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "call-1",
            "content": json.dumps({"forecast": "sunny"}),
        },
    ]


async def test_tool_call_without_content_sends_none_content():
    client = FakeClient(
        tool_calls(("call-1", "get_weather", '{"city": "Lisbon"}')),
        answer("Sunny."),
    )

    await Orchestrator(client, MODELS).run(
        USER_MESSAGES, tools=[weather_tool(RecordingHandler({}))]
    )

    assistant_message = client.completions.calls[1]["messages"][-2]
    assert assistant_message["role"] == "assistant"
    assert assistant_message["content"] is None


async def test_string_tool_result_is_sent_as_is():
    client = FakeClient(
        tool_calls(("call-1", "get_weather", '{"city": "Lisbon"}')),
        answer("Sunny."),
    )
    handler = RecordingHandler("sunny all weekend")

    await Orchestrator(client, MODELS).run(USER_MESSAGES, tools=[weather_tool(handler)])

    assert client.completions.calls[1]["messages"][-1]["content"] == "sunny all weekend"


async def test_several_tool_calls_each_get_a_tool_message_in_order():
    client = FakeClient(
        tool_calls(
            ("call-1", "get_weather", '{"city": "Lisbon"}'),
            ("call-2", "get_weather", '{"city": "Porto"}'),
        ),
        answer("Both sunny."),
    )
    handler = RecordingHandler({"forecast": "sunny"})

    await Orchestrator(client, MODELS).run(USER_MESSAGES, tools=[weather_tool(handler)])

    tool_messages = [m for m in client.completions.calls[1]["messages"] if m["role"] == "tool"]
    assert [m["tool_call_id"] for m in tool_messages] == ["call-1", "call-2"]
    assert handler.calls == [{"city": "Lisbon"}, {"city": "Porto"}]


async def test_unknown_tool_sends_error_back_and_continues():
    client = FakeClient(
        tool_calls(("call-1", "book_flight", '{"to": "Lisbon"}')),
        answer("I cannot book flights."),
    )

    result = await Orchestrator(client, MODELS).run(
        USER_MESSAGES, tools=[weather_tool(RecordingHandler({}))]
    )

    assert result == "I cannot book flights."
    tool_message = client.completions.calls[1]["messages"][-1]
    assert tool_message["role"] == "tool"
    assert tool_message["tool_call_id"] == "call-1"
    assert "error" in tool_message["content"].lower()


async def test_invalid_json_arguments_send_error_back_and_continue():
    client = FakeClient(
        tool_calls(("call-1", "get_weather", "{city: Lisbon")),
        answer("Sorry."),
    )
    handler = RecordingHandler({})

    result = await Orchestrator(client, MODELS).run(USER_MESSAGES, tools=[weather_tool(handler)])

    assert result == "Sorry."
    assert handler.calls == []
    tool_message = client.completions.calls[1]["messages"][-1]
    assert tool_message["role"] == "tool"
    assert "error" in tool_message["content"].lower()


async def test_failing_handler_sends_error_back_and_continues():
    client = FakeClient(
        tool_calls(("call-1", "get_weather", '{"city": "Lisbon"}')),
        answer("Weather unknown."),
    )

    result = await Orchestrator(client, MODELS).run(
        USER_MESSAGES, tools=[weather_tool(failing_handler)]
    )

    assert result == "Weather unknown."
    tool_message = client.completions.calls[1]["messages"][-1]
    assert tool_message["role"] == "tool"
    assert "error" in tool_message["content"].lower()


async def test_caller_messages_are_not_mutated():
    messages = [{"role": "user", "content": "Plan a weekend in Lisbon."}]
    client = FakeClient(
        tool_calls(("call-1", "get_weather", '{"city": "Lisbon"}')),
        answer("Sunny."),
    )

    await Orchestrator(client, MODELS).run(messages, tools=[weather_tool(RecordingHandler({}))])

    assert messages == [{"role": "user", "content": "Plan a weekend in Lisbon."}]


async def test_too_many_steps_raises_llm_error_after_max_steps_calls():
    client = FakeClient(
        *[tool_calls((f"call-{i}", "get_weather", '{"city": "Lisbon"}')) for i in range(10)]
    )

    with pytest.raises(LLMError):
        await Orchestrator(client, MODELS, max_steps=3).run(
            USER_MESSAGES, tools=[weather_tool(RecordingHandler({}))]
        )

    assert len(client.completions.calls) == 3


async def test_failing_model_falls_back_to_next_model():
    client = FakeClient(connection_error(), answer("From model b."))

    result = await Orchestrator(client, MODELS).run(USER_MESSAGES)

    assert result == "From model b."
    assert [call["model"] for call in client.completions.calls] == ["model-a", "model-b"]


async def test_fallback_retries_the_same_request():
    client = FakeClient(connection_error(), answer("From model b."))

    await Orchestrator(client, MODELS).run(USER_MESSAGES)

    first, second = client.completions.calls
    assert second["messages"] == first["messages"]


async def test_fallback_goes_through_models_in_order():
    client = FakeClient(connection_error(), connection_error(), answer("From model c."))

    result = await Orchestrator(client, MODELS).run(USER_MESSAGES)

    assert result == "From model c."
    assert [call["model"] for call in client.completions.calls] == MODELS


async def test_every_model_failing_raises_llm_error():
    client = FakeClient(connection_error(), connection_error(), connection_error())

    with pytest.raises(LLMError):
        await Orchestrator(client, MODELS).run(USER_MESSAGES)

    assert len(client.completions.calls) == 3


async def test_response_without_choices_falls_back_to_next_model():
    client = FakeClient(no_choices(), answer("From model b."))

    result = await Orchestrator(client, MODELS).run(USER_MESSAGES)

    assert result == "From model b."
    assert [call["model"] for call in client.completions.calls] == ["model-a", "model-b"]


async def test_empty_answer_from_every_model_raises_llm_error():
    client = FakeClient(answer(""), answer(None), answer(""))

    with pytest.raises(LLMError):
        await Orchestrator(client, MODELS).run(USER_MESSAGES)

    assert len(client.completions.calls) == 3


async def test_empty_answer_falls_back_to_next_model():
    # Seen live: a reasoning model can answer with no content at all.
    client = FakeClient(answer(None), answer("From model b."))

    result = await Orchestrator(client, MODELS).run(USER_MESSAGES)

    assert result == "From model b."
    assert [call["model"] for call in client.completions.calls] == ["model-a", "model-b"]


async def test_handler_error_text_is_not_sent_to_the_model():
    async def database_error(**kwargs):
        raise RuntimeError("INSERT INTO users VALUES ('jane.doe@example.com')")

    client = FakeClient(
        tool_calls(("call-1", "get_weather", '{"city": "Lisbon"}')),
        answer("Weather unknown."),
    )

    await Orchestrator(client, MODELS).run(USER_MESSAGES, tools=[weather_tool(database_error)])

    tool_message = client.completions.calls[1]["messages"][-1]
    assert "jane.doe" not in tool_message["content"]
    assert json.loads(tool_message["content"]) == {"error": "tool failed"}


async def test_tool_error_message_is_sent_to_the_model():
    async def unknown_city(**kwargs):
        raise ToolError("unknown city: Atlantis")

    client = FakeClient(
        tool_calls(("call-1", "get_weather", '{"city": "Atlantis"}')),
        answer("No such city."),
    )

    await Orchestrator(client, MODELS).run(USER_MESSAGES, tools=[weather_tool(unknown_city)])

    tool_message = client.completions.calls[1]["messages"][-1]
    assert json.loads(tool_message["content"]) == {"error": "unknown city: Atlantis"}


async def test_arguments_that_are_not_an_object_send_error_back():
    handler = RecordingHandler({})
    client = FakeClient(
        tool_calls(("call-1", "get_weather", '["Lisbon"]')),
        answer("Done."),
    )

    await Orchestrator(client, MODELS).run(USER_MESSAGES, tools=[weather_tool(handler)])

    assert handler.calls == []
    assert "error" in client.completions.calls[1]["messages"][-1]["content"]


async def test_tools_asked_for_on_the_last_step_are_not_run():
    handler = RecordingHandler({})
    client = FakeClient(
        *[tool_calls((f"call-{i}", "get_weather", '{"city": "Lisbon"}')) for i in range(3)]
    )

    with pytest.raises(LLMError):
        await Orchestrator(client, MODELS, max_steps=3).run(
            USER_MESSAGES, tools=[weather_tool(handler)]
        )

    assert len(handler.calls) == 2


async def test_rejected_api_key_stops_without_trying_other_models():
    request = httpx2.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    response = httpx2.Response(401, request=request)
    client = FakeClient(openai.AuthenticationError("bad key", response=response, body=None))

    with pytest.raises(LLMError, match="API key"):
        await Orchestrator(client, MODELS).run(USER_MESSAGES)

    assert len(client.completions.calls) == 1


async def test_every_model_failing_keeps_the_last_error():
    last = connection_error()
    client = FakeClient(connection_error(), connection_error(), last)

    with pytest.raises(LLMError) as raised:
        await Orchestrator(client, MODELS).run(USER_MESSAGES)

    assert raised.value.__cause__ is last


async def test_slow_model_raises_llm_error_after_the_deadline():
    class SlowCompletions:
        async def create(self, **kwargs):
            await asyncio.sleep(10)

    client = SimpleNamespace(chat=SimpleNamespace(completions=SlowCompletions()))

    with pytest.raises(LLMError, match="seconds"):
        await Orchestrator(client, MODELS, deadline_seconds=0.05).run(USER_MESSAGES)


async def test_converse_returns_the_whole_conversation():
    client = FakeClient(
        tool_calls(("call-1", "get_weather", '{"city": "Lisbon"}')),
        answer("Sunny."),
    )

    conversation = await Orchestrator(client, MODELS).converse(
        USER_MESSAGES, tools=[weather_tool(RecordingHandler({"sky": "clear"}))]
    )

    assert [m["role"] for m in conversation] == ["user", "assistant", "tool", "assistant"]
    assert conversation[-1] == {"role": "assistant", "content": "Sunny."}
