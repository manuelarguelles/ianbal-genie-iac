# Secuencia real de commits y evaluaciones

Goal: ejecutar y documentar V0 → V1 → V2 como historia real, validando al final en notebook.
Architecture: configuración completa + un prompt; CLI IaC con ETag; Jobs Python para benchmarks secuenciales; notebook final solo lector.
Spec: docs/DISENO.md

1. Tests de prompt completo, drift, commit y comparación; adaptar renderer/deploy. Preparar repo privado y commit V0.
2. Crear Space V0, congelar gold y ejecutar benchmark como tarea Python; preservar resultados, errores y evidencia.
3. Revisar V0, editar el mismo prompt con mejora sustentada, commit y tag V1, aplicar/evaluar.
4. Revisar V1, editar el mismo prompt, commit y tag V2, aplicar/evaluar.
5. Ejecutar notebook final al terminar las tres capturas. Verificar hashes, commits, 20 casos/juez por versión, casos corregidos/regresados y comparación numérica sin exigir mejora positiva.
6. Publicar resultados sanitizados, enlaces y memoria. No reescribir historial ni repetir ensayos para escoger mejor nota.
