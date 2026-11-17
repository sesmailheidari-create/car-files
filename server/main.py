import hashlib, hmac, json, os, sqlite3, time
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse

BASE = Path(__file__).parent
PASSWORD = os.getenv("APP_PASSWORD", "")
DB_PATH = os.getenv("DB_PATH", "data/cases.db")
if not PASSWORD:
    raise SystemExit("APP_PASSWORD را در فایل .env بنویسید")
TOKEN = hmac.new(PASSWORD.encode(), b"session", hashlib.sha256).hexdigest()
app = FastAPI()


def db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.execute("CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, created INTEGER, data TEXT)")
    return c


def auth(req: Request):
    if req.cookies.get("t") != TOKEN:
        raise HTTPException(401)


@app.post("/api/login")
async def login(req: Request, res: Response):
    body = await req.json()
    if not hmac.compare_digest(str(body.get("password", "")), PASSWORD):
        raise HTTPException(401)
    res.set_cookie("t", TOKEN, max_age=60 * 86400, httponly=True, samesite="lax")
    return {"ok": True}


@app.get("/api/cases")
def list_cases(req: Request, q: str = ""):
    auth(req)
    c = db()
    rows = c.execute("SELECT id, data FROM cases ORDER BY id DESC").fetchall()
    c.close()
    out = []
    for id_, data in rows:
        d = json.loads(data)
        text = " ".join(str(d.get(k, "")) for k in ("system", "model", "owner", "phone", "vin", "plate"))
        if q in text:
            out.append({"id": id_, "plate": d.get("plate"), "system": d.get("system"), "phone": d.get("phone"), "owner": d.get("owner"), "date": d.get("date")})
    return out


@app.get("/api/cases/{id}")
def get_case(id: int, req: Request):
    auth(req)
    c = db()
    row = c.execute("SELECT data FROM cases WHERE id=?", (id,)).fetchone()
    c.close()
    if not row:
        raise HTTPException(404)
    return json.loads(row[0])


@app.post("/api/cases")
async def create(req: Request):
    auth(req)
    data = json.dumps(await req.json(), ensure_ascii=False)
    c = db()
    with c:
        cur = c.execute("INSERT INTO cases (created, data) VALUES (?,?)", (int(time.time()), data))
    c.close()
    return {"id": cur.lastrowid}


@app.put("/api/cases/{id}")
async def update(id: int, req: Request):
    auth(req)
    data = json.dumps(await req.json(), ensure_ascii=False)
    c = db()
    with c:
        c.execute("UPDATE cases SET data=? WHERE id=?", (data, id))
    c.close()
    return {"id": id}


@app.delete("/api/cases/{id}")
def delete(id: int, req: Request):
    auth(req)
    c = db()
    with c:
        c.execute("DELETE FROM cases WHERE id=?", (id,))
    c.close()
    return {"ok": True}


@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")
