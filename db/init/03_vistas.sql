CREATE OR REPLACE VIEW public.v_contactos_flat AS
SELECT
  ct.contacto_id,
  ct.first_name,
  ct.last_name,
  ct.email,
  em.nombre AS empresa,
  dp.nombre AS departamento,
  di.address,
  di.zip,
  ci.nombre AS ciudad,
  es.codigo AS estado
FROM public.contacto ct
LEFT JOIN public.empresa em ON em.empresa_id = ct.empresa_id
LEFT JOIN public.departamento dp ON dp.departamento_id = ct.departamento_id
LEFT JOIN public.direccion di ON di.contacto_id = ct.contacto_id
LEFT JOIN public.ciudad ci ON ci.ciudad_id = di.ciudad_id
LEFT JOIN public.estado es ON es.estado_id = ci.estado_id;
