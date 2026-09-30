# 1. Mapa de arquitectura

**Proyecto:** Pipeline de generación y publicación de contenido con IA
**Orquestador:** n8n, en **un solo workflow** con 4 subworkflows internos y un punto HITL que **pausa la ejecución**
**Archivo técnico:** [`workflow/ecosistema-contenido-ia.n8n.json`](../workflow/ecosistema-contenido-ia.n8n.json)

## 1.1 Qué cambió respecto del primer intento

| Devolución del profesor | Cómo se resolvió |
|---|---|
| "Se espera que la integración suceda en **un solo flujo de trabajo con subworkflows** y no tres flujos separados" | Los 3 escenarios de Make se unificaron en **un único workflow de n8n**. El flujo principal invoca 4 **subworkflows** con el nodo *Execute Workflow*, que llama al mismo workflow (`$workflow.id`). El nodo *Entrada de subworkflows* recibe la llamada y un *Router* elige el subflujo. Se importa como un solo archivo `.json`. |
| "Revisá la integración de HITL: se debe **detener el flujo y esperar la intervención humana en tiempo real**" | El nodo **`🧍 HITL · Esperar aprobación humana`** (Slack → *Send and Wait for Response*) **pausa la ejecución**. El workflow no avanza hasta que una persona aprieta **✅ Aprobar y publicar** o **❌ Rechazar** en Slack. Recién en ese momento continúa por la rama correspondiente. Antes, el "HITL" era un checkbox en Airtable que disparaba otro escenario. Ahora la espera ocurre dentro de la misma ejecución. |
| "Asegurar que el repositorio contenga los archivos, configuración y documentación. Agregar instrucciones de ejecución y evidencias verificables" | El repositorio incluye el workflow, un README con los pasos de ejecución, la documentación de los 5 criterios en `docs/`, un plan de pruebas y una lista de evidencias a capturar. |

## 1.2 Diagrama

```mermaid
flowchart LR
  subgraph AT[Airtable · "Pipeline de Contenido" = memoria]
    C[(Contenidos)]
    L[(Log de Errores)]
    M[(Manual de Marca<br/>base RAG · solo lectura)]
  end

  subgraph MAIN[n8n · FLUJO PRINCIPAL]
    T[⚡ Trigger Airtable<br/>Estado = Generando] --> CFG[⚙️ Configuración]
    CFG --> LOOP[🔁 Loop 1 registro]
    LOOP --> N[🧹 Normalizar]
    N --> V{❓ ¿Datos completos?}
    V -- sí --> AB[🔒 Anti-bucle<br/>Estado = Procesando IA]
    AB --> S1c[🧩 SUB 1 · Generación RAG]
    S1c --> OK{❓ ¿IA generó contenido?}
    OK -- sí --> SR[💬 Slack · pieza a revisión<br/>guarda thread_ts]
    SR --> H[🧍 HITL · Send & Wait<br/>⏸ EJECUCIÓN PAUSADA]
    H --> D{❓ ¿Aprobado?}
    D -- ✅ --> S2c[🧩 SUB 2 · Publicación]
    D -- ❌ / timeout --> S3c[🧩 SUB 3 · Rechazo]
    V -- no --> E[🧾 Normalizar error]
    AB -. error .-> E
    SR -. error .-> E
    H -. error .-> E
    E --> S4c[🧩 SUB 4 · Registrar error]
    S2c & S3c & S4c --> LOOP
  end

  subgraph SUBS[n8n · SUBWORKFLOWS mismo archivo]
    IN[📥 Entrada de subworkflows] --> R{🔀 Router}
    R -- generar_rag --> RAG[📚 Buscar Manual] --> P[🧠 Armar prompt] --> G[🤖 Gemini<br/>retry x3] --> VAL[🧪 Validar respuesta] --> SAVE[💾 Estado = En revisión]
    R -- publicar --> PUB[✅ Estado = Publicado] --> OUT[📣 Slack #contenido-publicado] --> TH1[🧵 Respuesta en hilo]
    R -- rechazar --> REJ[🚫 Estado = Rechazado] --> TH2[🧵 Respuesta en hilo]
    R -- registrar_error --> LOG[📝 Log de Errores] --> ERR[⚠️ Estado = Error] --> AL[🚨 Slack alerta]
  end

  S1c -. Execute Workflow .-> IN
  S2c -. Execute Workflow .-> IN
  S3c -. Execute Workflow .-> IN
  S4c -. Execute Workflow .-> IN

  C -- registros --> T
  M -- contexto validado --> RAG
  SAVE & PUB & REJ & ERR --> C
  LOG --> L
  L -. link .-> C
```

