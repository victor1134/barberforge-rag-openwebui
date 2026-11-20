# F. Implementación y análisis de pruebas

## F2. Pruebas por API y resultados con el Golden Dataset

### F2.1 Prueba unitaria por API

El modelo personalizado `barberforge-soporte` se consultó por la API compatible con OpenAI de OpenWebUI
(`POST http://localhost:3080/api/chat/completions`), autenticando con una API key (`sk-...`) y usando `curl.exe`
desde PowerShell.

**Hallazgo técnico importante:** en la versión de OpenWebUI usada, una petición por API al modelo personalizado
**no ejecutaba el RAG automáticamente**, aunque el modelo tenía la base de conocimiento asociada:

| Prueba | Tokens de entrada | Respuesta a «¿Cuánto cuesta un corte clásico?» |
|---|---|---|
| Solo el modelo (sin enviar la colección) | 127 | **$15.000 COP** (inventado) |
| Enviando la colección en el campo `files` | 1.618 | **$25.000 COP** (correcto, con 4 fuentes citadas) |

Los 127 tokens de entrada mostraron que al modelo solo le llegaban la pregunta y el prompt del sistema, sin
fragmentos de los documentos. La solución fue enviar la colección en cada petición:

    "files": [{"type": "collection", "id": "be8df739-47a4-4d85-b599-bf1dc28735c5"}]

También se observó que **las tildes afectan la búsqueda semántica**: con la pregunta sin tildes
(«Cuanto cuesta un corte clasico») no se recuperaba la tabla de precios; con tildes sí.

Otro ajuste necesario fue configurar la **Llamada a funciones** del modelo en **«Heredado»**: en modo **«Nativa»** el
modelo de 3B no consultaba la base de conocimiento por sí mismo.

*Evidencia: `evidencias/api-01-curl.png`*

### F2.2 Metodología de evaluación

- **Golden Dataset:** 56 pruebas en 10 categorías (`evaluacion/golden_dataset.csv`), cada una con pregunta,
  respuesta esperada, palabras clave y tipo («responder» o «negarse»).
- **Script:** `evaluacion/evaluate_rag.py` envía cada pregunta a la API con la colección (`--knowledge-id`) y mide:
  - **Latencia** de cada respuesta (media, p50 y p95).
  - **Palabras clave**: sin tildes, sin mayúsculas y sin puntos de miles. Una prueba de tipo «responder» pasa con al
    menos la mitad de las palabras; una de tipo «negarse», con al menos una.
  - **Juez** (`llama3.2:3b`): califica **fidelidad** y **completitud** de 1 a 5. Pasa con un promedio ≥ 4.
- **Éxito de una prueba:** pasa por palabras clave **o** por el juez.
- **Eficiencia = éxitos / 56 × 100**; **% de error = 100 − eficiencia**. Meta de la actividad: **≥ 70 %**.

Se hicieron tres corridas:

| Corrida | Descripción |
|---|---|
| **sinRAG** | Sin enviar la colección: el modelo responde solo con el prompt del sistema (línea base) |
| **configA** | Con RAG · fragmentos de **500 tokens**, superposición de **100**, Top K 4 |
| **configB** | Con RAG · fragmentos de **250 tokens**, superposición de **50**, Top K 4 |

### F2.3 Resultados globales

| Métrica | sinRAG | **configA (500/100)** | configB (250/50) |
|---|---|---|---|
| Éxito total | 80,4 % (45/56) | **82,1 % (46/56)** | 75,0 % (42/56) |
| % de error | 19,6 % | **17,9 %** | 25,0 % |
| Meta 70 % | Cumple* | **Cumple** | Cumple |
| **Éxito solo por palabras clave** | 44,6 % | **71,4 %** | 62,5 % |
| Fidelidad media (1-5) | 3,82 | **4,41** | 4,11 |
| Completitud media (1-5) | 3,96 | **4,27** | 4,04 |
| Latencia media | 18,88 s | 30,47 s | 30,82 s |
| Latencia p50 | 18,23 s | 28,16 s | 26,94 s |
| Latencia p95 | 36,00 s | **47,16 s** | 58,64 s |
| Errores de API | 0 | 0 | 0 |

\* *El 80,4 % sin RAG está inflado por el juez (ver F2.5).*

*Evidencias: `evidencias/api-02-evaluacion-consola.png` (configA) y `evidencias/api-03-evaluacion-configB.png`
(configB). Detalle por prueba en `evaluacion/resultados/`.*

### F2.4 Resultados por categoría (% de éxito)

