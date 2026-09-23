# Databricks notebook source
# MAGIC %md
# MAGIC # Ianbal · validación final de una historia real en Git
# MAGIC Este notebook se ejecuta **después** de desplegar y evaluar V0, V1 y V2.
# MAGIC No crea Spaces, no cambia prompts y no vuelve a hacer preguntas al agente.
# MAGIC Reconstruye la cadena **commit → despliegue → benchmark → siguiente commit** desde evidencia guardada.

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1. Localizar las capturas
# MAGIC Las 20 preguntas provienen del benchmark del Space docente original, versionado en `agente/space.json`.
# MAGIC Después de desplegar V0 se ejecutó cada SQL de referencia una vez para congelar el gold.
# MAGIC V1 y V2 volvieron a comprobar esos resultados, sin sustituir la referencia. El juez y su rúbrica también permanecieron fijos.

# COMMAND ----------
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

dbutils.widgets.text('evidence_root', '/Workspace/Shared/ianbal-genie-iac/state')
root = Path(dbutils.widgets.get('evidence_root'))
sys.path.insert(0, '/Workspace/Shared/ianbal-genie-iac/final')
from validate import validate_series

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2. Verificar integridad y orden temporal
# MAGIC Esta celda exige 20 casos únicos por versión y el mismo examen, juez, rúbrica y Space.
# MAGIC Contrasta los hashes de los reportes y la configuración con los archivos extraídos de cada commit Git.
# MAGIC También comprueba que cada evaluación terminó antes del siguiente despliegue.
# MAGIC Un fallo detiene el notebook; una regresión de calidad se muestra como resultado, no se oculta.

# COMMAND ----------
result = validate_series(root)  # Lee y valida: no invoca inferencia ni APIs de despliegue.
print('Integridad verificada. Tres capturas secuenciales sobre el mismo Genie Space.')

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3. Qué commit se evaluó y qué resultado obtuvo
# MAGIC `correct` cuenta aprobaciones del juez; `judged` indica cuántas respuestas pudo juzgar.
# MAGIC Los errores técnicos se muestran separados. El run de MLflow conserva las trazas de cada pregunta.
# MAGIC Las fechas provienen del despliegue y de la captura, no de una reconstrucción retrospectiva.

# COMMAND ----------
import pandas as pd
columns = ['version','commit','correct','judged','attempted','execution_errors','judge_errors','deployment_at_utc','started_at_utc','completed_at_utc','run_id']
display(pd.DataFrame(result['versions'])[columns])

# COMMAND ----------
# MAGIC %md
# MAGIC ## 4. Mejoras y regresiones por caso
# MAGIC Una mejora neta puede esconder preguntas que antes pasaban y ahora fallan.
# MAGIC `corrected` muestra cambios de fallo a acierto; `regressed`, de acierto a fallo.
# MAGIC Si hay casos sin juicio, `unpaired` impide tratar el delta como una comparación completa.

# COMMAND ----------
display(pd.DataFrame(result['deltas']))
reports = {v:json.loads((root/'reports'/f'{v}.json').read_text()) for v in ('V0','V1','V2')}
rows = []
for index in range(1,21):
    case_id = f'I{index:02}'
    row = {'caso':case_id}
    for version, report in reports.items():
        case = next(c for c in report['cases'] if c['case_id'] == case_id)
        row[version] = '✓' if case.get('correctness') is True else '✗' if case.get('correctness') is False else 'Sin juicio'
    rows.append(row)
display(pd.DataFrame(rows))

# COMMAND ----------
# MAGIC %md
# MAGIC ## 5. Ver el cambio del prompt que produjo cada hipótesis
# MAGIC `instrucciones.md` es un único archivo completo. Git conserva sus versiones.
# MAGIC Abre **Files changed** para mostrar el delta; vuelve a la tabla de casos para revisar su efecto.
# MAGIC Las diferencias muestran una asociación observada en esta corrida; no demuestran causalidad ni generalización.

# COMMAND ----------
repo = 'https://github.com/manuelarguelles/ianbal-genie-iac'
for before, after in zip(result['versions'], result['versions'][1:]):
    print(f"{before['version']} → {after['version']}: {repo}/compare/{before['commit']}...{after['commit']}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 6. Conclusión y recibo del notebook
# MAGIC La validación de integridad y la mejora de calidad son resultados distintos.
# MAGIC Las 20 preguntas eran conocidas. Hay una corrida por versión y el juez LLM puede variar.
# MAGIC **Defecto detectado en I06:** la pregunta pide proveedores, pero la referencia cuenta ofertas.
# MAGIC La auditoría SQL encontró 6 ofertas y 4 proveedores distintos. Una nota alta puede incluir este falso criterio de aprobación.
# MAGIC Las referencias que agregan importes de distintas monedas también requieren interpretación y revisión humana.
# MAGIC El siguiente paso docente es revisar casos corregidos/regresados y, después, evaluar preguntas nuevas.

# COMMAND ----------
if result['reference_issues']:
    display(pd.DataFrame(result['reference_issues']))
for delta in result['deltas']:
    print(f"{delta['from']} → {delta['to']}: {delta['interpretation']}; delta neto {delta['net']:+d}/20")
result['notebook_executed_at_utc'] = datetime.now(timezone.utc).isoformat()
# Solo se escribe el resumen derivado: las capturas originales permanecen intactas.
(root/'final-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
dbutils.notebook.exit(json.dumps({'integrity_verified':True,'versions':[{'version':x['version'],'correct':x['correct'],'judged':x['judged']} for x in result['versions']],'deltas':result['deltas']}))
