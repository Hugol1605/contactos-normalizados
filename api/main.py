import os
from typing import Optional, Literal, List

from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, EmailStr, constr
import psycopg2
from psycopg2.extras import RealDictCursor

APP_DB_URL = os.getenv("APP_DB_URL", "postgresql://app:app_password@db:5432/challenge")
app = FastAPI(title="Contactos API", version="1.3.0")

def get_conn():
    return psycopg2.connect(APP_DB_URL)

# ------------------ Schemas ------------------

class EstadoIn(BaseModel):
    codigo: constr(min_length=2, max_length=2, pattern=r'^[A-Za-z]{2}$')
    nombre: Optional[str] = None

class EstadoOut(BaseModel):
    estado_id: int
    codigo: constr(min_length=2, max_length=2, pattern=r'^[A-Za-z]{2}$')
    nombre: Optional[str] = None

class EmpresaIn(BaseModel):
    nombre: constr(min_length=1)

class EmpresaOut(BaseModel):
    empresa_id: int
    nombre: str

class DeptoIn(BaseModel):
    nombre: constr(min_length=1)

class DeptoOut(BaseModel):
    departamento_id: int
    nombre: str

class CiudadIn(BaseModel):
    nombre: constr(min_length=1)
    estado: constr(min_length=2, max_length=2, pattern=r'^[A-Za-z]{2}$')

class CiudadOut(BaseModel):
    ciudad_id: int
    nombre: str
    estado: str

class DireccionIn(BaseModel):
    email: EmailStr
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[constr(min_length=2, max_length=2, pattern=r'^[A-Za-z]{2}$')] = None
    zip: Optional[str] = None

class DireccionOut(BaseModel):
    email: EmailStr
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None

class TelefonoIn(BaseModel):
    email: EmailStr
    tipo: Literal['principal','alterno']
    numero: constr(min_length=1)

class TelefonoOut(BaseModel):
    email: EmailStr
    tipo: Literal['principal','alterno']
    numero: str

