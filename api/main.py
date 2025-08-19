import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr, constr
import psycopg2
from psycopg2.extras import RealDictCursor

APP_DB_URL = os.getenv("APP_DB_URL", "postgresql://app:app_password@db:5432/challenge")

def get_conn():
    return psycopg2.connect(APP_DB_URL)

app = FastAPI(title="Contactos API", version="1.0.0")

class EmpresaIn(BaseModel):
    nombre: constr(strip_whitespace=True, min_length=1)
class EmpresaOut(EmpresaIn):
    empresa_id: int

class DepartamentoIn(BaseModel):
    nombre: constr(strip_whitespace=True, min_length=1)
class DepartamentoOut(DepartamentoIn):
    departamento_id: int

class EstadoIn(BaseModel):
    codigo: constr(strip_whitespace=True, min_length=2, max_length=2, pattern=r'^[A-Za-z]{2}$')
    nombre: constr(strip_whitespace=True, min_length=1)
class EstadoOut(EstadoIn):
    estado_id: int

class CiudadIn(BaseModel):
    nombre: constr(strip_whitespace=True, min_length=1)
    estado_codigo: constr(strip_whitespace=True, min_length=2, max_length=2, pattern=r'^[A-Za-z]{2}$')
class CiudadOut(BaseModel):
    ciudad_id: int
    nombre: str
    estado_codigo: str

class ContactIn(BaseModel):
    first_name: constr(strip_whitespace=True, min_length=1)
    last_name: constr(strip_whitespace=True, min_length=1)
    email: EmailStr
    empresa: Optional[constr(strip_whitespace=True, min_length=1)] = None
    departamento: Optional[constr(strip_whitespace=True, min_length=1)] = None
class ContactOut(BaseModel):
    contacto_id: int
    first_name: str
    last_name: str
    email: EmailStr
    empresa: Optional[str] = None
    departamento: Optional[str] = None

class DireccionIn(BaseModel):
    email: EmailStr
    address: Optional[str] = None
    zip: Optional[str] = None
    ciudad: Optional[str] = None
    estado: Optional[constr(strip_whitespace=True, min_length=2, max_length=2, pattern=r'^[A-Za-z]{2}$')] = None

class TelefonoIn(BaseModel):
    email: EmailStr
    tipo: constr(strip_whitespace=True, min_length=1)
    numero: constr(strip_whitespace=True, min_length=5)

@app.get("/health")
def health():
    return {"status": "ok"}

def fetchone(q, p=None):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, p or ())
            row = cur.fetchone()
            return dict(row) if row else None

def fetchall(q, p=None):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, p or ())
            rows = cur.fetchall()
            return [dict(r) for r in rows]

