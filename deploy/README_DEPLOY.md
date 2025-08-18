# Despliegue (CD) con GitHub Actions + GHCR

## Requisitos en el servidor
- Docker + Docker Compose plugin
- Abrir puerto 8000 si quieres acceso público a la API
- Directorio de despliegue (ej. /opt/contactos)

## Secretos en GitHub
Configura en Settings → Secrets and variables → Actions:

- `DEPLOY_HOST`  → IP o hostname del servidor
- `DEPLOY_USER`  → usuario SSH (con permisos docker)
- `DEPLOY_SSH_KEY` → clave privada SSH (formato PEM)
- (opcional) `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` si quieres sobrescribir

Permisos del repo:
- Packages: Read/Write (para GHCR)

## Flujo
1. En cada push/PR: **CI** construye la imagen, levanta db+api con compose y corre tests.
2. En `main` exitoso: **CD** construye/pushea imagen a GHCR y despliega vía SSH:
   - Copia `deploy/docker-compose.prod.yml` al servidor
   - Escribe `.env` con `API_IMAGE` apuntando a `ghcr.io/<owner>/contactos-api:<sha>`
   - Levanta `db` y `api` (y opcionalmente `db_bootstrap` si existe)
   - Verifica `/health`

## Rollback
Cambia `API_IMAGE` en `.env` a un tag anterior y ejecuta:
```
docker compose -f docker-compose.prod.yml up -d api
```
