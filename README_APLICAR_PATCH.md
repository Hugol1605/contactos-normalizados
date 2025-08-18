# Patch: Validación estricta de `state` + ejecución en Docker

Este patch agrega el archivo `db/init/02_validate_state.sql` que valida que `public.contactos.state` tenga
**longitud de 2** y contenga **solo letras**. Además, incluye un snippet de `docker-compose` para correr
01→02→02-validate→03 sin borrar el volumen.

## Cómo aplicarlo (Opción A: como la primera vez)
1) Copia `db/init/02_validate_state.sql` dentro de tu proyecto, en la misma carpeta donde están 01/02/03.
2) Asegúrate de que los nombres de archivo sean:
   - 01_init.sql
   - 02_seed_contactos.sh
   - 02_validate_state.sql   ← (este patch)
   - 03_modelo_normalizado_contactos.sql
   - contacts.csv
3) Inicializa en limpio para que el entrypoint ejecute todo 01→02→validate→03:
   ```powershell
   docker compose down -v
   docker compose up -d --build
   docker compose logs db -f
   ```

## Cómo aplicarlo (Opción B: sin borrar volumen, usando un job one-shot)
1) Copia `docker-compose.db_bootstrap.snippet.yml` y pega ese servicio en tu `docker-compose.yml`.
2) Ejecuta el job:
   ```powershell
   docker compose --profile ops up -d db_bootstrap
   docker compose logs db_bootstrap --tail=200
   ```

## Verificación
```powershell
docker compose exec db bash -lc 'PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT COUNT(*) FROM public.contactos;"'
docker compose exec db bash -lc 'PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" --pset=pager=off -c "SELECT * FROM public.v_contactos_flat LIMIT 5;"'
```

## (Opcional) Validación también desde la API
Consulta `api/STATE_VALIDATION_NOTES.txt` para aplicar la misma regla en tus endpoints de crear/actualizar.

Listo: validación estricta + ejecución en Docker, acoplable a tu proyecto que “ya funciona”.
