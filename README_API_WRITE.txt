# API Patch — Crear y Actualizar contactos (Docker Ready)

## Qué incluye
- Endpoints: GET /health, GET /estados, GET /contactos, **POST /contactos**, **PUT /contactos/{email}**
- Validación de `state` (2 letras) y `EmailStr` (requiere `email-validator`)
- Dockerfile y requirements listos

## Integración en tu proyecto
1) Copia la carpeta **api/** de este ZIP sobre tu proyecto (sustituye la carpeta api existente).
2) Reconstruye y levanta solo la API:
   ```powershell
   docker compose build api
   docker compose up -d
   docker compose logs api --tail=100
   ```
   Debes ver Uvicorn en `0.0.0.0:8000`.

## Pruebas rápidas (PowerShell usa curl.exe)
```powershell
curl.exe http://localhost:8000/health

# Crear
curl.exe -X POST http://localhost:8000/contactos ^
  -H "Content-Type: application/json" ^
  -d "{"first_name":"Ada","last_name":"Lovelace","email":"ada@example.com","company_name":"Analytical Engines","department":"R&D","address":"Somerset House","city":"London","state":"LD","zip":"WC2R","phone1":"+44-20-1234-5678","phone2":"+44-20-8765-4321"}"

# Actualizar
curl.exe -X PUT http://localhost:8000/contactos/ada@example.com ^
  -H "Content-Type: application/json" ^
  -d "{"first_name":"Ada","last_name":"Byron","email":"ada@example.com","company_name":"Analytical Engines","department":"Research","address":"Somerset House, New Wing","city":"London","state":"LD","zip":"WC2R","phone1":"+44-20-5555-1111","phone2":"+44-20-5555-2222"}"
```

## Notas
- `POST /contactos` devuelve 409 si el email ya existe.
- `PUT /contactos/{email}` actualiza por email; si no existe devuelve 404.
- Internamente hace upsert de empresa/departamento/estado/ciudad y actualiza dirección y teléfonos.
