# Incidentes conservados

V0, job 614291396218419: falló antes de freeze/inferencias porque el runtime Spark Python ejecuta el archivo sin definir `__file__`. Databricks efectuó dos intentos internos, ambos fallaron en la importación. No produjo gold ni casos evaluados. Se conserva el commit inicial 413a8ce; el fix proporciona explícitamente `--code-root` y no modifica el prompt/configuración. El nuevo commit se registra en un deploy V0 sin cambios antes de reintentar.
