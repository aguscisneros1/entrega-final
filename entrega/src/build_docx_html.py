import pathlib, re, markdown
root = pathlib.Path('/home/user/entrega-final')
ph = lambda t: f'<p style="background:#fff3cd;border:1px solid #f0ad4e;padding:8px"><b>📸 PEGAR ACÁ LA CAPTURA:</b> {t}</p>'
parts=[]
for md in sorted((root/'docs').glob('0*.md')):
    t = md.read_text(encoding='utf-8')
    t = re.sub(r"```mermaid.*?```", "<img src=\"/home/user/entrega-final/entrega/img/diagrama-arquitectura.png\" width=\"640\">", t, flags=re.S)
    t = re.sub(r"\]\((\.\./)?(workflow|entrega|docs)/[^)]*\)", "]", t)
    t = re.sub(r"\[([^\]]+)\](?!\()", r"\1", t)
    parts.append(markdown.markdown(t, extensions=["tables","fenced_code","nl2br"]))
REPO='https://github.com/aguscisneros1/entrega-final/tree/claude/ia-automation-unified-workflow-iuscap'
WF='https://github.com/aguscisneros1/entrega-final/blob/claude/ia-automation-unified-workflow-iuscap/workflow/ecosistema-contenido-ia.n8n.json'
C = "/tmp/claude-0/-home-user-entrega-final/8253df89-7381-57f4-b871-296b8383ab09/scratchpad/caps/"
CANVAS = "/home/user/entrega-final/entrega/img/workflow-n8n-canvas.png"
ev = [
 ("7.1 Workflow único en n8n: flujo principal (azul) + subworkflows (verde)", [CANVAS]),
 ("7.2 HITL: la ejecución queda PAUSADA (“Esperando”) hasta la decisión humana", [C+"img03.png"]),
 ("7.3 HITL: mensaje de aprobación en Slack con los botones Rechazar / Aprobar y publicar", [C+"img02.png", C+"img06.png"]),
 ("7.4 Después del clic en Aprobar: la ejecución termina y corre SUB 2 · Publicación", [C+"img04.png"]),
 ("7.5 Salida: publicación automática en #contenido-publicado", [C+"img05.png"]),
 ("7.6 Rechazo humano: la pieza queda en Estado Rechazado y no se publica", [C+"img07.png"]),
 ("7.7 Camino infeliz: Idea Semilla vacía → error controlado (no se llama a la IA)", [C+"img08.png"]),
 ("7.8 Error Handlers: credencial sin permiso (403) y caída real de Gemini (503) registradas y alertadas", [C+"img01.png"]),
 ("7.9 Log de Errores vinculado a Contenidos (relación entre tablas)", [C+"img09.png"]),
 ("7.10 Dashboard de control (Shared View pública “KPIs del sistema”)", [C+"img10.png"]),
]
evhtml = "<h1>7. Evidencias (capturas)</h1>" + "".join(f"<h2>{a}</h2>" + "".join(f'<p><img src="{x}" width="640"></p>' for x in imgs) for a,imgs in ev)
html = f"""<html><head><meta charset="utf-8"></head><body>
<h1>Ecosistema de Automatización IA Autónomo para Negocios</h1>
<p><b>Entrega final (intento 2)</b> · Agustina Cisneros<br>Caso de uso: pipeline de generación y publicación de contenido de marketing con IA (RAG), con aprobación humana en tiempo real antes de publicar.</p>
<h2>Enlaces</h2>
<table border="1" cellpadding="6">
<tr><td><b>Dashboard de control (Shared View)</b></td><td><a href="https://airtable.com/appCtyPCA4QGzyXR5/shr9RbSHu2YsiSJFt">https://airtable.com/appCtyPCA4QGzyXR5/shr9RbSHu2YsiSJFt</a></td></tr>
<tr><td><b>Base de datos (modo lectura)</b></td><td><a href="https://airtable.com/appCtyPCA4QGzyXR5/shrBIC22XxubHnrfF">https://airtable.com/appCtyPCA4QGzyXR5/shrBIC22XxubHnrfF</a> (vista de solo lectura de la tabla Contenidos, tablero por Estado)</td></tr>
<tr><td><b>Workflow n8n (.json)</b></td><td><a href="{WF}">{WF}</a></td></tr>
<tr><td><b>Repositorio</b></td><td><a href="{REPO}">{REPO}</a></td></tr>
<tr><td><b>Video demo (3 min)</b></td><td><a href="https://drive.google.com/file/d/1jWk3e47hR2khTUuzZeiAwceMCg9LZW8d/view?usp=sharing">https://drive.google.com/file/d/1jWk3e47hR2khTUuzZeiAwceMCg9LZW8d/view?usp=sharing</a></td></tr>
</table>
<h2>Correcciones respecto del intento 1</h2>
<ul>
<li><b>Un solo workflow con subworkflows:</b> los 3 escenarios de Make se reemplazaron por un único workflow de n8n que invoca SUB 1 Generación RAG, SUB 2 Publicación, SUB 3 Rechazo y SUB 4 Registro de errores (nodo Execute Workflow sobre el mismo workflow).</li>
<li><b>HITL con pausa real:</b> el nodo Slack “Send and Wait for Response” detiene la ejecución (estado “Esperando”) hasta que una persona aprieta Aprobar o Rechazar; recién entonces continúa.</li>
<li><b>Evidencias verificables:</b> 5 corridas reales documentadas (sección 6) con capturas (sección 7).</li>
</ul>
{''.join(parts)}
{evhtml}
</body></html>"""
pathlib.Path('/tmp/claude-0/-home-user-entrega-final/8253df89-7381-57f4-b871-296b8383ab09/scratchpad/gdoc.html').write_text(html, encoding='utf-8')
print(len(html))
