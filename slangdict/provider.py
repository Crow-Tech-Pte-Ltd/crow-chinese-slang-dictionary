"""Bounded OpenRouter client. Keys and raw responses never enter release data.

Credential validation and redacted HTTP handling follow Crow Chinese Dictionary's
MIT provider client. Reservations survive interruption; unknown charges stay held.
"""

import json, hashlib, sqlite3, time, urllib.request, urllib.error, re, math
from pathlib import Path
from contextlib import contextmanager

API = "https://openrouter.ai/api/v1/chat/completions"


class ProviderError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ProviderError("redirect-refused")


def canonical(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(x):
    return hashlib.sha256(
        (x if isinstance(x, str) else canonical(x)).encode()
    ).hexdigest()


def read_key(path):
    key = Path(path).read_text().strip()
    if not key or len(key) > 8192 or re.search(r"[\s\x00-\x1f]", key):
        raise ProviderError("invalid-explicit-key-file")
    return key


class Client:
    def __init__(self, root, key_file, max_usd=2):
        self.root = Path(root)
        self.work = self.root / "work"
        self.work.mkdir(exist_ok=True)
        self.key_file = key_file
        self.path = self.work / "budget.sqlite"
        self.max_micro = round(max_usd * 1e6)
        with self.connect() as db:
            db.executescript(
                "CREATE TABLE IF NOT EXISTS budget(id INTEGER PRIMARY KEY,cap INTEGER,spent INTEGER,calls INTEGER,halted INTEGER); CREATE TABLE IF NOT EXISTS requests(id TEXT PRIMARY KEY,phase TEXT,model TEXT,state TEXT,reserved INTEGER,settled INTEGER,created REAL,path TEXT,error TEXT);"
            )
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT cap FROM budget WHERE id=1").fetchone()
            if row and row[0] != self.max_micro:
                raise ProviderError("persistent-cap-change-refused")
            db.execute(
                "INSERT OR IGNORE INTO budget VALUES(1,?,0,0,0)", (self.max_micro,)
            )
            db.commit()

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA busy_timeout=30000")
        try:
            yield db
        finally:
            db.close()

    def call(self, phase, model, system, user, web=False, max_tokens=4096):
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": canonical(user)},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "reasoning": {"effort": "low", "exclude": True},
            "provider": {
                "data_collection": "deny",
                "require_parameters": True,
                "max_price": {"prompt": 1.1, "completion": 2.2},
            },
            "stream": False,
        }
        if model.startswith("deepseek/"):
            payload["reasoning"] = {"enabled": False, "exclude": True}
        if web:
            payload["plugins"] = [
                {
                    "id": "web",
                    "engine": "exa",
                    "mode": "auto",
                    "max_results": 5,
                    "exclude_domains": [
                        "*.moe.edu.tw",
                        "*.pleco.com",
                        "*.oxfordreference.com",
                        "*.oxfordlearnersdictionaries.com",
                        "*.zdic.net",
                        "moedict.tw",
                        "hanzidesk.com",
                        "*.hanzidesk.pages.dev",
                        "crow.sg",
                        "github.com/Crow-Tech-Pte-Ltd/*",
                    ],
                }
            ]
        fp = digest({"version": "crow-slang-v1", "phase": phase, "payload": payload})
        dest = self.work / (fp + ".json")
        bound = 2 * len(canonical(payload).encode()) + 4096 + (96000 if web else 0)
        reserve = math.ceil(bound * 1.1 + max_tokens * 2.2 + (7000 if web else 0))
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute(
                "SELECT state,path FROM requests WHERE id=?", (fp,)
            ).fetchone()
            if prior:
                db.commit()
                if prior[0] == "completed":
                    return json.loads(Path(prior[1]).read_text())
                raise ProviderError("previous-request-" + prior[0] + "-not-retried")
            cap, spent, calls, halted = db.execute(
                "SELECT cap,spent,calls,halted FROM budget WHERE id=1"
            ).fetchone()
            if halted or calls >= 180 or spent + reserve > cap:
                raise ProviderError("persistent-budget-cap-reached")
            db.execute(
                "UPDATE budget SET spent=spent+?,calls=calls+1 WHERE id=1", (reserve,)
            )
            db.execute(
                "INSERT INTO requests VALUES(?,?,?,'requesting',?,?,?,NULL,NULL)",
                (fp, phase, model, reserve, reserve, time.time()),
            )
            db.commit()
        key = read_key(self.key_file)
        request = urllib.request.Request(
            API,
            data=canonical(payload).encode(),
            method="POST",
            headers={
                "Authorization": "Bearer " + key,
                "Content-Type": "application/json",
                "User-Agent": "crow-chinese-slang-dictionary/0.1",
            },
        )
        try:
            with urllib.request.build_opener(NoRedirect()).open(
                request, timeout=180
            ) as reply:
                raw = reply.read(8 * 1024**2 + 1)
            if len(raw) > 8 * 1024**2 or key.encode() in raw:
                raise ProviderError("oversized-or-credential-echo-response")
            response = json.loads(raw)
            if not isinstance(response, dict) or response.get("error"):
                raise ProviderError("provider-response-error")
            if response.get("model") != model:
                raise ProviderError("model-identity-mismatch")
            actual = response.get("usage", {}).get("cost")
            settled = (
                (math.ceil(float(actual) * 1e6) + (7000 if web else 0))
                if isinstance(actual, (int, float))
                and math.isfinite(actual)
                and actual >= 0
                else reserve
            )
            # Store the response atomically before committing success. A crash never causes
            # an automatic resubmission with an unknown charge.
            tmp = dest.with_suffix(".pending")
            tmp.write_bytes(raw)
            tmp.replace(dest)
            with self.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute(
                    "UPDATE budget SET spent=spent+?,halted=MAX(halted,?) WHERE id=1",
                    (settled - reserve, int(settled > reserve)),
                )
                db.execute(
                    "UPDATE requests SET state='completed',settled=?,path=? WHERE id=?",
                    (settled, str(dest), fp),
                )
                db.commit()
            if settled > reserve:
                raise ProviderError("provider-cost-exceeded-reservation-halted")
            return response
        except Exception as exc:
            code = exc.code if isinstance(exc, urllib.error.HTTPError) else None
            state = (
                "rejected"
                if code in [400, 401, 402, 403, 404, 422]
                else "unknown-charge"
            )
            with self.connect() as db:
                db.execute(
                    "UPDATE requests SET state=?,error=? WHERE id=? AND state='requesting'",
                    (state, "HTTP-" + str(code) if code else type(exc).__name__, fp),
                )
                db.commit()
            raise ProviderError(
                "provider-request-failed-" + (str(code) if code else "unknown-charge")
            ) from None

    def summary(self):
        with self.connect() as db:
            cap, spent, calls, halted = db.execute(
                "SELECT cap,spent,calls,halted FROM budget WHERE id=1"
            ).fetchone()
            states = dict(
                db.execute("SELECT state,COUNT(*) FROM requests GROUP BY state")
            )
        return {
            "capUsd": cap / 1e6,
            "spentOrReservedUsd": spent / 1e6,
            "calls": calls,
            "halted": bool(halted),
            "states": states,
            "reservationsAreNotAlwaysFinalCharges": True,
        }


def output(response):
    choice = response.get("choices", [{}])[0]
    if choice.get("finish_reason") != "stop":
        raise ValueError("nonfinal-or-truncated-output")
    text = choice.get("message", {}).get("content")
    if not isinstance(text, str):
        raise ValueError("missing-json-content")
    return json.loads(text)
