# 4. Seguridad y resiliencia

## 4.1 Minimización de datos

| Se envía a la IA | Motivo |
|---|---|
| Idea Semilla | Tema a desarrollar |
| Categoria | Define qué contexto RAG se usa |
| Canal | Adapta el formato del post |
| Contexto validado del Manual de Marca (solo la categoría pedida) | Única fuente de verdad permitida |

**Nunca viajan al modelo:** Record ID, fechas, Estado, Aprobado, Hilo Slack, IDs de canales ni el resto de las filas de Airtable. El nodo `🧠 Unir contexto + armar prompt` arma el request campo por campo, así que no hay forma de que se cuele el registro completo.

- **Credenciales:** las API keys (Airtable, Slack, Gemini) viven en el gestor de credenciales cifrado de n8n. El JSON del workflow no contiene ninguna key: se puede compartir sin riesgo.
- **Anti-alucinación:** el system prompt limita al modelo al contexto validado ("No uses conocimiento externo ni inventes datos").
- **Mínimo privilegio:** el token de Airtable tiene alcance solo sobre las 2 bases. El Manual de Marca solo se lee. El bot de Slack solo escribe en los canales configurados.
- **Video y capturas:** las credenciales se ocultan (se muestran solo los nombres de credencial).

## 4.2 Rutas de error (Error Handlers)

En n8n, lo equivalente a las directivas *Resume/Break* de Make es la opción **On Error** de cada nodo:
- **Continue (using error output)**: equivale a *Resume* con ruta alternativa. El error sale por una segunda salida roja y se registra.
- **Continue**: equivale a *Resume/Ignore*. Se usa solo en nodos de notificación no críticos, para que un fallo al avisar no rompa el registro.
- **Retry on fail**: reintento automático antes de declarar el error.

| # | Nodo protegido | Falla posible | Manejo | Resultado |
|---|---|---|---|---|
| 1 | `❓ ¿Datos completos?` | Idea Semilla vacía o menor a 10 caracteres, Categoria vacía | Rama *false* → SUB 4 | Log con el detalle de qué falta, Estado = **Error**, alerta en Slack. **No se llama a la IA** |
| 2 | `🔒 Anti-bucle` (Airtable update) | Token vencido, registro borrado | Error output → SUB 4 | Log y alerta |
| 3 | `📚 RAG · Buscar en Manual de Marca` | API de Airtable caída | Error output → SUB 4 | Log y Estado = Error |
| 4 | `❓ ¿Hay contexto RAG?` | 0 fragmentos para la categoría | Rama *false* → SUB 4 | No se generan posts sin contexto |
| 5 | `🤖 IA · Gemini` | 503 por alta demanda, 429 por rate limit, timeout | **Retry 3 × 5 s**; si sigue fallando, error output → SUB 4 | El 503 real que apareció en las pruebas se resuelve con el reintento. Si persiste, queda registrado |
| 6 | `❓ ¿Respuesta IA válida?` | Respuesta vacía o bloqueada por seguridad (`finishReason` ≠ STOP) | Rama *false* → SUB 4 | Log con el `finishReason` |
| 7 | `💾 Guardar borrador` | Error de Airtable | Error output → SUB 4 | — |
| 8 | `💬 Slack · Enviar pieza a revisión` / `🧍 HITL` | Canal inválido, token revocado | Error output → SUB 4 | La pieza no queda "colgada" en revisión |
| 9 | `✅ Publicado` / `📣 Publicar` / `🚫 Rechazado` | Error de Airtable o Slack | Error output → SUB 4 | — |
| 10 | Llamadas `🧩 SUB 1..3` | Fallo inesperado del subworkflow | Error output → SUB 4 | — |
| 11 | **Cualquier nodo** (error no previsto) | — | `🛟 Error Trigger · red de seguridad` (opcional: se activa configurando el workflow como su propio *Error Workflow*, si la versión de n8n lo permite) | Log y alerta. Ningún fallo queda silencioso |

**SUB 4 · Registrar error** hace esto: crea el registro en `Log de Errores` **vinculado** al contenido, pone el contenido en `Estado = Error` y avisa en Slack. Los pasos no críticos usan *Continue*, así que el registrador en sí no puede fallar en cadena. Después de registrar, el loop sigue con el próximo registro.

### Filtros anti-bucle y tipos de datos (check de seguridad)
1. **Bucles infinitos:** (a) el trigger solo trae `Estado = 'Generando'`; (b) el primer paso cambia el Estado a `Procesando IA`, así que el mismo registro no vuelve a entrar aunque su *Ultima Modificacion* cambie; (c) el loop procesa como máximo los registros del lote y termina; (d) un `subflujo` desconocido corta con *Stop and Error*.
2. **Tipos correctos:** los IF usan *type validation: strict*. `longitudIdea` (number) ≥ `cfg.minCaracteresIdea` (number); `palabras` (number) > 0; `ok` y `approved` (boolean) se evalúan como boolean, no como texto.
3. **Prompt dinámico:** el prompt se arma solo con variables del registro, del contexto RAG y de `cfg`.

## 4.3 Human-in-the-loop: pausa real

**Acción crítica protegida:** publicar el contenido en el canal de salida, es decir, contactar al público o cliente final.

1. SUB 1 deja el borrador en **En revisión** y el flujo principal publica la pieza completa en `#aprobaciones-contenido`.
2. El nodo **`🧍 HITL · Esperar aprobación humana`** (Slack → *Send and Wait for Response*, aprobación doble) manda los botones **✅ Aprobar y publicar** / **❌ Rechazar**.
3. **La ejecución queda en estado *Waiting*.** n8n guarda el estado y no ejecuta ningún nodo posterior. En la lista de ejecuciones figura como "Waiting". No hay polling ni un segundo escenario.
4. Cuando la persona aprieta un botón, n8n **reanuda la misma ejecución** en tiempo real:
   - `approved = true` → **SUB 2**: Estado **Publicado**, publicación en `#contenido-publicado` y confirmación en el hilo.
   - `approved = false` → **SUB 3**: Estado **Rechazado** y aviso en el hilo. **No se contacta a nadie.**
5. **Timeout de seguridad:** si en `cfg.horasEsperaHITL` (24 h) nadie responde, la ejecución se reanuda como **no aprobada**. La opción segura por defecto es no publicar.

Así se evita el **"efecto metralleta"**: ninguna pieza sale sin una decisión humana explícita. La trazabilidad queda en Airtable (Estado, Aprobado, Fecha de Aprobación, Hilo Slack) y en el hilo de Slack.
