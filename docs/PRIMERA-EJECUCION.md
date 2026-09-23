# Primera ejecución: de tu computadora a Databricks

Estos pasos se ejecutan en **Terminal de macOS o en Terminal → New Terminal de VS Code**, dentro de una copia local del repositorio. El navegador se usa para autenticarse, revisar Genie y abrir resultados. `deploy/genie_space.py` y `evaluation/submit.py` son archivos de este repositorio; Databricks no los trae preinstalados.

## 1. Elige revisar lo existente o iniciar otra serie

**Para Manuel, revisar la serie ya terminada:** abre Terminal (⌘ Espacio, escribe Terminal, Enter), escribe `cd /Users/macdenix/clawd/ianbal-genie-iac` y luego `python3 evaluation/status.py V0`. Repite con V1 o V2. Esto consulta; no vuelve a evaluar. Abre `job_url` y `mlflow_url` de la salida. V0 tiene20 casos y17 aprobados por el juez. No ejecutes otra vez create/submit sobre esa serie terminada.

**Para iniciar una serie nueva:** sigue el resto de esta guía en otra carpeta. Se necesita permiso al repositorio privado, al workspace, a Genie, al SQL warehouse y a las tablas de `agente/space.json`, a Jobs serverless y al endpoint del juez. El script no crea tablas, warehouse ni permisos. Un alumno sin acceso a Ianbal usa sus propias tablas/preguntas y adapta la configuración antes del primer commit; la alternativa de clones del curso está documentada por separado y no es este flujo IaC.

## 2. Comprueba herramientas locales

En Terminal:

```bash
python3 --version
git --version
databricks --version
```