class ContactIn(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    company_name: Optional[str] = None
    department: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[constr(min_length=2, max_length=2, pattern=r'^[A-Za-z]{2}$')] = None
    zip: Optional[str] = None
    phone1: Optional[str] = None
    phone2: Optional[str] = None

class ContactOut(BaseModel):
    first_name: str
    last_name: str
    company_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    phone1: Optional[str] = None
    phone2: Optional[str] = None
    email: EmailStr
    department: Optional[str] = None

# ------------------ Helpers ------------------

def upsert_empresa(conn, nombre: Optional[str]) -> Optional[int]:
    if not nombre:
        return None
    with conn.cursor() as cur:
        cur.execute("SELECT empresa_id FROM public.empresa WHERE nombre=%s", (nombre,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute("INSERT INTO public.empresa(nombre) VALUES(%s) RETURNING empresa_id", (nombre,))
        return cur.fetchone()[0]

def upsert_departamento(conn, nombre: Optional[str]) -> Optional[int]:
    if not nombre:
        return None
    with conn.cursor() as cur:
        cur.execute("SELECT departamento_id FROM public.departamento WHERE nombre=%s", (nombre,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute("INSERT INTO public.departamento(nombre) VALUES(%s) RETURNING departamento_id", (nombre,))
        return cur.fetchone()[0]

def upsert_estado(conn, codigo: Optional[str]) -> Optional[int]:
    if not codigo:
        return None
    code = codigo.upper()
    with conn.cursor() as cur:
        cur.execute("SELECT estado_id FROM public.estado WHERE codigo=%s", (code,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute("INSERT INTO public.estado(codigo) VALUES(%s) RETURNING estado_id", (code,))
        return cur.fetchone()[0]

def upsert_ciudad(conn, nombre: Optional[str], estado_id: Optional[int]) -> Optional[int]:
    if not nombre or not estado_id:
        return None
    with conn.cursor() as cur:
        cur.execute("SELECT ciudad_id FROM public.ciudad WHERE nombre=%s AND estado_id=%s", (nombre, estado_id))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute("INSERT INTO public.ciudad(nombre, estado_id) VALUES(%s, %s) RETURNING ciudad_id", (nombre, estado_id))
        return cur.fetchone()[0]

def row_to_out(conn, email: str) -> ContactOut:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM public.v_contactos_flat WHERE email=%s LIMIT 1", (email.lower(),))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Contacto no encontrado")
        return ContactOut(**row)

def get_estado_id_by_code(conn, code: str) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT estado_id FROM public.estado WHERE codigo=%s", (code.upper(),))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Estado no encontrado")
        return row[0]

# ------------------ Read Endpoints ------------------

@app.get("/health")
def health():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/estados", response_model=List[EstadoOut])
def estados():
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT estado_id, codigo, coalesce(nombre,'') as nombre FROM public.estado ORDER BY codigo")
                rows = cur.fetchall()
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/empresas", response_model=List[EmpresaOut])
def empresas():
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT empresa_id, nombre FROM public.empresa ORDER BY nombre")
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/departamentos", response_model=List[DeptoOut])
def departamentos():
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT departamento_id, nombre FROM public.departamento ORDER BY nombre")
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ciudades", response_model=List[CiudadOut])
def ciudades(estado: Optional[constr(min_length=2, max_length=2, pattern=r'^[A-Za-z]{2}$')] = Query(None)):
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if estado:
                    cur.execute("""
                      SELECT c.ciudad_id, c.nombre, e.codigo AS estado
                      FROM public.ciudad c
                      JOIN public.estado e ON e.estado_id = c.estado_id
                      WHERE e.codigo = %s
                      ORDER BY c.nombre
                    """, (estado.upper(),))
                else:
                    cur.execute("""
                      SELECT c.ciudad_id, c.nombre, e.codigo AS estado
                      FROM public.ciudad c
                      JOIN public.estado e ON e.estado_id = c.estado_id
                      ORDER BY e.codigo, c.nombre
                    """)
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/contactos", response_model=List[ContactOut])
def contactos(limit: int = 10):
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM public.v_contactos_flat LIMIT %s", (limit,))
                rows = cur.fetchall()
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/contactos/{email}", response_model=ContactOut)
def contacto_by_email(email: EmailStr):
    try:
        with get_conn() as conn:
            return row_to_out(conn, email.lower())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/direcciones/{email}", response_model=DireccionOut)
def direccion_by_email(email: EmailStr):
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT ct.email, dir.address, ci.nombre AS city, es.codigo AS state, dir.zip
                    FROM public.contacto ct
                    LEFT JOIN public.direccion dir ON dir.contacto_id = ct.contacto_id
                    LEFT JOIN public.ciudad ci ON ci.ciudad_id = dir.ciudad_id
                    LEFT JOIN public.estado es ON es.estado_id = ci.estado_id
                    WHERE ct.email = %s LIMIT 1
                """, (email.lower(),))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Contacto no encontrado")
                return row
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/telefonos/{email}", response_model=List[TelefonoOut])
def telefonos_by_email(email: EmailStr):
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT ct.email, t.tipo, t.numero
                    FROM public.contacto ct
                    LEFT JOIN public.telefono t ON t.contacto_id = ct.contacto_id
                    WHERE ct.email = %s
                    ORDER BY t.tipo
                """, (email.lower(),))
                rows = cur.fetchall()
                if not rows:
                    # devolver 404 si el contacto no existe del todo
                    with conn.cursor() as c2:
                        c2.execute("SELECT 1 FROM public.contacto WHERE email=%s", (email.lower(),))
                        if not c2.fetchone():
                            raise HTTPException(status_code=404, detail="Contacto no encontrado")
                return [r for r in rows if r.get('tipo') is not None]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------------ Write Endpoints ------------------

@app.post("/estados", response_model=EstadoOut, status_code=201)
def create_estado(payload: EstadoIn):
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "INSERT INTO public.estado(codigo, nombre) VALUES(%s, %s) RETURNING estado_id, codigo, nombre",
                    (payload.codigo.upper(), payload.nombre)
                )
                return cur.fetchone()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/estados/{codigo}", response_model=EstadoOut)
def update_estado(codigo: constr(min_length=2, max_length=2, pattern=r'^[A-Za-z]{2}$'), payload: EstadoIn = None):
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT estado_id FROM public.estado WHERE codigo=%s", (codigo.upper(),))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Estado no encontrado")
                estado_id = row['estado_id']
                cur.execute("UPDATE public.estado SET nombre=%s WHERE estado_id=%s RETURNING estado_id, codigo, nombre",
                            (payload.nombre, estado_id))
                return cur.fetchone()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/empresas", response_model=EmpresaOut, status_code=201)
def create_empresa(payload: EmpresaIn):
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("INSERT INTO public.empresa(nombre) VALUES(%s) RETURNING empresa_id, nombre", (payload.nombre,))
                return cur.fetchone()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/empresas/{empresa_id}", response_model=EmpresaOut)
def update_empresa(empresa_id: int, payload: EmpresaIn):
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("UPDATE public.empresa SET nombre=%s WHERE empresa_id=%s RETURNING empresa_id, nombre",
                            (payload.nombre, empresa_id))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Empresa no encontrada")
                return row
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/departamentos", response_model=DeptoOut, status_code=201)
def create_departamento(payload: DeptoIn):
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("INSERT INTO public.departamento(nombre) VALUES(%s) RETURNING departamento_id, nombre", (payload.nombre,))
                return cur.fetchone()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/departamentos/{departamento_id}", response_model=DeptoOut)
def update_departamento(departamento_id: int, payload: DeptoIn):
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("UPDATE public.departamento SET nombre=%s WHERE departamento_id=%s RETURNING departamento_id, nombre",
                            (payload.nombre, departamento_id))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Departamento no encontrado")
                return row
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/ciudades", response_model=CiudadOut, status_code=201)
def create_ciudad(payload: CiudadIn):
    try:
        with get_conn() as conn:
            estado_id = upsert_estado(conn, payload.estado)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # unique (nombre, estado_id)
                cur.execute("""
                    INSERT INTO public.ciudad(nombre, estado_id)
                    VALUES(%s, %s)
                    ON CONFLICT (nombre, estado_id) DO UPDATE SET nombre=EXCLUDED.nombre
                    RETURNING ciudad_id, nombre, (SELECT codigo FROM public.estado WHERE estado_id=public.ciudad.estado_id) AS estado
                """, (payload.nombre, estado_id))
                return cur.fetchone()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/ciudades/{ciudad_id}", response_model=CiudadOut)
def update_ciudad(ciudad_id: int, payload: CiudadIn):
    try:
        with get_conn() as conn:
            estado_id = get_estado_id_by_code(conn, payload.estado)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    UPDATE public.ciudad SET nombre=%s, estado_id=%s
                    WHERE ciudad_id=%s
                    RETURNING ciudad_id, nombre, (SELECT codigo FROM public.estado WHERE estado_id=public.ciudad.estado_id) AS estado
                """, (payload.nombre, estado_id, ciudad_id))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Ciudad no encontrada")
                return row
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/contactos", response_model=ContactOut, status_code=201)
def create_contact(contact: ContactIn):
    email = contact.email.lower()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM public.contacto WHERE email=%s", (email,))
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="Ya existe un contacto con ese email")
        try:
            conn.autocommit = False
            empresa_id = upsert_empresa(conn, contact.company_name)
            departamento_id = upsert_departamento(conn, contact.department)
            estado_id = upsert_estado(conn, contact.state)
            ciudad_id = upsert_ciudad(conn, contact.city, estado_id)

            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO public.contacto (first_name, last_name, email, empresa_id, departamento_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING contacto_id
                    """,
                    (contact.first_name, contact.last_name, email, empresa_id, departamento_id)
                )
                contacto_id = cur.fetchone()[0]

                cur.execute(
                    """
                    INSERT INTO public.direccion (contacto_id, ciudad_id, address, zip)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (contacto_id) DO UPDATE
                      SET ciudad_id=EXCLUDED.ciudad_id, address=EXCLUDED.address, zip=EXCLUDED.zip
                    """,
                    (contacto_id, ciudad_id, contact.address, contact.zip)
                )

                if contact.phone1:
                    cur.execute(
                        """
                        INSERT INTO public.telefono (contacto_id, tipo, numero)
                        VALUES (%s, 'principal', %s)
                        ON CONFLICT (contacto_id, tipo) DO UPDATE SET numero=EXCLUDED.numero
                        """,
                        (contacto_id, contact.phone1)
                    )
                if contact.phone2:
                    cur.execute(
                        """
                        INSERT INTO public.telefono (contacto_id, tipo, numero)
                        VALUES (%s, 'alterno', %s)
                        ON CONFLICT (contacto_id, tipo) DO UPDATE SET numero=EXCLUDED.numero
                        """,
                        (contacto_id, contact.phone2)
                    )

            conn.commit()
            return row_to_out(conn, email)
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@app.put("/contactos/{email}", response_model=ContactOut)
def update_contact(
    email: EmailStr = Path(..., description="Email del contacto a actualizar"),
    patch: ContactIn = None
):
    target_email = email.lower()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT contacto_id FROM public.contacto WHERE email=%s", (target_email,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Contacto no encontrado")
            contacto_id = row[0]

        try:
            conn.autocommit = False
            empresa_id = upsert_empresa(conn, patch.company_name)
            departamento_id = upsert_departamento(conn, patch.department)
            estado_id = upsert_estado(conn, patch.state)
            ciudad_id = upsert_ciudad(conn, patch.city, estado_id)

            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE public.contacto
                       SET first_name = %s,
                           last_name  = %s,
                           empresa_id = %s,
                           departamento_id = %s,
                           actualizado_en = now()
                     WHERE contacto_id = %s
                    """,
                    (patch.first_name, patch.last_name, empresa_id, departamento_id, contacto_id)
                )

                cur.execute(
                    """
                    INSERT INTO public.direccion (contacto_id, ciudad_id, address, zip)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (contacto_id) DO UPDATE
                      SET ciudad_id=EXCLUDED.ciudad_id, address=EXCLUDED.address, zip=EXCLUDED.zip
                    """,
                    (contacto_id, ciudad_id, patch.address, patch.zip)
                )

                cur.execute("DELETE FROM public.telefono WHERE contacto_id=%s AND tipo IN ('principal','alterno')", (contacto_id,))
                if patch.phone1:
                    cur.execute("INSERT INTO public.telefono (contacto_id, tipo, numero) VALUES (%s, 'principal', %s)", (contacto_id, patch.phone1))
                if patch.phone2:
                    cur.execute("INSERT INTO public.telefono (contacto_id, tipo, numero) VALUES (%s, 'alterno', %s)", (contacto_id, patch.phone2))

            conn.commit()
            return row_to_out(conn, target_email)
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@app.post("/direcciones", response_model=DireccionOut, status_code=201)
def set_direccion(payload: DireccionIn):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT contacto_id FROM public.contacto WHERE email=%s", (payload.email.lower(),))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Contacto no encontrado")
                contacto_id = row[0]

            estado_id = upsert_estado(conn, payload.state)
            ciudad_id = upsert_ciudad(conn, payload.city, estado_id)

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO public.direccion (contacto_id, ciudad_id, address, zip)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (contacto_id) DO UPDATE
                      SET ciudad_id=EXCLUDED.ciudad_id, address=EXCLUDED.address, zip=EXCLUDED.zip
                """, (contacto_id, ciudad_id, payload.address, payload.zip))

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT ct.email, dir.address, ci.nombre AS city, es.codigo AS state, dir.zip
                    FROM public.contacto ct
                    JOIN public.direccion dir ON dir.contacto_id = ct.contacto_id
                    LEFT JOIN public.ciudad ci ON ci.ciudad_id = dir.ciudad_id
                    LEFT JOIN public.estado es ON es.estado_id = ci.estado_id
                    WHERE ct.email = %s
                """, (payload.email.lower(),))
                return cur.fetchone()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/telefonos", response_model=TelefonoOut, status_code=201)
def set_telefono(payload: TelefonoIn):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT contacto_id FROM public.contacto WHERE email=%s", (payload.email.lower(),))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Contacto no encontrado")
                contacto_id = row[0]

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO public.telefono (contacto_id, tipo, numero)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (contacto_id, tipo) DO UPDATE SET numero=EXCLUDED.numero
                """, (contacto_id, payload.tipo, payload.numero))

            return TelefonoOut(email=payload.email.lower(), tipo=payload.tipo, numero=payload.numero)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