def execute(q, p=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(q, p or ())

def upsert_empresa(nombre: Optional[str]) -> Optional[int]:
    if not nombre:
        return None
    row = fetchone("""
        INSERT INTO public.empresa(nombre) VALUES (%s)
        ON CONFLICT (nombre) DO UPDATE SET nombre = EXCLUDED.nombre
        RETURNING empresa_id
    """, (nombre,))
    return row["empresa_id"] if row else None

def upsert_departamento(nombre: Optional[str]) -> Optional[int]:
    if not nombre:
        return None
    row = fetchone("""
        INSERT INTO public.departamento(nombre) VALUES (%s)
        ON CONFLICT (nombre) DO UPDATE SET nombre = EXCLUDED.nombre
        RETURNING departamento_id
    """, (nombre,))
    return row["departamento_id"] if row else None

def get_estado_id(codigo: str) -> int:
    row = fetchone("SELECT estado_id FROM public.estado WHERE UPPER(codigo)=UPPER(%s)", (codigo,))
    if not row:
        raise HTTPException(status_code=400, detail=f"Estado codigo '{codigo}' no existe")
    return row["estado_id"]

def upsert_ciudad(nombre: str, estado_codigo: str) -> int:
    estado_id = get_estado_id(estado_codigo)
    row = fetchone("""
        INSERT INTO public.ciudad(nombre, estado_id) VALUES (%s, %s)
        ON CONFLICT (nombre, estado_id) DO UPDATE SET nombre = EXCLUDED.nombre
        RETURNING ciudad_id
    """, (nombre, estado_id))
    return row["ciudad_id"]

@app.get("/contactos", response_model=List[ContactOut])
def list_contactos(limit: int = 20, offset: int = 0):
    rows = fetchall("""
        SELECT ct.contacto_id, ct.first_name, ct.last_name, ct.email,
               em.nombre AS empresa, dp.nombre AS departamento
        FROM public.contacto ct
        LEFT JOIN public.empresa em ON em.empresa_id = ct.empresa_id
        LEFT JOIN public.departamento dp ON dp.departamento_id = ct.departamento_id
        ORDER BY ct.contacto_id
        LIMIT %s OFFSET %s
    """, (limit, offset))
    return rows

@app.get("/contactos/{email}", response_model=ContactOut)
def get_contacto(email: EmailStr):
    row = fetchone("""
        SELECT ct.contacto_id, ct.first_name, ct.last_name, ct.email,
               em.nombre AS empresa, dp.nombre AS departamento
        FROM public.contacto ct
        LEFT JOIN public.empresa em ON em.empresa_id = ct.empresa_id
        LEFT JOIN public.departamento dp ON dp.departamento_id = ct.departamento_id
        WHERE ct.email = %s
    """, (str(email),))
    if not row:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return row

@app.get("/estados", response_model=List[EstadoOut])
def list_estados():
    return fetchall("SELECT estado_id, codigo, nombre FROM public.estado ORDER BY codigo" )

@app.get("/ciudades", response_model=List[CiudadOut])
def list_ciudades(estado: Optional[constr(min_length=2, max_length=2, pattern=r'^[A-Za-z]{2}$')] = None):
    if estado:
        return fetchall("""
            SELECT ci.ciudad_id, ci.nombre, es.codigo AS estado_codigo
            FROM public.ciudad ci
            JOIN public.estado es ON es.estado_id = ci.estado_id
            WHERE UPPER(es.codigo) = UPPER(%s)
            ORDER BY ci.nombre
        """, (estado,))
    return fetchall("""
        SELECT ci.ciudad_id, ci.nombre, es.codigo AS estado_codigo
        FROM public.ciudad ci
        JOIN public.estado es ON es.estado_id = ci.estado_id
        ORDER BY es.codigo, ci.nombre
    """ )

@app.post("/estados", response_model=EstadoOut, status_code=201)
def create_estado(body: EstadoIn):
    return fetchone("""
        INSERT INTO public.estado(codigo, nombre) VALUES (UPPER(%s), %s)
        ON CONFLICT (codigo) DO UPDATE SET nombre = EXCLUDED.nombre
        RETURNING estado_id, codigo, nombre
    """, (body.codigo, body.nombre))

@app.post("/ciudades", response_model=CiudadOut, status_code=201)
def create_ciudad(body: CiudadIn):
    ciudad_id = upsert_ciudad(body.nombre, body.estado_codigo)
    return fetchone("""
        SELECT ci.ciudad_id, ci.nombre, es.codigo AS estado_codigo
        FROM public.ciudad ci
        JOIN public.estado es ON es.estado_id = ci.estado_id
        WHERE ci.ciudad_id = %s
    """, (ciudad_id,))

@app.post("/empresas", response_model=EmpresaOut, status_code=201)
def create_empresa(body: EmpresaIn):
    return fetchone("""
        INSERT INTO public.empresa(nombre) VALUES (%s)
        ON CONFLICT (nombre) DO UPDATE SET nombre = EXCLUDED.nombre
        RETURNING empresa_id, nombre
    """, (body.nombre,))

@app.post("/departamentos", response_model=DepartamentoOut, status_code=201)
def create_departamento(body: DepartamentoIn):
    return fetchone("""
        INSERT INTO public.departamento(nombre) VALUES (%s)
        ON CONFLICT (nombre) DO UPDATE SET nombre = EXCLUDED.nombre
        RETURNING departamento_id, nombre
    """, (body.nombre,))

@app.post("/contactos", response_model=ContactOut, status_code=201)
def create_contacto(body: ContactIn):
    empresa_id = upsert_empresa(body.empresa) if body.empresa else None
    departamento_id = upsert_departamento(body.departamento) if body.departamento else None
    return fetchone("""
        INSERT INTO public.contacto(first_name, last_name, email, empresa_id, departamento_id)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (email) DO UPDATE SET
          first_name = EXCLUDED.first_name,
          last_name  = EXCLUDED.last_name,
          empresa_id = EXCLUDED.empresa_id,
          departamento_id = EXCLUDED.departamento_id
        RETURNING contacto_id, first_name, last_name, email,
          (SELECT nombre FROM public.empresa WHERE empresa_id = public.contacto.empresa_id) AS empresa,
          (SELECT nombre FROM public.departamento WHERE departamento_id = public.contacto.departamento_id) AS departamento
    """, (body.first_name, body.last_name, str(body.email), empresa_id, departamento_id))

@app.put("/contactos/{email}", response_model=ContactOut)
def update_contacto(email: EmailStr, body: ContactIn):
    if str(email) != str(body.email):
        raise HTTPException(status_code=400, detail="Email del path y del body deben coincidir")
    return create_contacto(body)

@app.post("/direcciones", status_code=201)
def upsert_direccion(body: DireccionIn):
    ct = fetchone("SELECT contacto_id FROM public.contacto WHERE email = %s", (str(body.email),))
    if not ct:
        raise HTTPException(status_code=404, detail="Contacto no existe para esa dirección")
    ciudad_id = None
    if body.ciudad and body.estado:
        ciudad_id = upsert_ciudad(body.ciudad, body.estado)
    execute("""
        INSERT INTO public.direccion(contacto_id, ciudad_id, address, zip)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (contacto_id) DO UPDATE
        SET ciudad_id = EXCLUDED.ciudad_id,
            address   = EXCLUDED.address,
            zip       = EXCLUDED.zip
    """, (ct["contacto_id"], ciudad_id, body.address, body.zip))
    return {"ok": True}

@app.get("/direcciones/{email}")
def get_direccion(email: EmailStr):
    row = fetchone("""
        SELECT di.address, di.zip, ci.nombre AS ciudad, es.codigo AS estado
        FROM public.contacto ct
        LEFT JOIN public.direccion di ON di.contacto_id = ct.contacto_id
        LEFT JOIN public.ciudad ci ON ci.ciudad_id = di.ciudad_id
        LEFT JOIN public.estado es ON es.estado_id = ci.estado_id
        WHERE ct.email = %s
    """, (str(email),))
    if not row:
        raise HTTPException(status_code=404, detail="Dirección no encontrada")
    return row

@app.post("/telefonos", status_code=201)
def upsert_telefono(body: TelefonoIn):
    ct = fetchone("SELECT contacto_id FROM public.contacto WHERE email = %s", (str(body.email),))
    if not ct:
        raise HTTPException(status_code=404, detail="Contacto no existe para ese teléfono")
    execute("""
        INSERT INTO public.telefono(contacto_id, tipo, numero)
        VALUES (%s, %s, %s)
        ON CONFLICT (contacto_id, tipo) DO UPDATE SET numero = EXCLUDED.numero
    """, (ct["contacto_id"], body.tipo, body.numero))
    return {"ok": True}

@app.get("/telefonos/{email}")
def list_telefonos(email: EmailStr):
    return fetchall("""
        SELECT t.tipo, t.numero
        FROM public.telefono t
        JOIN public.contacto ct ON ct.contacto_id = t.contacto_id
        WHERE ct.email = %s
        ORDER BY t.tipo
    """, (str(email),))
