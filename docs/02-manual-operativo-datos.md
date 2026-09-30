# 2. Manual operativo de datos

## 2.1 Esquema de tablas en Airtable

El sistema usa la base **"Pipeline de Contenido"** (`appCtyPCA4QGzyXR5`) como memoria y registro. El contexto RAG sale de la base **"Manual de Marca"** (`app8saP7sKupgcjAK`), que el flujo solo lee.

### Tabla `Contenidos` (`tblPQPkpH8S5B10wz`): núcleo y máquina de estados

| Campo | Tipo | Quién lo escribe | Uso |
|---|---|---|---|
| Idea Semilla | Long text | Humano | Tema que desarrolla la IA (obligatorio, mínimo 10 caracteres) |
| Categoria | Single select | Humano | Filtra los fragmentos del Manual de Marca (RAG) |
| Canal | Single select | Humano | Destino editorial (ej. LinkedIn). Se incluye en el prompt |
| **Estado** | Single select | Humano / n8n | `Generando` → `Procesando IA` → `En revisión` → `Publicado` / `Rechazado` / `Error` |
| Contenido Generado | Long text | n8n (SUB 1) | Borrador de la IA |
| Aprobado | Checkbox | n8n (SUB 2/3) | Resultado de la decisión humana tomada en Slack |
| Fecha de Aprobación | Date | n8n (SUB 2) | Fecha en que se aprobó |
| **Hilo Slack** | Single line text | n8n (SUB 2/3) | `thread_ts` del mensaje de revisión, para trazabilidad del hilo |
| Notificado | Checkbox | (legado Make) | Ya no se usa: la notificación y la espera ocurren dentro de la misma ejecución |
| Ultima Modificacion | Last modified time | Airtable | Campo que usa el trigger de n8n |
| Errores | Link → Log de Errores | Airtable (campo inverso) | Relación 1:N con los errores del registro |
| KPI Aprobación / KPI Salida / KPI Error | Formula | Airtable | Alimentan el Dashboard (ver criterio 5) |

Los estados equivalen a los que pide la consigna: *Pendiente* = `Generando`, *Procesado por IA* = `En revisión`, *Aprobado por Humano* = `Publicado`.

### Tabla `Log de Errores` (`tblgYFeGeFImx8eZe`): resiliencia y auditoría

| Campo | Tipo | Uso |
|---|---|---|
| Modulo | Single line text | Nodo de n8n que falló (ej. `🤖 IA · Gemini genera borrador`) |
| Mensaje | Long text | Mensaje de error capturado |
| Fecha | Created time | Automático |
| **Contenido** | Link → Contenidos | **Relación entre tablas**: el error queda vinculado al registro afectado, así ningún dato queda aislado |

### Tabla `Manual de Marca` (`tblJNVngOBOStcL4k`, vista verificada `viwlVKJmk27LL5Wy8`): fuente RAG, solo lectura

| Campo | Tipo | Uso |
|---|---|---|
| Categoria | Single select | Se filtra con `{Categoria} = '<categoría del contenido>'` |
| Tema | Single line text | Título del fragmento |
| Contenido Validado | Long text | Texto que se inyecta como contexto en el prompt |

Esta tabla vive en otra base y Airtable no permite links entre bases. Por eso la relación con `Contenidos` es lógica: la hace el flujo, por **Categoria**. La sincronización entre ambas bases también la resuelve el flujo, como pide la consigna.

### Cambios a aplicar en Airtable (una sola vez)

1. En `Contenidos`, agregar el campo **Hilo Slack** (Single line text).
2. En `Log de Errores`, agregar el campo **Contenido** (Link to another record → Contenidos). Airtable crea solo el campo inverso **Errores** en `Contenidos`.
3. Las opciones `Procesando IA` y `Error` del campo **Estado** se crean solas: los nodos de Airtable escriben con `typecast: true`. También se pueden crear a mano.
4. Crear los 3 campos fórmula del dashboard (criterio 5).

## 2.2 Esquemas JSON de transferencia entre integraciones

Todos los ejemplos son reales en estructura. Los IDs se acortaron.

### a) Airtable Trigger → Configuración (entrada del flujo)
```json
{
  "id": "recECFm6VtGeO7RrI",
  "createdTime": "2026-09-29T13:02:11.000Z",
  "fields": {
    "Idea Semilla": "Tips de organización para freelancers",
    "Categoria": "Servicios",
    "Canal": "LinkedIn",
    "Estado": "Generando",
    "Ultima Modificacion": "2026-09-29T13:02:40.000Z"
  }
}
```

### b) `🧹 Normalizar registro`: objeto interno del flujo
```json
{
  "recordId": "recECFm6VtGeO7RrI",
  "idea": "Tips de organización para freelancers",
  "categoria": "Servicios",
  "canal": "LinkedIn",
  "longitudIdea": 37,
  "cfg": {
    "modeloIA": "gemini-3.6-flash", "maxTokens": 1000, "temperatura": 0.7,
    "maxPalabras": 200, "minCaracteresIdea": 10,
    "canalAprobaciones": "C0C12LQCXJR", "canalPublicacion": "contenido-publicado",
    "canalAlertas": "C0C12LQCXJR", "horasEsperaHITL": 24
  }
}
```
`longitudIdea` y `minCaracteresIdea` son **números** y se comparan como números (`number ≥ number`), con validación de tipos estricta en el IF.

