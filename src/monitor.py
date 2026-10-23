"""Monitor de precios de Xiaomi México y Liverpool. Solo datos verificables."""
import json, os, re, sqlite3, logging, time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
LOG = logging.getLogger("prices")
UA = "XiaomiPriceMonitor/1.0 (+https://github.com/FerMartinez17125/xiaomi-price-monitor)"
def amount(value):
    s = str(value).strip().replace("MXN","").replace("$","").replace(",","").strip()
    if not re.fullmatch(r"\d+(?:\.\d{1,2})?",s): return None
    return int(Decimal(s)*100)
def mxn(c): return f"${c/100:,.2f} MXN"
def normalized(title): return re.sub(r"\s+"," ",title).strip().lower()
def is_model(title,product):
    t=normalized(title)
    if product["id"].startswith("xiaomi-15t"): return bool(re.search(r"\b15\s*t\s*pro\b",t))
    return bool(re.search(r"\b17\b(?!\s*(?:t|pro|ultra))",t))
def extract(html, product, source):
    soup=BeautifulSoup(html,"html.parser")
    h1=soup.select_one("h1")
    title=(h1.get_text(" ",strip=True) if h1 else "")
    if not title:
        og=soup.select_one('meta[property="og:title"]')
        title=og.get("content","") if og else (soup.title.get_text(" ",strip=True) if soup.title else "")
    if not is_model(title,product): raise ValueError("Modelo no confirmado en título")
    if re.search(r"usad[oa]|reacondicionad[oa]|refurbished|seminuev[oa]|open.box",title,re.I):
        raise ValueError("Producto no nuevo")
    # Un precio en JSON-LD solo se acepta si coincide modelo y memoria en el nombre de la oferta.
    offers=[]
    for script in soup.select('script[type="application/ld+json"]'):
        try: doc=json.loads(script.string or script.get_text())
        except (ValueError,TypeError): continue
        def visit(obj):
            if isinstance(obj,list):
                for x in obj: visit(x)
            if not isinstance(obj,dict): return
            typ=str(obj.get("@type","")).lower()
            if "product" in typ:
                name=str(obj.get("name",""))
                if is_model(name,product) and re.search(r"(?<!\d)512\s*(?:gb|gib)\b",name,re.I):
                    o=obj.get("offers",{})
                    if isinstance(o,dict): offers.append(o)
            for key in ("@graph","mainEntity","itemListElement"):
                if key in obj: visit(obj[key])
        visit(doc)
    values=set()
    for offer in offers:
        if "aggregate" in str(offer.get("@type","")).lower(): continue
        availability=str(offer.get("availability","")).lower()
        if any(s in availability for s in ("outofstock","soldout","preorder")): continue
        condition=str(offer.get("itemCondition","")).lower()
        if condition and "newcondition" not in condition: continue
        if str(offer.get("priceCurrency","MXN")).upper()!="MXN": continue
        raw=offer.get("price")
        if raw is None and isinstance(offer.get("priceSpecification"),dict):
            raw=offer["priceSpecification"].get("price")
        val=amount(raw)
        if val: values.add(val)
    if len(values)!=1: raise ValueError("Precio o SKU de 512 GB no verificable en datos estructurados")
    price=values.pop()
    if not (300000<=price<=8000000): raise ValueError("Precio sospechoso")
    txt=(soup.select_one("main") or soup).get_text(" ",strip=True)[:12000]
    # Evitar un JSON-LD ambiguo cuando la ficha visual selecciona otra memoria.
    if re.search(r"\b(?:usado|reacondicionado)\b",title,re.I): raise ValueError("No nuevo")
    coupon=re.search(r"\bcup[oó]n\b.{0,45}",txt,re.I)
    promo=re.search(r"\b(?:promoci[oó]n especial|descuento especial)\b.{0,45}",txt,re.I)
    msi=bool(re.search(r"\b\d{1,2}\s*meses sin intereses\b",txt,re.I))
    return {"price":price,"title":title,"coupon":coupon.group(0) if coupon else "",
            "promo":promo.group(0) if promo else "","msi":int(msi)}
def fetch(url):
    p=urlparse(url)
    if p.scheme!="https" or p.hostname not in ("www.mi.com","www.liverpool.com.mx"):
        raise ValueError("URL de tienda no autorizada")
    with requests.Session() as session:
        session.headers.update({"User-Agent":UA,"Accept":"text/html"})
        robots=session.get(f"{p.scheme}://{p.netloc}/robots.txt",timeout=15)
        if robots.status_code==200:
            parser=RobotFileParser(); parser.parse(robots.text.splitlines())
            if not parser.can_fetch(UA,url): raise PermissionError("robots.txt no permite la consulta")
        elif robots.status_code not in (404,410):
            raise PermissionError(f"robots.txt sin verificar: HTTP {robots.status_code}")
        response=session.get(url,timeout=25)
        if response.status_code in (401,403,429): raise PermissionError(f"Acceso restringido HTTP {response.status_code}")
        response.raise_for_status()
        if urlparse(response.url).hostname!=p.hostname: raise ValueError("Redirección externa")
        if "html" not in response.headers.get("Content-Type","").lower(): raise ValueError("Respuesta no HTML")
        if re.search(r"captcha|verify you are human|access denied|cf-chl-",response.text[:5000],re.I):
            raise PermissionError("Protección anti-bot")
        return response.text
