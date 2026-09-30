# Entrega Final: Ecosistema de Automatización IA Autónomo

**Alumna:** Agustina Cisneros · **Caso de uso:** pipeline de generación y publicación de contenido de marketing con IA (RAG), con aprobación humana en tiempo real antes de publicar.

| Categoría | Tecnología |
|---|---|
| Orquestador | **n8n**: **un solo workflow** con **4 subworkflows** internos |
| Base de datos (memoria) | **Airtable**: `Contenidos` ⇄ `Log de Errores` (vinculadas) y `Manual de Marca` (RAG) |
| Procesamiento IA | **Google Gemini** (`gemini-3.6-flash`) con RAG y prompt dinámico; se puede cambiar por Claude u OpenAI ([criterio 3](docs/03-matriz-costos.md)) |
| Canal de salida | **Slack**: aprobación con botones (HITL), publicación y respuestas en hilo (`thread_ts`) |

## Correcciones respecto del intento 1

| Devolución | Solución en esta versión |
|---|---|
| Se esperaba **un solo flujo con subworkflows**, no 3 escenarios separados | Un único archivo [`workflow/ecosistema-contenido-ia.n8n.json`](workflow/ecosistema-contenido-ia.n8n.json). El flujo principal llama a **SUB 1 Generación RAG**, **SUB 2 Publicación**, **SUB 3 Rechazo** y **SUB 4 Registro de errores** con *Execute Workflow*, invocando al mismo workflow (`$workflow.id`) |
| El **HITL** tiene que **detener el flujo y esperar la intervención humana en tiempo real** | El nodo `🧍 HITL · Esperar aprobación humana` (Slack *Send and Wait for Response*) **pausa la ejecución**, que queda en estado *Waiting*. Se reanuda recién cuando una persona aprieta **Aprobar** o **Rechazar** |
| Faltaban archivos, instrucciones de ejecución y evidencias verificables | Se agregaron esta guía, la documentación de los 5 criterios en `docs/`, un plan de pruebas y una lista de evidencias |

Los blueprints de Make del intento 1 quedan en [`legacy/make/`](legacy/make) solo como historial. **Ya no forman parte de la solución.**

## Contenido del repositorio

| Criterio de la rúbrica (20 % c/u) | Documento |
|---|---|
| 1. Mapa de arquitectura | [`docs/01-arquitectura.md`](docs/01-arquitectura.md) y [`entrega/Diagrama-Arquitectura.pdf`](entrega/Diagrama-Arquitectura.pdf) |
| 2. Estructuras de datos (tablas y JSON) | [`docs/02-manual-operativo-datos.md`](docs/02-manual-operativo-datos.md) |
| 3. Optimización de costos (matriz de modelos) | [`docs/03-matriz-costos.md`](docs/03-matriz-costos.md) |
| 4. Seguridad, resiliencia y HITL | [`docs/04-seguridad-resiliencia.md`](docs/04-seguridad-resiliencia.md) |
| 5. Dashboard de control (Shared View) | [`docs/05-dashboard-control.md`](docs/05-dashboard-control.md) |
| Test de estrés y evidencias | [`docs/06-pruebas-y-evidencias.md`](docs/06-pruebas-y-evidencias.md) |
| Workflow (archivo técnico) | [`workflow/ecosistema-contenido-ia.n8n.json`](workflow/ecosistema-contenido-ia.n8n.json) |
| Documento único para subir (PDF) | [`entrega/Entrega-Final-Agustina-Cisneros.pdf`](entrega/Entrega-Final-Agustina-Cisneros.pdf) |
| Evidencias de la versión anterior (Make) | [`evidencias/`](evidencias) |

## Enlaces

- **Dashboard de control (Shared View):** https://airtable.com/appCtyPCA4QGzyXR5/shrBIC22XxubHnrfF *(si se crea la vista de KPIs nueva, reemplazar este link por el nuevo)*
- **Base de datos en modo lectura:** _pegar acá el link de lectura de la base "Pipeline de Contenido"_
- **Documento público (Google Doc / Notion):** _pegar acá el link_
- **Video demo (3 min):** _pegar acá el link_

## Cómo ejecutarlo

### Requisitos
- n8n Cloud o self-hosted **accesible desde internet**: los botones de Slack reanudan la ejecución a través de una URL de n8n.
- Credenciales creadas en n8n:
  - **Airtable Personal Access Token** (scopes `data.records:read`, `data.records:write`, `schema.bases:read` sobre las 2 bases).
  - **Slack** (OAuth2 o bot token con `chat:write`, `channels:read`), con el bot invitado a `#aprobaciones-contenido` y `#contenido-publicado`.
  - **Google Gemini (PaLM) API** con la API key de Google AI Studio.

### Pasos
1. **Airtable (una sola vez):**
   - En `Contenidos`, crear el campo **Hilo Slack** (Single line text).
   - En `Log de Errores`, crear el campo **Contenido** (link a `Contenidos`).
   - Crear los campos fórmula del dashboard ([criterio 5](docs/05-dashboard-control.md)).
2. **Importar:** en n8n, *Workflows → Import from File →* `workflow/ecosistema-contenido-ia.n8n.json`.
3. **Credenciales:** abrir cada nodo de Airtable, Slack y `🤖 IA · Gemini` y elegir la credencial. Si un canal de Slack aparece marcado, volver a elegirlo de la lista.
4. **Configuración:** revisar el nodo `⚙️ Configuración del sistema` (modelo, tokens, canales, horas de espera del HITL). Los IDs de base y tabla ya corresponden a la base del proyecto.
5. **Guardar** el workflow. Los subworkflows se invocan con `$workflow.id`, así que el workflow tiene que estar guardado.
6. **Red de seguridad:** *Workflow Settings → Error workflow →* elegir **este mismo workflow**. Así se activa `🛟 Error Trigger`.
7. **Activar** el workflow (toggle *Active*).
8. **Probar:** en Airtable, crear una fila con Idea Semilla, Categoria, Canal y **Estado = Generando**. En menos de 1 minuto llega la pieza a Slack. La ejecución queda en **Waiting** hasta apretar ✅ o ❌.

### Estados del registro
`Generando` → `Procesando IA` → `En revisión` → ⏸ **HITL** → `Publicado` | `Rechazado` · (ante un fallo: `Error` + Log de Errores)

## Check de seguridad

1. **Filtro anti-bucle:** el trigger solo toma `Estado = 'Generando'` y el primer paso cambia el Estado a `Procesando IA`. Un Router con fallback *Stop and Error* frena cualquier subflujo desconocido.
2. **Tipos correctos:** los IF usan validación estricta. Se comparan número con número (`longitudIdea ≥ minCaracteresIdea`, `palabras > 0`) y boolean con boolean (`ok`, `approved`).
3. **Prompt dinámico:** se arma solo con variables (idea, categoría, canal, contexto RAG y `cfg`).
