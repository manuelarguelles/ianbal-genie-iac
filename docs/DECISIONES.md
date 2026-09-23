# Decisiones de mejora basadas en esta ejecución

## V0 → V1

V0 (`ff6de6c`) terminó el 23-sep-2026 con **17/20**, 20 juicios y cero errores técnicos. La configuración permaneció estable durante la captura. Evidencia resumida: `evidence/V0.json`; respuestas/trazas completas en el workspace y `.local/captures`.

Fallos I08 e I10: la consulta agrupó también por moneda antes de LIMIT 5. El resultado contenía cinco filas pero solo dos items distintos. Hipótesis V1: explicitar una fila por item antes de ordenar/limitar elimina ese error de grano. Se añade esa regla al mismo `agente/instrucciones.md`, conservando la base completa. Las monedas se pueden mostrar como conjunto; se aclara que métricas nominales mixtas no son precios económicamente normalizados.

I17: la respuesta dio promedios por moneda, pero la referencia calcula promedio nominal global. Se conserva como hallazgo separado; esta versión no añade una regla específica para ese caso. No se cambian preguntas, gold, rúbrica, juez, código de benchmark, tablas o ejemplos SQL. Se evalúa todo el benchmark después de aplicar, no solo los dos casos fallidos.

## V1 → V2

V1 (`c38a730`) terminó con **18/20**, 20 juicios y cero errores técnicos. I08 e I10 pasaron; I17 siguió fallando. La evaluación automática también marcó I06 como regresión: V1 contó correctamente proveedores distintos (4), pero el gold compara ofertas (6). Una consulta SQL independiente confirmó 6 filas/ofertas y 4 supplier_id distintos. Se registra un defecto del examen, no una instrucción para responder 6 proveedores. La revisión humana en Review App queda pendiente del docente.

Hipótesis V2: responder el promedio global solicitado como **estadístico nominal**, con la advertencia visible de que mezcla monedas y no constituye precio comparable. Se mantiene el desglose por moneda como complemento y se requieren tipos de cambio/fecha para comparaciones económicas. Solo se añade esta precisión al mismo prompt completo. El gold original se conserva en esta serie; corregir I06 requiere versionar el examen y volver a evaluar en un ciclo nuevo.
