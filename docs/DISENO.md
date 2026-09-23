# Ensayo real de evolución de Genie

Un repo privado nuevo, un Genie Space nuevo y un único prompt completo `agente/instrucciones.md`. Git conserva la historia; no se crean archivos V1/V2 ni puntero active.md. `agente/space.json` versiona tablas, ejemplos SQL, benchmarks y demás configuración; el renderer inserta el prompt en el único contenedor de instrucciones.

Secuencia autorizada: commit V0 → deploy → congelar referencia SQL → benchmark de 20 preguntas → revisar fallos → commit V1 → deploy mismo Space → benchmark → revisar fallos → commit V2 → deploy → benchmark. Solo después se ejecuta el notebook final de validación/comparación. No se espera mejora garantizada; ningún ensayo se elimina por malos resultados. La base de preguntas es conocida y proviene del export docente V0, no es un conjunto de prueba reservado.

Cada despliegue exige árbol Git limpio y vincula commit, configuración, timestamp y Space ID. La evaluación comprueba los hashes antes y después, comparte gold/juez/rúbrica y guarda las 20 respuestas. El notebook final no hace inferencias ni modifica el agente; verifica integridad y presenta correcciones/regresiones. Datos, ACL y warehouse no forman parte del despliegue.

La configuración completa se guarda en repo privado para que V0 sea visible; respuestas/gold con filas de negocio se conservan localmente y en el workspace autorizado. No se importa material de Apex. Se reutiliza el evaluador docente y se adapta el despliegue ya probado.
