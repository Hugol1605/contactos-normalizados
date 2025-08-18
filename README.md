# Contactos — Entregable completo (Docker + SQL + E‑R)

Este paquete incluye:
- **Docker Compose** con `db` (Postgres), `api` (FastAPI) y jobs opcionales `db_seed` / `db_migrate`.
- **SQL** en tres fases: `01` (estructura), `02` (seed desde CSV con dedupe) y `03` (migración al modelo normalizado + vista).
- **E‑R** en Mermaid (`docs/er_diagram.md`) y **schema.sql** para crear toda la estructura.
- Un **CSV** de ejemplo en `db/init/contacts.csv` (reemplázalo por el tuyo si quieres).

## Estructura de carpetas
```
.
├─ docker-compose.yml
├─ .env
├─ api/
│  ├─ Dockerfile
│  ├─ requirements.txt
│  └─ main.py
├─ db/
│  └─ init/
│     ├─ 01_init.sql
│     ├─ 02_seed_contactos.sql
│     ├─ 03_modelo_normalizado_contactos.sql
│     └─ contacts.csv
└─ docs/
   ├─ er_diagram.md
   └─ schema.sql
```

## Uso rápido (Opción 1: todo automático 01→02→03)
> Ejecuta en una carpeta limpia para que el entrypoint corra los scripts.
```powershell
docker compose down -v
docker compose up -d --build
docker compose logs db -f
```
Verás en los logs de `db`:
- running `01_init.sql`
- running `02_seed_contactos.sql`
- running `03_modelo_normalizado_contactos.sql`

### Verificación
```powershell
docker compose exec db psql -U app -d challenge -tAc "SELECT 'contactos='||COUNT(*) FROM public.contactos;"
docker compose exec db psql -U app -d challenge --pset=pager=off -c "SELECT * FROM public.v_contactos_flat LIMIT 5;"
```

## Uso (Opción 2: sin borrar la base)
Sembrar de nuevo:
```powershell
docker compose --profile ops up -d db_seed
docker compose logs db_seed -f
```
Migrar (modelo normalizado):
```powershell
docker compose --profile ops up -d db_migrate
docker compose logs db_migrate -f
```

## API mínima (FastAPI)
- `GET http://localhost:8000/health`
- `GET http://localhost:8000/estados`
- `GET http://localhost:8000/contactos?limit=10`

## Notas
- La línea `\copy` en `02_seed_contactos.sql` está en **una sola línea** (requisito de `psql`).
- El CSV se busca en `/docker-entrypoint-initdb.d/contacts.csv` (por eso está dentro de `db/init/`). 
- La tabla `contactos_seed` es **UNLOGGED** y puede quedar vacía tras reinicios; el objetivo es `public.contactos`.
