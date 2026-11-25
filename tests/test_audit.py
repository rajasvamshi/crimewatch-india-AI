import json

from src.crimewatch.audit import AuditLogger, redact, verify_chain


def test_records_are_json_lines_with_identity(tmp_path):
    log = AuditLogger(tmp_path / "a" / "audit.jsonl")
    log.log("login", user="sp.hyd", role="supervisor", session_id="abc", details={"method": "local"})
    log.log("export", user="sp.hyd", role="supervisor", session_id="abc", details={"rows": 10})
    lines = (tmp_path / "a" / "audit.jsonl").read_text().splitlines()
    recs = [json.loads(line) for line in lines]
    assert [r["event"] for r in recs] == ["login", "export"]
    assert recs[0]["user"] == "sp.hyd" and recs[0]["session"] == "abc"
    assert recs[1]["prev"] == recs[0]["hash"]
    assert verify_chain(lines)


def test_tampering_is_detected(tmp_path):
    p = tmp_path / "audit.jsonl"
    log = AuditLogger(p)
    for i in range(3):
        log.log("view", user="u", details={"i": i})
    lines = p.read_text().splitlines()
    rec = json.loads(lines[1])
    rec["user"] = "someone-else"
    tampered = [lines[0], json.dumps(rec, sort_keys=True), lines[2]]
    assert not verify_chain(tampered)
    assert not verify_chain([lines[0], lines[2]])  # deleted line


def test_chain_continues_across_restarts(tmp_path):
    p = tmp_path / "audit.jsonl"
    AuditLogger(p).log("a")
    AuditLogger(p).log("b")
    assert verify_chain(p.read_text().splitlines())


def test_secrets_are_redacted():
    out = redact({"password": "x", "nested": {"api_key": "y", "ok": 1}, "Authorization": "Bearer z", "list": ["a"]})
    assert out["password"] == "[REDACTED]"
    assert out["nested"] == {"api_key": "[REDACTED]", "ok": 1}
    assert out["Authorization"] == "[REDACTED]"
    assert out["list"] == ["a"]
    assert len(redact("x" * 5000)) <= 2001