def notify(message):
    token=os.getenv("TELEGRAM_BOT_TOKEN",""); chat=os.getenv("TELEGRAM_CHAT_ID","")
    if not (token and chat): return False
    response=requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
       json={"chat_id":chat,"text":message[:4000],"disable_web_page_preview":True},timeout=20)
    if response.status_code!=200 or not response.json().get("ok"):
        raise RuntimeError(f"Telegram HTTP {response.status_code}")
    return True
def schema(db):
    db.executescript("""
    PRAGMA journal_mode=DELETE;
    CREATE TABLE IF NOT EXISTS observations(
      id INTEGER PRIMARY KEY,ts TEXT NOT NULL,source TEXT NOT NULL,product TEXT NOT NULL,
      store TEXT NOT NULL,price INTEGER NOT NULL,title TEXT NOT NULL,coupon TEXT NOT NULL,
      promo TEXT NOT NULL,msi INTEGER NOT NULL);
    CREATE INDEX IF NOT EXISTS obs_idx ON observations(source,id);
    CREATE TABLE IF NOT EXISTS checks(id INTEGER PRIMARY KEY,ts TEXT,source TEXT,status TEXT,detail TEXT);
    CREATE TABLE IF NOT EXISTS outbox(id INTEGER PRIMARY KEY,message TEXT NOT NULL,delivered TEXT);
    CREATE TABLE IF NOT EXISTS state(source TEXT,kind TEXT,value TEXT,PRIMARY KEY(source,kind));
    """)
