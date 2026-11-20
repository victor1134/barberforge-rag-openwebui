# Configuración del modelo y de la estrategia RAG

## Resumen
| Decisión | Valor | Por qué |
|---|---|---|
| Modelo base | **llama3.2:3b** (Ollama) | Corre en local en PCs de 7-8 GB de RAM como los del equipo; responde bien en español; es libre. En un PC de 16 GB se puede probar llama3.1:8b y comparar. |
| Modelo de embeddings | **nomic-embed-text** (Ollama) | Liviano (≈ 270 MB), multilingüe y es el mismo que usa BarberForge en producción. |
| Divisor de texto | **Token (Tiktoken)** | La actividad pide el corte y el solapamiento en tokens. |
| Tamaño del fragmento (chunk) | **500 tokens** | Cada documento tiene entre 250 y 370 palabras (en español, ≈ 400-650 tokens): cada documento queda en 1 o 2 fragmentos y una sección completa rara vez se parte. |
| Solapamiento (overlap) | **100 tokens (20 %)** | Si una regla queda en el borde de dos fragmentos, aparece completa en los dos. |
| Top K | **4** | Trae hasta 4 fragmentos: suficiente para preguntas que mezclan temas (p. ej. precio + horario) sin llenar el contexto. |
| Temperatura | **0.2** | Respuestas estables y pegadas a la base de conocimiento; menos creatividad = menos invenciones. |
| Ventana de contexto (num_ctx) | **4096** | Cabe el system prompt + 4 fragmentos + la pregunta y la respuesta. |
| Máximo de tokens de respuesta (num_predict) | **400** | Respuestas cortas, como pide el prompt; reduce la latencia. |

## Base de conocimiento (9 documentos, carpeta `base-conocimiento/`)
| Documento | Tema | Autor |
|---|---|---|
| 01-servicios-y-precios.md | Servicios, precios, duración, pagos | Victor |
| 02-horarios-y-ubicacion.md | Horario, ubicación, atención sin cita, llegada tarde | Victor |
| 03-como-agendar-y-cancelar.md | Registro, 4 pasos para agendar, cancelar | Miyer |
| 04-recordatorios-y-confirmacion.md | Recordatorio 40 min, aviso 60 min (ML), correos | Miyer |
| 05-politicas-cancelacion-e-inasistencia.md | Cancelación, confirmación, inasistencia | Victor |
| 06-pqrs-procedimiento.md | Tipos de PQRS, canales, plazos | Miyer |
| 07-cuidado-cabello-y-barba.md | Frecuencia de corte, estilos, cuidados | Javier |
| 08-preguntas-frecuentes.md | Preguntas frecuentes | Javier |
| 09-tratamiento-de-datos.md | Ley 1581 de 2012, derechos | Victor |

## Experimento de configuración (para el informe)
Correr el Golden Dataset con dos configuraciones y comparar:
| Configuración | Chunk | Overlap | Top K | Resultado (% éxito) | Latencia media |
|---|---|---|---|---|---|
| A (principal) | 500 | 100 | 4 | **82,1 %** (46/56) | 30,47 s |
| B (fragmentos pequeños) | 250 | 50 | 4 | 75,0 % (42/56) | 30,82 s |

Se mantuvo la **A**: con fragmentos de 250 tokens bajaron el éxito y la fidelidad (detalle en la sección E.7 del
informe y en `evaluacion/resultados/`).

Para la B: cambiar Chunk Size y Overlap en Admin Panel → Settings → Documents, pulsar **Reindex** (o volver a subir
los documentos a la Knowledge) y repetir la evaluación.

## Cómo se configuró en OpenWebUI (con capturas para el informe)
1. **Admin Panel → Settings → Documents:**
   Embedding Model Engine = Ollama · Embedding Model = `nomic-embed-text` · Text Splitter = Token (Tiktoken) ·
   Chunk Size = 500 · Chunk Overlap = 100 · Top K = 4 → **Save**. *(Captura 1)*
2. **Workspace → Knowledge → +** «BarberForge» → subir los 9 archivos de `base-conocimiento/`. *(Captura 2)*
3. **Workspace → Models → +** «barberforge-soporte»: modelo base `llama3.2:3b`, System Prompt de
   `system-prompt.md`, Knowledge = «BarberForge», Advanced Params: Temperature 0.2, Context Length 4096,
   Max Tokens 400 · Capacidades → Llamada a funciones = **Heredado** → **Save**. *(Captura 3)*
   En modo «Nativa» el modelo de 3B no consultaba la base de conocimiento por sí mismo.
4. **Settings → Account → API Keys → Create new secret key** (para evaluate_rag.py; no se sube a GitHub). *(Captura 4,
   tapando la clave)*

> Los nombres exactos de los menús pueden variar un poco según la versión de OpenWebUI.
