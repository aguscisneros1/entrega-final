# 5. Dashboard de control

## 5.1 Enlace público (Shared View)

> **Dashboard de control (Shared View de Airtable, vista "KPIs del sistema"):** https://airtable.com/appCtyPCA4QGzyXR5/shr9RbSHu2YsiSJFt
>
> ⚠️ Antes de entregar: abrir el link en una **ventana de incógnito**. Si pide iniciar sesión o solicitar acceso, todavía no es una Shared View.

## 5.2 KPIs que muestra

| KPI | Definición | Cómo se calcula en Airtable |
|---|---|---|
| **Tasa de aprobación** | Publicados / (Publicados + Rechazados) | Campo fórmula `KPI Aprobación` y resumen **Average** en la barra inferior |
| **Volumen de salida** | Cantidad de piezas publicadas | Campo fórmula `KPI Salida` y resumen **Sum** |
| **Tasa de error** | Registros con Estado = Error / total procesado | Campo fórmula `KPI Error` y resumen **Average** |
| Pendientes de HITL | Registros en "En revisión" | Agrupación por Estado (conteo por grupo) |
| Errores por módulo | Conteo en `Log de Errores` agrupado por Modulo | Vista agrupada de `Log de Errores` |

## 5.3 Cómo publicarlo (unidad "Cuadros de mando automáticos", Módulo 7)

1. En la tabla **Contenidos**, crear 3 campos de tipo *Formula*:
   - `KPI Aprobación` → `IF({Estado}='Publicado', 1, IF({Estado}='Rechazado', 0, BLANK()))`. Formato: porcentaje.
   - `KPI Salida` → `IF({Estado}='Publicado', 1, 0)`
   - `KPI Error` → `IF({Estado}='Error', 1, IF(OR({Estado}='Publicado', {Estado}='Rechazado'), 0, BLANK()))`. Formato: porcentaje.
2. Crear una vista **Grid** llamada `KPIs del sistema`:
   - Agrupar por **Estado**.
   - Mostrar solo: Idea Semilla, Categoria, Estado, Fecha de Aprobación, KPI Aprobación, KPI Salida, KPI Error y Errores (link).
   - En la **barra de resumen** (footer): `KPI Aprobación` → **Average** (tasa de aprobación), `KPI Salida` → **Sum** (volumen de salida), `KPI Error` → **Average** (tasa de error).
3. **Share view** → *Create a shareable link to the view* → copiar el link `https://airtable.com/app…/shr…`.
4. Opcional: hacer lo mismo en **Log de Errores**, con una vista agrupada por *Modulo*.
5. Abrir el link en incógnito y sacar una captura de los 3 KPIs para las evidencias.

## 5.4 Por qué es un panel de control y no el link a la base

- Muestra **métricas agregadas** (tasas y volumen), no filas sueltas.
- Es de **solo lectura** y no expone campos técnicos ni credenciales.
- Se actualiza solo: cada ejecución de n8n cambia el Estado, y las fórmulas y resúmenes se recalculan al instante.
