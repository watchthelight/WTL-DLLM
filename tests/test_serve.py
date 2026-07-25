# wtl-dllm · tests/test_serve.py
# what: stub websocket streaming — schema-valid frames, verdict on final, error frame on junk
# by:   <wtl> watchthelight
# tags: tests, serve

import json

from fastapi.testclient import TestClient

from dllm.serve.app import STATE, app

client = TestClient(app)
FRAME_KEYS = {"step", "total_steps", "tokens", "committed", "conf", "just_committed", "done"}


def test_info_and_levels():
    STATE["stub"] = True
    info = client.get("/api/info").json()
    assert info["model"] == "stub" and info["levels"] == [1, 2, 3, 4, 5]
    lv = client.get("/api/levels").json()
    assert lv["1"]["canvas"] == 12 and lv["1"]["prompt"].endswith("=")


def test_ws_stream_schema_and_verdict():
    STATE["stub"] = True
    with client.websocket_connect("/ws/generate") as ws:
        ws.send_text(json.dumps({"level": 1, "seed": 4}))
        frames = []
        while True:
            f = json.loads(ws.receive_text())
            assert FRAME_KEYS <= set(f), f"missing keys: {FRAME_KEYS - set(f)}"
            n = len(f["tokens"])
            assert len(f["committed"]) == n == len(f["conf"])
            frames.append(f)
            if f["done"]:
                break
    assert frames[-1]["verdict"] == "correct"  # stub reveals the true answer
    assert frames[-1]["answer"]
    steps = [f["step"] for f in frames]
    assert steps == sorted(steps)


def test_ws_bad_request_gets_error_frame():
    with client.websocket_connect("/ws/generate") as ws:
        ws.send_text("{not json")
        f = json.loads(ws.receive_text())
        assert "error" in f
