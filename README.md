# Ianbal: un agente, un prompt, historia real en Git

Repositorio privado de clase. Contiene la configuración completa de un Genie Space y su prompt original: [`agente/instrucciones.md`](agente/instrucciones.md). Los commits posteriores modificarán ese mismo archivo. **No hay base oculta ni selector `active.md`.** Las tablas, ejemplos SQL y 20 preguntas de benchmark están en [`agente/space.json`](agente/space.json).

Secuencia: commit V0 → deploy → benchmark → revisar → commit V1 → deploy → benchmark → revisar → commit V2 → deploy → benchmark → notebook final. Se crea un único Genie de práctica, distinto del original, y se actualiza in-place con ETag y verificación del export. Git conserva las versiones; etiquetas y resultados se registran después de cada paso real.

## Ejecutar

**Primera vez:** sigue [la guía desde Terminal hasta Jobs y MLflow](docs/PRIMERA-EJECUCION.md), con instalación, acceso, carpeta, comandos, resultados esperados y recuperación. Para consultar la serie existente sin repetirla: `python evaluation/status.py V0`.

1. Configura un perfil Databricks autorizado y un entorno local: crea `.local/` y copia `environments/classroom.example.json` a `.local/classroom.json`; completa warehouse/perfil y un `workspace_root` exclusivo para la nueva serie. Usa otra copia local para otra práctica; no copies los recibos `.local` de la serie anterior.
2. `python deploy/genie_space.py create --label V0` crea el Space y guarda su ID local. Requiere checkout limpio.
3. `python evaluation/submit.py V0` ejecuta las 20 preguntas como Job Python serverless. Congela gold SQL una vez y usa el mismo juez/rúbrica para las versiones siguientes.
4. Revisa los resultados; modifica `agente/instrucciones.md` y haz commit. `python deploy/genie_space.py plan --out .local/plan.json`, revisa diff y `python deploy/genie_space.py apply --label V1`. Después `python evaluation/submit.py V1`.
5. Repite con V2. Solo al terminar se ejecuta el notebook final de comparación, sin inferencias ni despliegues.

Para regresar a un commit: checkout de ese commit → plan → apply. No se revierten datos ni conversaciones. El nuevo deploy se identifica por su commit y hash; un tag por sí solo no cambia Databricks.

## Evaluación y límites

Las preguntas vienen del benchmark nativo incluido en el export docente original. Los SQL de referencia se ejecutan independientemente sobre el warehouse y sus resultados se congelan como gold. Cada versión verifica que esas referencias siguen iguales. El juez es `databricks-meta-llama-3-3-70b-instruct`; su rúbrica vive en `evaluation/benchmark.py`. La evaluación usa Conversation API + juez, no la nota de la UI nativa.

No se presupone mejora: se reportan aciertos, errores técnicos, casos corregidos y regresiones. Son 20 preguntas conocidas, no un holdout; revisar referencias discutibles (en particular operaciones nominales con distintas monedas) y resultados humanos antes de decisiones de negocio. Las respuestas/gold con filas y trazas permanecen en `.local/` y el workspace autorizado; este repo privado contiene configuración y resúmenes de evidencia.

Tests: `python -m unittest discover -s tests -v`. Las dependencias del Job remoto se fijan en `evaluation/submit.py`. Para CLI local basta `databricks-sdk==0.140.0`. No se despliegan tablas, permisos o infraestructura del warehouse ni se habilita CD automático.


## Resultado de la secuencia real · 23 septiembre 2026

V0 **17/20**, V1 **18/20**, V2 **20/20** según el mismo juez automático: 20 casos juzgados y cero errores de ejecución por versión. Una única corrida completa por versión. La captura V0 requirió previamente corregir un fallo de arranque, documentado en `docs/INCIDENTES.md`.

- [Validación final ejecutada en Databricks](https://dbc-0410b264-20c7.cloud.databricks.com/editor/notebooks/1277065895608519?o=7474657121564806): SUCCESS, después del cierre de V2; verifica orden temporal, configuración desplegada, commits, hashes y resultados.
- [Evidencia final](evidence/final-validation.json) y [recibo del notebook](evidence/final-notebook.json).
- [Flujo explicado paso a paso](docs/FLUJO-REAL.md) y [guía de clase/versiones](docs/GUIA-CLASE.md).
- [Cambios V0 → V1](https://github.com/manuelarguelles/ianbal-genie-iac/compare/v0-evaluacion...v1) y [V1 → V2](https://github.com/manuelarguelles/ianbal-genie-iac/compare/v1...v2).

**Interpretación pendiente de revisión humana:** I06 pregunta por proveedores, pero la referencia devuelve ofertas: se verificaron cuatro proveedores y seis ofertas. El 20/20 de V2 es acuerdo con el benchmark, no demostración de corrección de negocio. I17 calcula un promedio nominal entre monedas. Estos problemas quedan registrados; no se cambió el examen durante la comparación. Una revisión del benchmark abrirá otro ciclo comparable.

La Review App contiene las 20 trazas de V0 preparadas para valoración humana; no se han inventado ni enviado anotaciones humanas. En el experimento, abrir **Labeling sessions → Ianbal-IaC-V0-20-casos-revision-Manuel**. Crear una valoración no vuelve a ejecutar Genie ni modifica la métrica automática original.
