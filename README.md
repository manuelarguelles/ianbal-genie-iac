# Ianbal: un agente, un prompt, historia real en Git

Repositorio privado de clase. Contiene la configuración completa de un Genie Space y su prompt original: [`agente/instrucciones.md`](agente/instrucciones.md). Los commits posteriores modificarán ese mismo archivo. **No hay base oculta ni selector `active.md`.** Las tablas, ejemplos SQL y 20 preguntas de benchmark están en [`agente/space.json`](agente/space.json).

Secuencia: commit V0 → deploy → benchmark → revisar → commit V1 → deploy → benchmark → revisar → commit V2 → deploy → benchmark → notebook final. Se crea un único Genie de práctica, distinto del original, y se actualiza in-place con ETag y verificación del export. Git conserva las versiones; etiquetas y resultados se registran después de cada paso real.

## Ejecutar

1. Configura un perfil Databricks autorizado y un entorno local: crea `.local/` y copia `environments/classroom.example.json` a `.local/classroom.json`; completa warehouse/perfil.
2. `python deploy/genie_space.py create --label V0` crea el Space y guarda su ID local. Requiere checkout limpio.
3. `python evaluation/submit.py V0` ejecuta las 20 preguntas como Job Python serverless. Congela gold SQL una vez y usa el mismo juez/rúbrica para las versiones siguientes.
4. Revisa los resultados; modifica `agente/instrucciones.md` y haz commit. `python deploy/genie_space.py plan --out .local/plan.json`, revisa diff y `python deploy/genie_space.py apply --label V1`. Después `python evaluation/submit.py V1`.
5. Repite con V2. Solo al terminar se ejecuta el notebook final de comparación, sin inferencias ni despliegues.

Para regresar a un commit: checkout de ese commit → plan → apply. No se revierten datos ni conversaciones. El nuevo deploy se identifica por su commit y hash; un tag por sí solo no cambia Databricks.

## Evaluación y límites

Las preguntas vienen del benchmark nativo incluido en el export docente original. Los SQL de referencia se ejecutan independientemente sobre el warehouse y sus resultados se congelan como gold. Cada versión verifica que esas referencias siguen iguales. El juez es `databricks-meta-llama-3-3-70b-instruct`; su rúbrica vive en `evaluation/benchmark.py`. La evaluación usa Conversation API + juez, no la nota de la UI nativa.

No se presupone mejora: se reportan aciertos, errores técnicos, casos corregidos y regresiones. Son 20 preguntas conocidas, no un holdout; revisar referencias discutibles (en particular operaciones nominales con distintas monedas) y resultados humanos antes de decisiones de negocio. Las respuestas/gold con filas y trazas permanecen en `.local/` y el workspace autorizado; este repo privado contiene configuración y resúmenes de evidencia.

Tests: `python -m unittest discover -s tests -v`. Las dependencias del Job remoto se fijan en `evaluation/submit.py`. Para CLI local basta `databricks-sdk==0.140.0`. No se despliegan tablas, permisos o infraestructura del warehouse ni se habilita CD automático.
