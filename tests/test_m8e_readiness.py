"""M8E readiness classification with a local JSON-RPC executable fixture only."""
import json
from pathlib import Path

import pytest

from apps.core.codex_conversation_provider import CodexConversationProvider
from apps.core.local_private_ai import PrivatePilotGate
from apps.core.storage import SafeError, encode
from test_m8a_release import package
from test_m8b_readiness import runtime_package
from test_m8c_private import private_package, protected
from test_m8d_private import controller, isolated, private_ai_package, vault


def fake_app_server(tmp_path: Path, scenario: str) -> tuple[Path, Path]:
    forbidden = tmp_path / "ORIGINAL_SYNTHETIC_FORBIDDEN_TURN.marker"
    source = f'''#!/usr/bin/env python3
import json, sys, time
SCENARIO = {scenario!r}
FORBIDDEN = {str(forbidden)!r}
RAW = "ORIGINAL_SYNTHETIC_RAW_RPC_SENTINEL /private/Users/private/.codex/auth.json"
MODELS = [
    {{"model": "gpt-6-luna", "supportedReasoningEfforts": [{{"reasoningEffort": x}} for x in ["low", "medium", "high", "xhigh", "max"]]}},
    {{"model": "gpt-6.1-sol", "supportedReasoningEfforts": [{{"reasoningEffort": x}} for x in ["low", "medium", "high"]]}},
]
def send(message):
    sys.stdout.write(json.dumps(message) + "\\n")
    sys.stdout.flush()
for line in sys.stdin:
    request = json.loads(line)
    method = request.get("method")
    identifier = request.get("id")
    if method in {{"thread/start", "turn/start"}}:
        with open(FORBIDDEN, "w") as marker:
            marker.write(method)
        send({{"id": identifier, "result": {{}}}})
    elif method == "initialize":
        if SCENARIO == "initialize_rpc":
            send({{"id": identifier, "error": {{"code": -32000, "message": RAW}}}})
        else:
            send({{"id": identifier, "result": {{}}}})
    elif method == "initialized":
        continue
    elif method == "account/read":
        if SCENARIO == "account_rpc":
            send({{"id": identifier, "error": {{"code": -32000, "message": RAW}}}})
        elif SCENARIO == "account_exit":
            sys.exit(0)
        elif SCENARIO == "account_timeout":
            time.sleep(3)
        elif SCENARIO == "account_protocol":
            sys.stdout.write(RAW + "\\n")
            sys.stdout.flush()
        elif SCENARIO == "auth_missing":
            send({{"id": identifier, "result": {{"account": None}}}})
        elif SCENARIO == "auth_non_chatgpt":
            send({{"id": identifier, "result": {{"account": {{"type": "api", "accountId": RAW}}}}}})
        else:
            send({{"id": identifier, "result": {{"account": {{"type": "chatgpt", "accountId": RAW}}}}}})
    elif method == "model/list":
        if SCENARIO == "model_rpc":
            send({{"id": identifier, "error": {{"code": -32000, "message": RAW}}}})
        elif SCENARIO == "model_exit":
            sys.exit(0)
        elif SCENARIO == "model_timeout":
            time.sleep(3)
        elif SCENARIO == "model_protocol":
            sys.stdout.write(RAW + "\\n")
            sys.stdout.flush()
        elif SCENARIO == "model_missing":
            send({{"id": identifier, "result": {{"data": [MODELS[0]]}}}})
        elif SCENARIO == "model_unverifiable":
            models = json.loads(json.dumps(MODELS))
            models[1].pop("supportedReasoningEfforts")
            send({{"id": identifier, "result": {{"data": models}}}})
        elif SCENARIO == "effort_missing":
            models = json.loads(json.dumps(MODELS))
            models[0]["supportedReasoningEfforts"] = [{{"reasoningEffort": x}} for x in ["low", "medium", "high"]]
            send({{"id": identifier, "result": {{"data": models}}}})
        else:
            send({{"id": identifier, "result": {{"data": MODELS}}}})
    else:
        send({{"id": identifier, "error": {{"code": -32000, "message": RAW}}}})
'''
    executable = tmp_path / f"ORIGINAL_SYNTHETIC_APP_SERVER_{scenario}"
    executable.write_text(source)
    executable.chmod(0o700)
    return executable, forbidden