### c) Contrato de llamada a un subworkflow (Execute Workflow → Entrada de subworkflows)
```json
{ "subflujo": "generar_rag", "recordId": "rec…", "idea": "…", "categoria": "Servicios", "canal": "LinkedIn", "cfg": { … } }
```
Valores posibles de `subflujo`: `generar_rag` | `publicar` | `rechazar` | `registrar_error`. Si llega otro valor, el Router lo manda a `⛔ Subflujo desconocido`, que corta con un error.

### d) Airtable Search (Manual de Marca) → `🧠 Unir contexto + armar prompt`
```json
[
  { "id": "recA1…", "Categoria": "Servicios", "Tema": "Consultoría", "Contenido Validado": "Ofrecemos consultoría personalizada de organización financiera para freelancers…" },
  { "id": "recA2…", "Categoria": "Servicios", "Tema": "Tono de voz", "Contenido Validado": "Hablamos de vos, cercano y profesional…" }
]
```
Puede devolver N fragmentos. El nodo Code los concatena en un solo bloque de contexto. Si devuelve 0, se toma como error: no se gastan tokens sin contexto.

### e) Request a la IA (HTTP → `generateContent` de Gemini)
```json
{
  "system_instruction": { "parts": [{ "text": "Sos el redactor de contenido de la marca. Tu única fuente de verdad es el CONTEXTO VALIDADO… de no más de 200 palabras." }] },
  "contents": [{ "role": "user", "parts": [{ "text": "Idea semilla: Tips de organización para freelancers\nCategoría: Servicios\nCanal destino: LinkedIn\n\nCONTEXTO VALIDADO DE LA MARCA:\nTema: Consultoría\nOfrecemos…" }] }],
  "generationConfig": { "maxOutputTokens": 1000, "temperature": 0.7 }
}
```
Todo el prompt se arma con variables (`idea`, `categoria`, `canal`, contexto RAG, `cfg.maxPalabras`). No hay texto de negocio escrito a mano.

### f) Respuesta de la IA → `🧪 Validar respuesta IA`
```json
{
  "candidates": [{ "content": { "parts": [{ "text": "¿Sos freelancer y sentís que tu tiempo no rinde?…" }] }, "finishReason": "STOP" }],
  "usageMetadata": { "promptTokenCount": 812, "candidatesTokenCount": 356 }
}
```
Se mapea `candidates[0].content.parts[*].text` a `contenido`. Además se calculan `palabras`, `finishReason` y los tokens de entrada y salida, que sirven para controlar costos.

### g) Salida de SUB 1 (vuelve al flujo principal)
```json
{ "ok": true, "recordId": "rec…", "idea": "…", "categoria": "Servicios", "canal": "LinkedIn", "contenido": "¿Sos freelancer…", "palabras": 187, "tokensEntrada": 812, "tokensSalida": 356 }
```

### h) Slack: mensaje de revisión (`chat.postMessage`)
```json
{ "channel": "C0C12LQCXJR", "text": "📋 *Nueva pieza para revisar* (registro `rec…`)\n*Idea semilla:* …\n*Borrador generado por IA:*\n>>> …" }
```
Respuesta: `{ "ok": true, "channel": "C0C12LQCXJR", "message_timestamp": "1759150000.123456" }`. Ese valor es el **Thread ID** (`thread_ts`) que se reutiliza después.

### i) HITL: Slack *Send and Wait for Response* (salida cuando el humano responde)
```json
{ "data": { "approved": true } }
```
`approved: false` (❌ Rechazar), o que se cumpla el plazo sin respuesta, lleva a SUB 3.

### j) Payload de SUB 2 / SUB 3 y respuesta en hilo
```json
{ "subflujo": "publicar", "recordId": "rec…", "idea": "…", "canal": "LinkedIn", "contenido": "…", "threadTs": "1759150000.123456", "cfg": { … } }
```
```json
{ "channel": "C0C12LQCXJR", "thread_ts": "1759150000.123456", "text": "✅ Aprobado por revisión humana y publicado en #contenido-publicado…" }
```

### k) Registro final en Airtable (tras aprobación)
```json
{ "id": "rec…", "fields": { "Estado": "Publicado", "Aprobado": true, "Fecha de Aprobación": "2026-09-30", "Hilo Slack": "1759150000.123456", "Contenido Generado": "…" } }
```

### l) SUB 4: registro de error
```json
{ "subflujo": "registrar_error", "recordId": "rec…", "modulo": "🤖 IA · Gemini genera borrador", "mensaje": "503 - The model is overloaded", "cfg": { … } }
```
→ Airtable `Log de Errores`: `{ "Modulo": "🤖 IA · Gemini genera borrador", "Mensaje": "503 - …", "Contenido": ["rec…"] }`
