from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional
from datetime import datetime
import sqlite3, json, uuid

DB = Path(__file__).with_name("billing.db")
app = FastAPI(title="Universal Billing API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

with db() as c:
    c.executescript("""
    CREATE TABLE IF NOT EXISTS business(id INTEGER PRIMARY KEY CHECK(id=1), name TEXT NOT NULL, business_type TEXT NOT NULL, owner_name TEXT, phone TEXT, email TEXT, gstin TEXT, state TEXT, address TEXT, tax_mode TEXT NOT NULL DEFAULT 'GST');
    CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, name TEXT NOT NULL, category TEXT, unit TEXT DEFAULT 'pcs', price REAL NOT NULL, gst_rate REAL DEFAULT 0, description TEXT, active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS invoices(id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_no TEXT UNIQUE, date TEXT, customer_name TEXT, customer_phone TEXT, customer_gstin TEXT, subtotal REAL, tax_total REAL, grand_total REAL, tax_mode TEXT, items_json TEXT);
    """)

class Business(BaseModel):
    name:str
    business_type:str
    owner_name:Optional[str]=""
    phone:Optional[str]=""
    email:Optional[str]=""
    gstin:Optional[str]=""
    state:Optional[str]=""
    address:Optional[str]=""
    tax_mode:str="GST"

class Product(BaseModel):
    sku:Optional[str]=""
    name:str
    category:Optional[str]=""
    unit:Optional[str]="pcs"
    price:float=Field(ge=0)
    gst_rate:float=Field(default=0,ge=0,le=100)
    description:Optional[str]=""

class Item(BaseModel):
    product_id:int
    quantity:float=Field(gt=0)

class Invoice(BaseModel):
    customer_name:str="Walk-in Customer"
    customer_phone:Optional[str]=""
    customer_gstin:Optional[str]=""
    items:list[Item]

@app.get("/api/health")
def health(): return {"status":"ok"}

@app.get("/api/business")
def get_business():
    with db() as c:
        r=c.execute("SELECT * FROM business WHERE id=1").fetchone()
        return dict(r) if r else None

@app.post("/api/business")
def save_business(x:Business):
    with db() as c:
        c.execute("""INSERT INTO business(id,name,business_type,owner_name,phone,email,gstin,state,address,tax_mode) VALUES(1,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET name=excluded.name,business_type=excluded.business_type,owner_name=excluded.owner_name,phone=excluded.phone,email=excluded.email,gstin=excluded.gstin,state=excluded.state,address=excluded.address,tax_mode=excluded.tax_mode""",
        (x.name,x.business_type,x.owner_name,x.phone,x.email,x.gstin,x.state,x.address,x.tax_mode))
    return {"saved":True}

@app.get("/api/products")
def products():
    with db() as c: return [dict(r) for r in c.execute("SELECT * FROM products WHERE active=1 ORDER BY name")]

@app.post("/api/products")
def add_product(x:Product):
    with db() as c:
        cur=c.execute("INSERT INTO products(sku,name,category,unit,price,gst_rate,description) VALUES(?,?,?,?,?,?,?)",(x.sku,x.name,x.category,x.unit,x.price,x.gst_rate,x.description))
        return dict(c.execute("SELECT * FROM products WHERE id=?",(cur.lastrowid,)).fetchone())

@app.delete("/api/products/{pid}")
def delete_product(pid:int):
    with db() as c:
        cur=c.execute("UPDATE products SET active=0 WHERE id=?",(pid,))
        if not cur.rowcount: raise HTTPException(404,"Product not found")
    return {"deleted":True}

@app.post("/api/invoices")
def create_invoice(x:Invoice):
    if not x.items: raise HTTPException(400,"Add at least one item")
    with db() as c:
        b=c.execute("SELECT * FROM business WHERE id=1").fetchone()
        if not b: raise HTTPException(400,"Complete business setup first")
        lines=[]; subtotal=0; tax_total=0
        for item in x.items:
            p=c.execute("SELECT * FROM products WHERE id=? AND active=1",(item.product_id,)).fetchone()
            if not p: raise HTTPException(404,f"Product {item.product_id} not found")
            amount=round(p["price"]*item.quantity,2)
            rate=p["gst_rate"] if b["tax_mode"]=="GST" else 0
            tax=round(amount*rate/100,2)
            subtotal+=amount; tax_total+=tax
            lines.append({"product_id":p["id"],"sku":p["sku"],"name":p["name"],"unit":p["unit"],"quantity":item.quantity,"price":p["price"],"gst_rate":rate,"amount":amount,"tax":tax})
        total=round(subtotal+tax_total,2)
        number=f"INV-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:5].upper()}"
        cur=c.execute("INSERT INTO invoices(invoice_no,date,customer_name,customer_phone,customer_gstin,subtotal,tax_total,grand_total,tax_mode,items_json) VALUES(?,?,?,?,?,?,?,?,?,?)",
          (number,datetime.now().isoformat(timespec="seconds"),x.customer_name,x.customer_phone,x.customer_gstin,round(subtotal,2),round(tax_total,2),total,b["tax_mode"],json.dumps(lines)))
        return dict(c.execute("SELECT * FROM invoices WHERE id=?",(cur.lastrowid,)).fetchone())

@app.get("/api/invoices")
def invoices():
    with db() as c:
        return [{**dict(r),"items":json.loads(r["items_json"])} for r in c.execute("SELECT * FROM invoices ORDER BY id DESC")]
