# 6. Test de estrés y evidencias

## 6.1 Plan de pruebas (mínimo 5 ejecuciones)

| # | Caso | Datos de entrada en Airtable | Acción humana | Resultado esperado | Evidencia a capturar |
|---|---|---|---|---|---|
| 1 | Camino feliz: aprobación | Idea "Tips de organización para freelancers", Categoria "Servicios", Estado "Generando" | ✅ Aprobar en Slack | Estado **Publicado**, Aprobado ✔, Fecha y Hilo Slack completos; post en `#contenido-publicado`; confirmación en el hilo | Ejecución en n8n (verde), mensaje de Slack con botones, post publicado, fila de Airtable |
| 2 | Camino feliz: rechazo | Otra idea válida | ❌ Rechazar | Estado **Rechazado**; aviso en el hilo; **nada** en `#contenido-publicado` | Ejecución con la rama "false" del IF |
| 3 | **Pausa HITL visible** | Idea válida | Esperar 2 minutos **antes** de responder | La ejecución figura como **Waiting** en *Executions*; después de apretar el botón pasa a *Success* | Captura de la ejecución "Waiting" y de la misma ejecución terminada |
| 4 | Camino infeliz: dato faltante | Idea Semilla **vacía** | — | No se llama a la IA; Log de Errores "Validación de entrada: Idea Semilla vacía"; Estado **Error**; alerta en Slack | Rama false de `❓ ¿Datos completos?`, fila en Log de Errores vinculada |
| 5 | Camino infeliz: idea demasiado corta | Idea "Hola" (4 caracteres) | — | Error "Idea Semilla demasiado corta (4 < 10)" | Idem |
| 6 | Camino infeliz: categoría sin contexto | Categoria que no existe en el Manual (ej. "Legales") | — | Error "Sin contexto validado…"; no se gastan tokens | Rama false de `❓ ¿Hay contexto RAG?` |
| 7 | Fallo de API de IA | Cambiar temporalmente `cfg.modeloIA` a `modelo-inexistente` | — | 3 reintentos, después Log "🤖 IA · Gemini…" con el 404; Estado Error | Nodo con "Retry on fail" y salida de error |
| 8 | Lote (varios registros juntos) | 3 filas en "Generando" a la vez | Aprobar 2 y rechazar 1 | El loop procesa de a uno; cada pieza tiene su propia pausa HITL | Ejecución con 3 iteraciones |
| 9 | Anti-bucle | Editar una fila que ya está "En revisión" | — | El trigger **no** la vuelve a tomar | Lista de ejecuciones sin disparos nuevos |

## 6.2 Evidencias (capturas) a incluir en el documento público

1. Canvas completo del workflow en n8n, con el flujo principal y los subworkflows a la vista.
2. Zoom al nodo **HITL** (configuración *Send and Wait*, aprobación doble y límite de espera).
3. Lista de *Executions* con al menos una ejecución en **Waiting** y 5 o más ejecuciones terminadas (éxito y error).
4. Mensaje de Slack con los botones Aprobar/Rechazar y la respuesta en el hilo.
5. Post publicado en `#contenido-publicado`.
6. Tabla `Contenidos` con registros en Publicado, Rechazado y Error.
7. Tabla `Log de Errores` con registros vinculados a `Contenidos`.
8. Dashboard (Shared View) abierto en incógnito, con los 3 KPIs.
9. Credenciales de n8n ocultas: se muestran solo los nombres, nunca las keys.

## 6.3 Resultados de las corridas (1 de octubre de 2026, n8n Cloud)

| # | Hora | Caso | Resultado observado | Estado final en Airtable |
|---|---|---|---|---|
| 1 | 11:21 | Credencial de Airtable sin acceso a la base (403) | Error output del Anti-bucle → SUB 4 → alerta en Slack "Forbidden". Se corrigió con un Personal Access Token | — |
| 2 | 11:30 | Fallo real de la API de IA (Gemini 503 *Service unavailable*) | 3 reintentos automáticos; luego SUB 4: alerta en Slack y Estado **Error** | Error |
| 3 | 11:38 | **Camino feliz + HITL**: borrador generado con RAG y enviado a revisión | La ejecución quedó en **"Esperando"** hasta el clic; al aprobar, SUB 2 publicó en #contenido-publicado | **Publicado** |
| 4 | 11:48 | Rechazo humano ("Cómo fijar tus tarifas como freelancer") | Clic en ❌ Rechazar → SUB 3, aviso en el hilo; nada en el canal de salida | **Rechazado** |
| 5 | 11:52 | Camino infeliz: Idea Semilla vacía | La IA no se invocó; registro en Log de Errores (vinculado al contenido) y alerta en Slack "Datos faltantes: Idea Semilla vacía" | **Error** |

Las 5 corridas cubren el camino feliz, el rechazo, la pausa HITL, el dato faltante y el fallo de API. Las capturas de cada una están en el documento público.
