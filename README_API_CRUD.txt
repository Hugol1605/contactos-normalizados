# API Patch — CRUD Básico para tablas normalizadas (Docker)

Tablas cubiertas: **estado, ciudad, empresa, departamento, contacto, direccion, telefono**.

## Endpoints

### Estados
- GET `/estados`
- POST `/estados` — crea (valida `codigo` 2 letras)
- PUT `/estados/{codigo}` — actualiza `nombre` del estado

### Empresas
- GET `/empresas`
- POST `/empresas`
- PUT `/empresas/{empresa_id}`

### Departamentos
- GET `/departamentos`
- POST `/departamentos`
- PUT `/departamentos/{departamento_id}`

### Ciudades
- GET `/ciudades` — opcional `?estado=XX`
- POST `/ciudades` — crea con `nombre` + `estado` (upsert de estado)
- PUT `/ciudades/{ciudad_id}` — cambia `nombre` y/o estado

### Contactos
- GET `/contactos?limit=10`
- GET `/contactos/{email}`
- POST `/contactos` — crea todo (empresa/depto/estado/ciudad + direccion + telefonos)
- PUT `/contactos/{email}` — actualiza todo

### Direcciones (1:1 por contacto)
- GET `/direcciones/{email}`
- POST `/direcciones` — upsert por `email`

### Telefonos (2 tipos por contacto)
- GET `/telefonos/{email}`
- POST `/telefonos` — upsert por `(email, tipo)`

## Cómo aplicar
1) Reemplaza tu carpeta `api/` con la de este ZIP.
2) Reconstruye:
   ```powershell
   docker compose build api
   docker compose up -d
   docker compose logs api --tail=100
   ```

## Postman
Importa `Contactos_API_CRUD.postman_collection.json` y prueba.

## Notas
- Validación de `state`=2 letras en **API** y en **BD** (paso 02_validate_state.sql).
- Todas las operaciones usan **transacciones** y parámetros (psycopg2) para evitar inyección.
- Respuestas adecuadas: 201 (creado), 404 (no encontrado), 409 (conflicto).
