# 3. Optimización de costos: matriz de decisión de modelos

## 3.1 Matriz: qué modelo para cada tarea

| # | Tarea del ecosistema | Volumen / latencia | Modelo elegido | Por qué | Alternativa descartada y motivo |
|---|---|---|---|---|---|
| 1 | **Redactar el post con RAG**: lectura densa del Manual de Marca y redacción con tono de marca | Bajo (pocas piezas por día); interactivo, porque hay un humano esperando para revisar | **Implementado:** Gemini `gemini-3.6-flash` (free tier). **Producción:** Claude Sonnet con *prompt caching* | En producción la prioridad es la calidad del texto y la consistencia de tono sobre contexto largo. En esta entrega se usa el free tier por presupuesto | GPT-4o-mini: más barato, pero rinde menos en redacción larga con tono de marca |
| 2 | **Validar entrada** (campos vacíos, largo mínimo) | Cada ejecución | **Sin LLM**: IF de n8n | Es una regla determinística y cuesta $0. Usar IA acá sería desperdicio | Pedirle al LLM que "detecte datos faltantes": caro y no determinístico |
| 3 | **Validar la salida de la IA** (vacía, bloqueada, truncada) | Cada ejecución | **Sin LLM**: Code node (`finishReason`, conteo de palabras) | Costo $0; mide tokens para auditar el gasto | Un segundo LLM como "juez": duplica el costo por pieza |
| 4 | **Clasificar la categoría** de una idea cuando llega vacía (mejora futura) | Alto volumen; texto corto | **GPT-4o-mini** o Claude Haiku | Tarea de bajo razonamiento: el modelo chico alcanza a un costo entre 10 y 20 veces menor | Sonnet: sobredimensionado para una clasificación |
| 5 | **Regenerar el catálogo completo** (ej. 1.000 piezas por cambio de manual) | Masivo; no urgente | **Batch API** (Anthropic u OpenAI) | 50 % de descuento a cambio de respuesta diferida (hasta 24 h); no hay humano esperando | API síncrona: paga el doble sin ningún beneficio |
| 6 | Prototipado y pruebas de estrés | 5 a 20 corridas | **Gemini free tier** | $0; el límite de 15 req/min alcanza | — |

## 3.2 Palancas de costo aplicadas en el workflow

| Palanca | Dónde | Efecto |
|---|---|---|
| **Trigger filtrado** `{Estado}='Generando'` | `⚡ Trigger` | El flujo solo corre cuando hay trabajo real. Sin polling de registros ya procesados |
| **Anti-bucle** `Procesando IA` | `🔒 Anti-bucle` | Un registro nunca se procesa dos veces, así que no se pagan tokens por duplicado |
| **Validación antes de la IA** | `❓ ¿Datos completos?`, `❓ ¿Hay contexto RAG?` | Si faltan datos o no hay contexto, **no se llama al modelo**. En la entrega anterior una Idea Semilla vacía generaba un post inútil y gastaba tokens |
| **`maxOutputTokens` = 1000** y límite de `maxPalabras` | `⚙️ Configuración` → prompt | Tope al costo de salida por pieza |
| **Minimización del prompt** | `🧠 Unir contexto + armar prompt` | Solo viajan idea, categoría, canal y el contexto filtrado por categoría, no toda la tabla |
| **Reintentos acotados** (3 × 5 s) | `🤖 IA · Gemini` | Resuelve el 503 que se vio en las pruebas sin reintentos infinitos |
| **Medición** de `tokensEntrada` / `tokensSalida` | `🧪 Validar respuesta IA` | Permite auditar el gasto real por pieza |

## 3.3 Precios de referencia (USD por 1M de tokens)

| Modelo | Input | Output | Input Batch (−50 %) | Output Batch (−50 %) |
|---|---|---|---|---|
| Claude Sonnet | 3,00 | 15,00 | 1,50 | 7,50 |
| GPT-4o-mini | 0,15 | 0,60 | 0,075 | 0,30 |
| Gemini Flash (pago) | 1,50 | 7,00 | 0,75 | 3,75 |
| Gemini free tier (usado) | 0 | 0 | — | — |

*Son precios de lista tomados como referencia al momento de armar la matriz. Hay que verificarlos antes de pasar a producción.*

## 3.4 Ahorro estimado

Volumen de ejemplo: **1.000 piezas por mes**, cada una con ~800 tokens de entrada (≈500 de contexto estático del manual y ≈300 dinámicos) y ~400 de salida.

| Escenario | Cálculo | Costo mensual | Ahorro vs. A |
|---|---|---|---|
| **A** — Sonnet estándar | 0,8 × 3 + 0,4 × 15 | **USD 8,40** | — |
| **B** — Sonnet + prompt caching (contexto estático cacheado; lectura al 10 %) | 0,3 × 3 + 0,5 × 0,30 + 0,4 × 15 | **USD 7,05** | −16 % |
| **C** — Sonnet + caching + Batch (solo regeneración masiva) | 0,3 × 1,5 + 0,5 × 0,15 + 0,4 × 7,5 | **USD 3,53** | −58 % |
| **D** — Clasificación (tarea 4) con GPT-4o-mini en vez de Sonnet (1.000 × 100 tokens de entrada y 10 de salida) | 0,1 × 0,15 + 0,01 × 0,60 vs. 0,1 × 3 + 0,01 × 15 | **USD 0,02** vs. 0,45 | −95 % en esa tarea |
| **E** — Validaciones sin LLM (tareas 2 y 3) | Evita ~1 llamada extra por pieza | ≈ USD 8,40 evitados si se usara Sonnet como juez | −100 % en esa tarea |
| **Implementación actual** — Gemini free tier | — | **USD 0** | −100 % |

**Criterio de migración:** si el volumen supera el free tier (15 req/min), el primer paso es activar la facturación de Gemini Flash. Solo cambia la credencial. Si la prioridad pasa a ser la calidad de redacción, se migra la tarea 1 a Claude Sonnet con caching. Para esa migración solo se modifican 2 nodos: la URL y el body del `🤖 IA` (endpoint `https://api.anthropic.com/v1/messages`, `max_tokens` = `cfg.maxTokens`) y el parseo en `🧪 Validar respuesta IA` (`content[0].text`). El resto del workflow no cambia.

**Condición para que funcione el caching:** el bloque estático (system prompt y contexto del manual) tiene que ir primero y con contenido y orden idénticos en cada llamada. Cualquier variación invalida la caché.