def fixture_gate(store, executable: Path):
    def factory(mode, model, effort):
        provider = CodexConversationProvider(
            model=model,
            effort=effort,
            executable=str(executable),
            budget=object(),
        )
        provider.readiness_timeout = 0.6
        return provider

    return PrivatePilotGate(store, provider_factory=factory)


@pytest.mark.parametrize(
    ("scenario", "expected"),
    [
        ("initialize_rpc", "PRIVATE_PROVIDER_ROUTE_UNAVAILABLE"),
        ("account_rpc", "PRIVATE_PROVIDER_ROUTE_UNAVAILABLE"),
        ("account_exit", "PRIVATE_PROVIDER_ROUTE_UNAVAILABLE"),
        ("account_timeout", "PRIVATE_PROVIDER_ROUTE_UNAVAILABLE"),
        ("account_protocol", "PRIVATE_PROVIDER_ROUTE_UNAVAILABLE"),
        ("model_rpc", "PRIVATE_PROVIDER_ROUTE_UNAVAILABLE"),
        ("model_exit", "PRIVATE_PROVIDER_ROUTE_UNAVAILABLE"),
        ("model_timeout", "PRIVATE_PROVIDER_ROUTE_UNAVAILABLE"),
        ("model_protocol", "PRIVATE_PROVIDER_ROUTE_UNAVAILABLE"),
        ("auth_missing", "EXISTING_CHATGPT_AUTH_REQUIRED"),
        ("auth_non_chatgpt", "EXISTING_CHATGPT_AUTH_REQUIRED"),
        ("model_missing", "PRIVATE_PROVIDER_PROFILE_UNVERIFIED"),
        ("model_unverifiable", "PRIVATE_PROVIDER_PROFILE_UNVERIFIED"),
        ("effort_missing", "PROVIDER_EFFORT_UNSUPPORTED"),
    ],
)
def test_readiness_preserves_sanitized_failure_categories(controller, tmp_path, scenario, expected):
    conversation_controller, _ = controller
    executable, forbidden = fake_app_server(tmp_path, scenario)
    gate = fixture_gate(conversation_controller.conversations.store, executable)

    with pytest.raises(SafeError) as raised:
        gate.activate("ORIGINAL_SYNTHETIC_SESSION", "a" * 64)

    assert raised.value.code == expected
    assert "ORIGINAL_SYNTHETIC_RAW_RPC_SENTINEL" not in str(raised.value)
    assert "/private/Users/private" not in str(raised.value)
    assert not gate.adapters
    assert not forbidden.exists()


def test_readiness_success_discards_account_data_and_never_starts_thread_or_turn(controller, tmp_path):
    conversation_controller, _ = controller
    executable, forbidden = fake_app_server(tmp_path, "success")
    provider = CodexConversationProvider(
        model="gpt-6-luna",
        effort="high",
        executable=str(executable),
        budget=object(),
    )
    provider.readiness_timeout = 0.6

    proof = provider.readiness()
    assert proof["account_type"] == "chatgpt"
    assert set(proof["models"]) == {"gpt-6-luna", "gpt-6.1-sol"}
    assert proof["inference_started"] is False and proof["thread_started"] is False
    assert "ORIGINAL_SYNTHETIC_RAW_RPC_SENTINEL" not in encode(proof)
    assert not forbidden.exists()

    gate = fixture_gate(conversation_controller.conversations.store, executable)
    assert gate.activate("ORIGINAL_SYNTHETIC_SESSION", "a" * 64)["state"] == "PRIVATE_AI_OWNER_CONSENTED"
    assert not forbidden.exists()