| Categoría | Pruebas | sinRAG | configA | configB |
|---|---|---|---|---|
| servicios | 8 | 87,5 % | 87,5 % | 87,5 % |
| horarios | 5 | 80,0 % | 80,0 % | 60,0 % |
| agendar | 7 | 85,7 % | 71,4 % | 71,4 % |
| recordatorios | 5 | 80,0 % | 60,0 % | 80,0 % |
| políticas | 5 | 60,0 % | **100,0 %** | 80,0 % |
| pqrs | 8 | 62,5 % | 50,0 % | 37,5 % |
| datos | 3 | 100,0 % | 100,0 % | 100,0 % |
| cuidado | 5 | 100,0 % | 100,0 % | 80,0 % |
| fuera de alcance | 6 | 66,7 % | **100,0 %** | 83,3 % |
| seguridad | 4 | 100,0 % | 100,0 % | 100,0 % |

### F2.5 Análisis

**1. El RAG mejora de forma real la precisión.** El % de éxito total apenas cambia entre sinRAG y configA
(80,4 % → 82,1 %), pero las métricas que no dependen del juez muestran la diferencia:
- El éxito por palabras clave sube de **44,6 % a 71,4 %** (+26,8 puntos).
- La fidelidad sube de **3,82 a 4,41**: el modelo deja de inventar.

Sin RAG, el modelo inventaba servicios y precios que no existen (por ejemplo «Arreglado básico $15.000,
Arreglado completo $25.000, Arreglado premium $40.000»). Con RAG responde con el catálogo real (Corte clásico
$25.000, Barba perfilada $18.000, Combo $40.000, Tratamiento capilar $35.000).

**2. El juez de 3B es demasiado permisivo.** Como el éxito se cuenta si pasa por palabras clave **o** por el juez,
y el juez es el mismo modelo pequeño (`llama3.2:3b`), aprobó respuestas con datos inventados. Por eso la corrida sin
RAG llegó al 80,4 %. La métrica más confiable de este informe es el **éxito por palabras clave junto con la fidelidad**.

**3. El RAG también mejora las negativas.** En «fuera de alcance» se pasa de 66,7 % a 100 %, y en «políticas» de 60 %
a 100 %: con el contexto, el modelo reconoce lo que la barbería no ofrece (tintes, domicilio, pagos anticipados)
en vez de inventar.

**4. Costo en latencia.** El RAG aumenta la latencia media de 18,9 s a 30,5 s (+61 %), porque el modelo procesa
~1.600 tokens de entrada en lugar de ~130. Es una latencia alta para un chat en tiempo real, debida a que el modelo
corre en CPU.

**5. Fragmentos de 500/100 son mejores que 250/50.** configB bajó en todas las métricas de calidad (−7,1 puntos de
éxito, −8,9 en palabras clave, fidelidad 4,41 → 4,11) y empeoró el p95 de latencia (47 s → 59 s). Razones:
- Con Top K = 4, configB entrega la mitad de contexto (~1.000 tokens contra ~2.000).
- Los fragmentos pequeños separan filas de tablas de sus encabezados y preguntas frecuentes de sus respuestas.
  Por eso fallaron en B preguntas simples que en A estaban bien, como P09 (horario) y P14 (cómo agendar).
- La única categoría que mejoró fue «recordatorios» (60 % → 80 %), porque su información está en párrafos cortos.

**Configuración elegida: fragmentos de 500 tokens con superposición de 100.**

### F2.6 Pruebas que fallan siempre

Estas pruebas fallaron tanto en configA como en configB, así que no dependen del tamaño del fragmento:

| ID | Pregunta | Causa probable |
|---|---|---|
| P07 | ¿El fade cuesta más que un corte normal? | Requiere inferir que el precio es el mismo para cualquier estilo |
| P12 | ¿A qué hora es la última cita para un corte? | Requiere calcular (cierre 5:00 p. m. − duración del corte) |
| P18 | ¿Por qué no me aparecen horas disponibles? | Respuesta con varias causas repartidas en distintos documentos |
| P23 | ¿Por qué me llegaron dos correos antes de mi cita? | Dato muy específico (aviso a 60 min + recordatorio a 40 min) |
| P32, P33, P34, P38 | Quejas, reclamos, garantía y tiempos de PQRS | El procedimiento de PQRS tiene muchos pasos y el modelo de 3B no los sigue completos |

**PQRS es la categoría más débil** (50 % en configA) y es el principal punto de mejora: reorganizar el documento
de PQRS con una sección corta por tipo de solicitud y reforzar en el prompt del sistema los pasos que el asistente
debe seguir.