Cada comando debe imprimir una versión. Si falta Python, instala Python3 desde [python.org](https://www.python.org/downloads/). Si falta Git en macOS, `xcode-select --install` abre su instalador. Para Databricks CLI, con Homebrew disponible, usa `brew install databricks/tap/databricks`; otros sistemas tienen [instrucciones oficiales](https://docs.databricks.com/aws/en/dev-tools/cli/install). No uses el paquete antiguo `pip install databricks-cli`.

## 3. Descarga el código y entra a su carpeta

En Terminal, desde la carpeta donde guardarás tu trabajo:

```bash
git clone https://github.com/manuelarguelles/ianbal-genie-iac.git ianbal-practica
cd ianbal-practica
pwd
ls agente deploy evaluation
```

El resultado de `pwd` debe terminar en `ianbal-practica`. `ls` debe mostrar los archivos del agente y los scripts. Si GitHub responde repository not found, comprueba tu cuenta y permiso al repositorio privado; inicia sesión con tu cliente Git autorizado. No pongas tokens en el comando. Si esa carpeta ya existe, usa otro nombre para una serie nueva.

## 4. Activa un Python exclusivo para esta práctica

En la misma terminal/carpeta:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install databricks-sdk==0.140.0
python -c "from databricks.sdk import WorkspaceClient; print('SDK listo')"
```

Espera `SDK listo`. La CLI local solo necesita el SDK. El Job instala MLflow y el resto de dependencias en Databricks. Al abrir otra terminal, vuelve a `cd` a la carpeta y activa `.venv` antes de usar `python`.

## 5. Conecta tu terminal con el workspace

En la misma terminal, para el workspace de la clase:

```bash
databricks auth login --host https://dbc-0410b264-20c7.cloud.databricks.com --profile ianbal-practica
databricks current-user me --profile ianbal-practica
```

El primer comando abre el navegador para iniciar sesión; regresa después a Terminal. El segundo debe identificar tu usuario. Para otro workspace sustituye el host. Este perfil se usará en el JSON del paso siguiente; no es el nombre del Genie. [Autenticación oficial](https://docs.databricks.com/aws/en/dev-tools/cli/authentication).

## 6. Configura un Space y una carpeta remota nuevos

```bash
mkdir -p .local
cp environments/classroom.example.json .local/classroom.json
```

Abre `.local/classroom.json` en tu editor: VS Code → File → Open File. Completa `profile`, `warehouse_id`, `title`, `description`; deja `space_id` en `null` y añade `workspace_root`. Ejemplo de estructura (sustituye los valores explicados):

```json
{
  "profile": "ianbal-practica",
  "warehouse_id": "ID_DEL_WAREHOUSE_AUTORIZADO",
  "title": "Ianbal practica Manuel",
  "description": "Nueva serie de aprendizaje",
  "space_id": null,
  "workspace_root": "/Shared/ianbal-practica-manuel-20260923-01"
}
```

Obtén el ID del warehouse en Databricks → SQL Warehouses → tu warehouse → Connection details: el segmento final de HTTP Path identifica el warehouse. No pegues todo el HTTP Path en `warehouse_id`. Debes poder usar ese warehouse y consultar las tablas.

`workspace_root` es una carpeta **nueva y exclusiva** en Workspace para esta serie. Cambia nombre/fecha/sufijo si ya la usaste; no reutilices `/Shared/ianbal-genie-iac` de la serie histórica. El prefijo de configuración es `/Shared/`, no `/Workspace/Shared/`. No copies `.local` del instructor: contiene los IDs y recibos de su serie.

## 7. Prepara el contenido V0 y guárdalo en Git

`main` contiene las mejoras finales. Para comenzar con el prompt original conservando el lanzador actualizado:

```bash
git switch -c practica-manuel
git restore --source v0-evaluacion -- agente/instrucciones.md agente/space.json
```

Si usarás datos propios, adapta ahora tablas, preguntas y prompt en tu editor. Hazlo después de restore (que reemplaza los archivos) y antes de guardar el commit. Después vuelve a Terminal:

```bash
git diff --stat
git add agente/instrucciones.md agente/space.json
git commit -m "Practica: punto de partida V0"
git status --short
```

Lee el diff antes de confirmar. Si usarás datos propios, adapta tablas, preguntas y prompt **después de git restore y antes de git add/commit**: restore reemplaza esos archivos con V0. Incluye tus adaptaciones en el commit. La última salida debe estar vacía: es la comprobación de que lo desplegado corresponde al commit. Si Git solicita identidad, configura tu nombre/correo de autor en este repositorio antes de repetir el commit. `.local` y `.venv` están excluidos de Git.

## 8. Crea V0 desde la terminal

```bash
python deploy/genie_space.py create --label V0
```

El script local llama a la API de Databricks. Espera un JSON con `space_id`, `commit` y `verified: true`; además guarda `.local/deployed.json`. Abre Databricks → Genie y busca el título de tu práctica, o usa `https://HOST/genie/rooms/SPACE_ID` con tu host e ID.

Si `space_id` ya existe en el JSON, create se detiene. Para una serie en curso se usa plan/apply; para otra práctica vuelve al paso1 en un clon y carpeta remota nuevos. No borres IDs/recibos para forzar un nuevo envío.

## 9. Envía las veinte preguntas a Databricks

En **la misma terminal**, con `.venv` activa y sin cambiar el commit:

```bash
python evaluation/submit.py V0
```

Esto sube el código de esa revisión y pide un Job serverless. La terminal devuelve `V0: run_id=..., commit=...`: es aceptación del envío, todavía no éxito de la evaluación. El Job remoto ejecuta `evaluation/run.py`: comprueba el Space, extrae las veinte preguntas y SQL de referencia de su configuración, genera `gold20.json`, pregunta a Genie, llama al juez y registra MLflow. No necesitas pegar run.py en una celda ni pulsar Run all en un notebook.

## 10. Consulta y abre el Job

```bash
python evaluation/status.py V0
```

Abre `job_url` en tu navegador. En el detalle de la ejecución selecciona la tarea **benchmark** y revisa su estado y salida/logs. En la salida aparecerán casos I01…I20. Puedes consultar otra vez status mientras corre: consulta, no relanza. Un fallo técnico se investiga en los logs; no cuenta como una respuesta incorrecta ni se arregla enviando otra vez a ciegas.

En la UI también puedes entrar por **Jobs & Pipelines → Runs**, localizar el nombre `Ianbal-IaC-V0-...` y cotejar su Run ID con el que imprimió Terminal. El enlace directo es la ruta más segura si la navegación cambia. [Monitoreo de Jobs](https://docs.databricks.com/aws/en/jobs/monitor).

## 11. Abre las métricas en MLflow

Cuando status muestre `TERMINATED` y `SUCCESS`, comprueba `captured_cases: 20`, `summary.judged: 20` y los errores. Abre `mlflow_url`. Este run de MLflow es diferente del Run ID del Job. Inspecciona métricas, reporte y trazas; en Artifacts consulta `benchmark-report.json` si el panel de métricas no muestra toda la información. Registra casos, errores y aciertos, no solo el porcentaje. `null` mientras aún no hay reporte significa pendiente.

## 12. Mejora V1 y V2 en la misma serie

Edita **agente/instrucciones.md** en tu editor según los fallos observados. Guarda el archivo completo. En Terminal:

```bash
git diff -- agente/instrucciones.md
git add agente/instrucciones.md
git commit -m "V1: describir la mejora diagnosticada"
python deploy/genie_space.py plan --label V1
```

Lee el diff que presenta plan. Cuando corresponde al cambio deseado:

```bash
python deploy/genie_space.py apply --label V1
python evaluation/submit.py V1
python evaluation/status.py V1
```

Espera V1 completa antes de cambiar otra vez el agente. Para V2, repite editar→diff→commit→plan→apply→submit→status con etiqueta V2. `--label V1` no busca automáticamente un prompt V1: despliega el commit actual. Gold y juez se mantienen fijos dentro de la serie.

El notebook final publicado corresponde a las **capturas históricas ya verificadas**. No presenta otra serie como validada automáticamente: otra carpeta requiere preparar sus fuentes Git/recibos y configurar su evidencia antes de compararla. La modificación de ubicación nueva está verificada con tests locales; no se lanzó otra serie remota para reescribir estos resultados.

## Recuperación rápida

| Mensaje o síntoma | Qué revisar |
|---|---|
| No such file / no encuentra script | `pwd`, luego `ls evaluation`; debes estar en la raíz del clon. |
| No module named databricks | Activa `.venv` e instala el SDK con ese mismo `python`. |
| Perfil o autorización | Comprueba host/perfil con current-user; completa login. |
| Árbol Git sucio / commit sin desplegar | Guarda cambios en Git; plan/apply de ese commit antes de submit. |
| Ya se envió / ya existe evidencia | Usa status y abre el Job; no borres reportes. |
| Faltan tablas / warehouse / juez | Revisa permisos y recursos del entorno antes de continuar. |
| RUNNING / reporte ausente | Consulta el Job y sus logs; no interpretes pendiente como cero aciertos. |