def run():
    cfg=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))
    now=datetime.now(ZoneInfo(cfg["timezone"])); ts=now.astimezone(timezone.utc).isoformat()
    (ROOT/"data").mkdir(exist_ok=True)
    db=sqlite3.connect(ROOT/"data"/"prices.sqlite"); db.row_factory=sqlite3.Row; schema(db)
    products={p["id"]:p for p in cfg["products"]}; successes=0
    for src in cfg["sources"]:
        sid=src["id"]
        if not src.get("enabled") or not src.get("url"):
            db.execute("INSERT INTO checks(ts,source,status,detail) VALUES(?,?,?,?)",
                       (ts,sid,"pendiente",src.get("notes","Sin URL")));continue
        try:
            q=extract(fetch(src["url"]),products[src["product_id"]],src)
            old=db.execute("SELECT * FROM observations WHERE source=? ORDER BY id DESC LIMIT 1",(sid,)).fetchone()
            db.execute("INSERT INTO observations(ts,source,product,store,price,title,coupon,promo,msi) VALUES(?,?,?,?,?,?,?,?,?)",
                (ts,sid,src["product_id"],src["store"],q["price"],q["title"],q["coupon"],q["promo"],q["msi"]))
            db.execute("INSERT INTO checks(ts,source,status,detail) VALUES(?,?,?,?)",
                       (ts,sid,"ok",mxn(q["price"])))
            successes+=1
            p=products[src["product_id"]]; signals=[]
            target=int(Decimal(str(p["target_price"]))*100)
            previous_state=db.execute("SELECT value FROM state WHERE source=? AND kind='target'",(sid,)).fetchone()
            if q["price"]<=target:
                if previous_state is None or q["price"]<int(previous_state["value"]):
                    signals.append(f"Objetivo alcanzado: {mxn(target)}")
                    db.execute("INSERT INTO state(source,kind,value) VALUES(?,'target',?) ON CONFLICT(source,kind) DO UPDATE SET value=excluded.value",(sid,str(q["price"])))
            else: db.execute("DELETE FROM state WHERE source=? AND kind='target'",(sid,))
            if old:
                drop=(old["price"]-q["price"])/old["price"]*100
                if drop>10: signals.append(f"Bajó {drop:.1f}% (>10%)")
                elif drop>5: signals.append(f"Bajó {drop:.1f}% (>5%)")
                if q["coupon"] and q["coupon"]!=old["coupon"]:signals.append("Cupón: "+q["coupon"])
                if q["promo"] and q["promo"]!=old["promo"]:signals.append("Promoción: "+q["promo"])
                if q["msi"] and not old["msi"]:signals.append("Meses sin intereses anunciados")
            if signals:
                msg=f"{p['name']} 512 GB — {src['store']}\n{mxn(q['price'])}\n"+"\n".join(signals)+"\n"+src["url"]
                db.execute("INSERT INTO outbox(message) VALUES(?)",(msg,))
            LOG.info("OK %s %s",sid,mxn(q["price"]))
        except (ValueError,RuntimeError,PermissionError,requests.RequestException) as exc:
            LOG.warning("%s: %s",sid,exc)
            db.execute("INSERT INTO checks(ts,source,status,detail) VALUES(?,?,?,?)",
                       (ts,sid,"error",str(exc)[:250]))
        db.commit()
        time.sleep(0.2)
    if successes==0:
        today=now.strftime("%Y-%m-%d")
        state=db.execute("SELECT value FROM state WHERE source='_system' AND kind='health'").fetchone()
        if not state or state["value"]!=today:
            db.execute("INSERT INTO state(source,kind,value) VALUES('_system','health',?) ON CONFLICT(source,kind) DO UPDATE SET value=excluded.value",(today,))
            db.execute("INSERT INTO outbox(message) VALUES(?)",("Monitor Xiaomi: ninguna fuente produjo un precio validado. Revisar reportes.",))
    if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
        for row in db.execute("SELECT id,message FROM outbox WHERE delivered IS NULL ORDER BY id LIMIT 10").fetchall():
            try:
                if notify(row["message"]): db.execute("UPDATE outbox SET delivered=? WHERE id=?",(ts,row["id"]))
            except (ValueError,RuntimeError,requests.RequestException) as exc: LOG.warning("Telegram: %s",str(exc).replace(os.getenv("TELEGRAM_BOT_TOKEN",""),"[SECRET]"))
    reports=ROOT/"reports"; (reports/"daily").mkdir(parents=True,exist_ok=True); (reports/"weekly").mkdir(parents=True,exist_ok=True)
    lines=[f"# Monitor Xiaomi — {now.strftime('%Y-%m-%d %H:%M %Z')}","",f"Consultas válidas: {successes}/{sum(bool(x.get('enabled')) for x in cfg['sources'])}","",
      "Precios únicamente observados y verificados; no se usan cifras ficticias.",""]
    for p in cfg["products"]:
        hist=db.execute("SELECT * FROM observations WHERE product=? ORDER BY id DESC",(p["id"],)).fetchall()
        low=min((r["price"] for r in hist),default=None)
        high=max((r["price"] for r in hist),default=None)
        lines.extend([f"## {p['name']} 512 GB",f"Objetivo: {mxn(int(p['target_price']*100))}",
          f"Mínimo histórico: {mxn(low) if low else 'Sin datos'}",
          f"Máximo histórico: {mxn(high) if high else 'Sin datos'}","",
          "| Tienda | Precio último | Variación | Descuento vs máximo histórico | Estado |",
          "|---|---:|---:|---:|---|"])
        current=[]
        for src in (x for x in cfg["sources"] if x["product_id"]==p["id"]):
            check=db.execute("SELECT * FROM checks WHERE source=? ORDER BY id DESC LIMIT 1",(src["id"],)).fetchone()
            rows=[r for r in hist if r["source"]==src["id"]]
            latest=rows[0] if rows else None
            # Una consulta fallida invalida el precio para comparación actual.
            current_quote=latest if check and check["status"]=="ok" and latest and latest["ts"]==check["ts"] else None
            if current_quote: current.append((latest["price"],src["store"],src["url"]))
            change=f"{(latest['price']-rows[1]['price'])/100:+,.2f} MXN ({(latest['price']/rows[1]['price']-1)*100:+.1f}%)" if len(rows)>1 else "—"
            discount=f"{(1-latest['price']/high)*100:.1f}%" if latest and high else "—"
            lines.append(f"| {src['store']} | {mxn(latest['price']) if latest else '—'} | {change} | {discount} | {check['status'] if check else 'sin ejecutar'} |")
        if current:
            best=min(current);lines.append(f"\n**Mejor oferta actual comprobada:** {mxn(best[0])} — {best[1]} — {best[2]}\n")
        else:lines.append("\n**Mejor oferta actual:** sin precios validados en esta ejecución.\n")
    lines.extend(["","## Estado de fuentes",""])
    for s in cfg["sources"]:
        row=db.execute("SELECT * FROM checks WHERE source=? ORDER BY id DESC LIMIT 1",(s["id"],)).fetchone()
        if row:lines.append(f"- {s['id']}: {row['status']} — {row['detail']}")
    content="\n".join(lines)+"\n"
    for path in (reports/"latest.md",reports/"daily"/f"{now:%Y-%m-%d}.md",reports/"weekly"/f"{now.isocalendar().year}-W{now.isocalendar().week:02d}.md"):
        path.write_text(content,encoding="utf-8")
    db.commit();db.close()
    LOG.info("Finalizado: %s cotizaciones verificadas",successes)
if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)
    run()
