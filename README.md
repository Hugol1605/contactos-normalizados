# Contactos

- Redes: `api_db` y `ingest_db` internas; `public_net` para exponer API al host.
- `centos_ingest` con perfil `ops` y plataforma `linux/amd64`.
- Esquema (estado=2 letras), API y flujo de ingesta.
- ER: ver **docs/er/ERD.md**.

---

# README — Pasos de despliegue (db → ingesta → api)

**Fecha:** 2025-08-19

Guía breve con los **comandos exactos** para levantar la base de datos, ejecutar una ingesta y luego arrancar la API.

> Si tu servicio `centos_ingest` está bajo `profiles: ["ops"]`, **usa** `--profile ops` en los comandos que lo invoquen.

## 1) Base de datos
```powershell
docker compose down -v
docker compose up -d --build db
docker compose ps
docker compose logs -f db
```

## 2) Ingesta (archivo específico, modo UPSERT)
### Opción A — En varias líneas (PowerShell con backticks)
```powershell
docker compose --profile ops run --rm `
  -e CSV_PATH=/data/clientes_1.csv `
  -e MODE=UPSERT `
  centos_ingest
```
### Opción B — En una sola línea
```powershell
docker compose --profile ops run --rm -e CSV_PATH=/data/clientes_1.csv -e MODE=UPSERT centos_ingest
```
> `CSV_PATH` es la ruta **dentro del contenedor** (si tu CSV está en `./data`, usa `/data/tu_archivo.csv`).  
> `MODE=UPSERT` inserta nuevos y **actualiza por `email`** los existentes. Alternativa: `MODE=REPLACE` borra y recarga.

## 3) API
```powershell
docker compose up -d --build api
```

## Verificaciones rápidas

**Base de datos (conteo):**
```powershell
docker compose exec db bash -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT COUNT(*) AS contactos FROM public.contacto;"'
```

**API (salud y lectura):**
```powershell
curl http://localhost:8000/health
curl "http://localhost:8000/contacts"
```

## 📚 API — Endpoints disponibles

> Base URL (local): `http://localhost:8000`

- **GET** `/ciudades`  _(func: list_ciudades)_
- **GET** `/contactos`  _(func: list_contactos)_
- **GET** `/contactos/{email}`  _(func: get_contacto)_
- **GET** `/direcciones/{email}`  _(func: get_direccion)_
- **GET** `/estados`  _(func: list_estados)_
- **GET** `/health`  _(func: health)_
- **GET** `/telefonos/{email}`  _(func: list_telefonos)_
- **POST** `/ciudades`  _(func: create_ciudad)_
- **POST** `/contactos`  _(func: create_contacto)_
- **POST** `/departamentos`  _(func: create_departamento)_
- **POST** `/direcciones`  _(func: upsert_direccion)_
- **POST** `/empresas`  _(func: create_empresa)_
- **POST** `/estados`  _(func: create_estado)_
- **POST** `/telefonos`  _(func: upsert_telefono)_
- **PUT** `/contactos/{email}`  _(func: update_contacto)_

**Ejemplos**
```bash
# Salud
curl http://localhost:8000/health

# Listar contactos
curl "http://localhost:8000/contactos"

# Filtrar por email
curl "http://localhost:8000/contactos?email=jbutt@gmail.com"

# Crear
curl -X POST "http://localhost:8000/contactos" -H "Content-Type: application/json" -d '{
  "nombre": "Ana",
  "email": "ana@example.com",
  "telefono": "555-0000",
  "estado": "JA"
}'

# Actualizar
curl -X PUT "http://localhost:8000/contactos/1" -H "Content-Type: application/json" -d '{
  "nombre": "Ana María",
  "email": "ana@example.com",
  "telefono": "555-0001",
  "estado": "JA"
}'
```

## Notas útiles
- Si tu CSV está fuera de `./data`, móntalo puntualmente:
  ```powershell
  docker compose --profile ops run --rm `
    -e CSV_PATH=/data/import.csv `
    --volume "C:\ruta\afuera\mi_archivo.csv:/data/import.csv:ro" `
    centos_ingest
  ```
- Si no usas perfiles para `centos_ingest`, omite `--profile ops`.
- Validación: `estado` **debe tener 2 letras** (la BD tiene un `CHECK`, la API valida por regex).
