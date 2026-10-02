"""Genera entrega/Entrega-Final-Agustina-Cisneros.html a partir de docs/*.md (luego se imprime a PDF)."""
import base64, pathlib, re, markdown
root = pathlib.Path(__file__).resolve().parents[2]
img = lambda p: "data:image/png;base64," + base64.b64encode((root / p).read_bytes()).decode()
parts = []
for md in sorted((root / "docs").glob("0*.md")):
    t = md.read_text(encoding="utf-8")
    t = re.sub(r"```mermaid.*?```", f'<img class="full" src="{img("entrega/img/diagrama-arquitectura.png")}">', t, flags=re.S)
    t = re.sub(r"\]\((\.\./)?(workflow|entrega|docs)/[^)]*\)", "]", t)  # links relativos → texto
    t = re.sub(r"\[([^\]]+)\](?!\()", r"\1", t)
    if md.name.startswith("06"):
        t += f'\n\n### Captura: workflow importado en n8n (flujo principal y subworkflows)\n\n<img class="full" src="{img("entrega/img/workflow-n8n-canvas.png")}">\n'
    parts.append('<section>' + markdown.markdown(t, extensions=["tables", "fenced_code"]) + '</section>')
html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Entrega Final</title><style>
@page {{ size: A4; margin: 16mm 14mm; }}
body {{ font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 10.5pt; color:#111827; line-height:1.45; }}
h1 {{ font-size: 19pt; color:#1d4ed8; border-bottom:2px solid #1d4ed8; padding-bottom:4px; }}
h2 {{ font-size: 13.5pt; color:#1e3a8a; margin-top:18px; }} h3 {{ font-size: 11.5pt; }}
table {{ border-collapse: collapse; width:100%; margin:8px 0; font-size:9pt; page-break-inside:auto; }}
th, td {{ border:1px solid #d1d5db; padding:4px 6px; vertical-align:top; text-align:left; }} th {{ background:#eff6ff; }}
pre {{ background:#f3f4f6; padding:8px; font-size:8.3pt; white-space:pre-wrap; word-break:break-word; border-radius:4px; }}
code {{ font-size: 9pt; }} blockquote {{ border-left:4px solid #f59e0b; background:#fffbeb; margin:8px 0; padding:6px 10px; }}
section {{ page-break-before: always; }} .full {{ width:100%; border:1px solid #e5e7eb; }}
.cover h1 {{ font-size: 24pt; border:none; margin-top:60px; }} .cover td {{ font-size:10pt; }}
</style></head><body>
<div class="cover">
<h1>Ecosistema de Automatización IA Autónomo para Negocios</h1>
<p><b>Entrega final (intento 2)</b> · Agustina Cisneros<br>Caso de uso: pipeline de generación y publicación de contenido con IA (RAG), con aprobación humana en tiempo real.</p>
<table>
<tr><th>Orquestador</th><td>n8n: <b>un solo workflow</b> con 4 subworkflows internos (Execute Workflow → mismo workflow)</td></tr>
<tr><th>Base de datos</th><td>Airtable: Contenidos ⇄ Log de Errores (vinculadas) y Manual de Marca (RAG)</td></tr>
<tr><th>IA</th><td>Google Gemini con RAG y prompt dinámico (se puede cambiar por Claude u OpenAI)</td></tr>
<tr><th>Salida</th><td>Slack: aprobación HITL con botones, publicación y respuestas en hilo (thread_ts)</td></tr>
</table>
<h2>Enlaces</h2>
<table>
<tr><th>Workflow n8n (.json)</th><td>https://github.com/aguscisneros1/entrega-final/blob/claude/ia-automation-unified-workflow-iuscap/workflow/ecosistema-contenido-ia.n8n.json</td></tr>
<tr><th>Repositorio</th><td>https://github.com/aguscisneros1/entrega-final/tree/claude/ia-automation-unified-workflow-iuscap</td></tr>
<tr><th>Dashboard de control (Shared View)</th><td>https://airtable.com/appCtyPCA4QGzyXR5/shr9RbSHu2YsiSJFt</td></tr>
<tr><th>Base de datos (lectura)</th><td>https://airtable.com/appCtyPCA4QGzyXR5/shrBIC22XxubHnrfF</td></tr>
<tr><th>Video demo (3 min)</th><td>https://drive.google.com/file/d/1jWk3e47hR2khTUuzZeiAwceMCg9LZW8d/view?usp=sharing</td></tr>
</table>
<h2>Correcciones respecto del intento 1</h2>
<ul>
<li><b>Un solo workflow con subworkflows</b>: los 3 escenarios de Make se reemplazaron por un único workflow de n8n que invoca SUB 1 Generación RAG, SUB 2 Publicación, SUB 3 Rechazo y SUB 4 Registro de errores.</li>
<li><b>HITL con pausa real</b>: el nodo Slack <i>Send and Wait for Response</i> detiene la ejecución (estado <i>Waiting</i>) hasta que una persona aprieta Aprobar o Rechazar. Recién ahí continúa.</li>
<li><b>Repositorio completo</b>: el workflow, las instrucciones de ejecución, la documentación de los 5 criterios, el plan de pruebas y las evidencias.</li>
</ul>
</div>
{''.join(parts)}
</body></html>"""
(root / "entrega/src/Entrega-Final.html").write_text(html, encoding="utf-8")