El mismo diagrama, en versión visual para imprimir, está en [`entrega/Diagrama-Arquitectura.pdf`](../entrega/Diagrama-Arquitectura.pdf).

## 1.3 Componentes por categoría obligatoria

| Categoría | Tecnología | Nodos |
|---|---|---|
| **Orquestador** | n8n: 1 workflow, 4 subworkflows | `⚡ Trigger`, `🔁 Loop`, `🔀 Router de subworkflows`, `🧩 SUB 1..4` (Execute Workflow) |
| **Base de datos (memoria)** | Airtable: base "Pipeline de Contenido" y base "Manual de Marca" | Contenidos (estado), Log de Errores (vinculada a Contenidos), Manual de Marca (RAG) |
| **Procesamiento IA** | Google Gemini `gemini-3.6-flash` vía API REST, con RAG y prompt estructurado. Se puede cambiar por Claude u OpenAI: ver criterio 3 | `🧠 Unir contexto + armar prompt`, `🤖 IA · Gemini genera borrador`, `🧪 Validar respuesta IA` |
| **Canal de salida** | Slack: aprobaciones con botones, publicación y respuestas en hilo (`thread_ts`) | `💬 Slack · Enviar pieza a revisión`, `🧍 HITL`, `📣 Slack · Publicar`, `🧵 Respuestas en hilo`, `🚨 Alerta de error` |

## 1.4 Recorrido de una pieza (camino feliz)

1. En Airtable se carga una fila con *Idea Semilla*, *Categoria*, *Canal* y **Estado = Generando**.
2. El **trigger de Airtable** consulta la tabla cada minuto y solo trae registros que cumplen `{Estado} = 'Generando'`. Así se evitan operaciones innecesarias.
3. `⚙️ Configuración` define las variables del sistema: modelo, max tokens, temperatura, canales y horas de espera del HITL. Ningún dato de negocio queda escrito dentro de los nodos.
4. El **loop** procesa **un registro por vez**. Cada registro tiene su propia pausa HITL.
5. Se valida la entrada. Enseguida el registro pasa a **Procesando IA**, que funciona como bloqueo anti-bucle: el trigger ya no vuelve a tomarlo.
6. **SUB 1** busca el contexto del Manual de Marca (RAG), arma el prompt dinámico, llama a Gemini (con 3 reintentos ante un 503), valida la respuesta y guarda el borrador en **En revisión**.
7. Slack recibe la pieza completa en `#aprobaciones-contenido`. Su `thread_ts` se guarda para responder en el mismo hilo.
8. **HITL:** el workflow **se pausa** con los botones Aprobar/Rechazar. Si nadie responde en 24 h (configurable), se toma como rechazo.
9. Si se aprueba, **SUB 2** marca **Publicado**, completa la *Fecha de Aprobación* y el *Hilo Slack*, publica en `#contenido-publicado` y responde en el hilo original.
10. Si se rechaza, **SUB 3** marca **Rechazado**, responde en el hilo y no contacta a nadie.
11. Si algo falla, **SUB 4** crea un registro en **Log de Errores** vinculado al contenido, marca **Error** y manda una alerta a Slack. Después el loop sigue con el próximo registro.
