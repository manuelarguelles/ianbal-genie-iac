# De V0 a una mejora evaluada

**Review App no lanza el benchmark.** La evaluación automática produce respuestas y métricas; Review App recoge después el criterio humano sobre esas respuestas. El notebook final consolida evidencia existente.

| Etapa | Qué haces | Dónde en este laboratorio | Qué produce |
|---|---|---|---|
| Definir V0 | Tablas, ejemplos e instrucciones completas; commit | Git: `agente/` | Versión reproducible de configuración |
| Preparar examen | Preguntas + SQL de referencia; validar que representan la intención | `agente/space.json`, sección benchmarks | 20 casos conocidos |
| Desplegar | Render, plan, apply y export de comprobación | CLI IaC → Genie | Space con configuración ligada al commit |
| Congelar gold | Ejecutar SQL de referencia una vez | Job Python, antes de V0 | Resultado esperado de cada caso |
| Evaluar V0 | Preguntar al agente, capturar respuesta/SQL, juzgar | Job Python → MLflow | Run, trazas, juicios y métricas |
| Revisar | Examinar respuestas y referencias, registrar desacuerdo/corrección | Review App + guía de referencias | Feedback humano, separado de la nota del juez |
| Mejorar | Hipótesis basada en fallos, editar el mismo prompt, commit V1 | Git | Cambio explicable |
| Repetir examen | Desplegar V1, mismo gold/juez/rúbrica | Job Python → MLflow | Otro run comparable |
| Consolidar | Contrastar V0/V1/V2, integridad, correcciones/regresiones | Notebook final | Informe reproducible |

El benchmark es el examen, el runner es quien administra el examen, el juez asigna una valoración automática y el experto revisa esa valoración. Un run agrupa una ejecución; una traza conserva lo ocurrido con una pregunta. Una labeling session agrupa trazas para Review App.

## Recorrido con clics

1. **Para ver el agente:** abre el Genie nuevo y su configuración. Cambiar archivos en Git no cambia el agente hasta aplicar IaC.
2. **Para lanzar nuestro benchmark:** se usa `python evaluation/submit.py V0` (o V1/V2 después de su despliegue). Crea una tarea Python visible en Jobs & Pipelines. Review App no ejecuta este comando.
3. **Para ver métricas:** abre Experiments → el experimento enlazado en los resultados → el run de Ianbal-V0/V1/V2. Ahí están métricas y trazas. Las 20 trazas corresponden a las 20 preguntas; los números son juicios del modelo.
4. **Para revisar como humano:** abre la Review App preparada. Desde UI: Experiments → experimento → Labeling sessions → `Ianbal-IaC-V0-20-casos-revision-Manuel`. Lee cada pregunta/respuesta, contrasta el SQL/referencia de la guía, elige Aprobada/Requiere corrección/No evaluable, escribe evidencia y corrección y guarda. Reabre el caso y verifica tu valoración en Assessments.
5. **Para mejorar:** usa tus observaciones y los fallos del run para decidir qué cambiar. Primero commit, después deploy, después otro benchmark completo.

También existe el benchmark nativo de Genie, con otro mecanismo de evaluación. No hay que insertar ese mecanismo entre nuestro Job y Review App ni comparar sus notas como si fueran el mismo juez. Este laboratorio usa Conversation API + SQL de referencia independiente + juez fijo en MLflow.

## Un ejemplo real: el examen también puede equivocarse

I06 pregunta por proveedores, pero su SQL de referencia lee `item_n_offers`. La auditoría independiente halló 6 ofertas y 4 proveedores distintos. Una respuesta de 4 proveedores puede estar bien aunque el juez la rechace por no coincidir con 6.

En Review App registra el desacuerdo y la evidencia. El equipo debería corregir la referencia, versionar un nuevo benchmark y volver a evaluar las versiones que quiera comparar. Esta serie conserva el examen original y documenta el defecto: no cambia el gold a mitad de V0 → V1 → V2.

I17 requiere otra discusión: un promedio nominal entre monedas no representa un precio económicamente comparable. La respuesta debe explicitar esa limitación; mejorar una nota no basta para aprobar decisiones de compras.

La revisión humana del docente sigue pendiente hasta que él guarde sus valoraciones. La inspección técnica de SQL realizada durante esta demostración no se presenta como una sesión humana completada en Review App.

Fuentes oficiales: [Labeling sessions y UI](https://docs.databricks.com/aws/en/mlflow3/genai/human-feedback/concepts/labeling-sessions), [Review App sobre trazas existentes](https://docs.databricks.com/aws/en/mlflow3/genai/human-feedback/expert-feedback/label-existing-traces).
