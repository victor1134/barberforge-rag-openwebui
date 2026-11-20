# G. Conclusiones y trabajos futuros

## Conclusiones
El asistente barberforge-soporte alcanzó un 82,1 % de éxito (46 de 56 pruebas) del Golden Dataset con la configuración principal (fragmentos de 500 tokens, solapamiento de 100, Top K 4), por encima de la meta del 70 %, con una fidelidad media de 4,41 y una completitud de 4,27 sobre 5. Todo se ejecutó en local con Docker, sin servicios en la nube.
El RAG es lo que hace confiable al asistente. Sin la base de conocimiento, el éxito medido por palabras clave fue de apenas 44,6 % y el modelo inventó datos (un precio para el tinte o cortes a domicilio, que la barbería no ofrece). Con RAG subió a 71,4 % y la fidelidad pasó de 3,82 a 4,41. Además, actualizar un precio o un horario solo requiere editar un documento, sin reentrenar el modelo.
El prompt del sistema con políticas explícitas funcionó. Con la configuración A, las categorías de seguridad (intentos de inyección de prompt), datos personales y fuera de alcance tuvieron 100 % de éxito: el asistente no entregó datos de otros clientes, no dio consejos médicos y no aceptó cambiar sus reglas.
El tamaño del fragmento importa. Con fragmentos de 250/50 tokens el éxito bajó a 75,0 % y la fidelidad a 4,11: la información de un mismo tema quedaba repartida y no siempre llegaba completa al modelo. Por eso se mantuvo 500/100.
El punto más débil son las PQRS (50 % de éxito): ante una queja, el modelo a veces muestra empatía pero no menciona el plazo de 15 días hábiles o el canal para radicarla. También falló en preguntas cortas o ambiguas, donde prefirió pedir más detalles.
El costo del RAG es la latencia: unos 30 segundos por respuesta en promedio, frente a 19 sin RAG, porque el modelo procesa los fragmentos recuperados en equipos sin GPU.


## Lo que aprendió cada integrante
- **Eli:** Eli: levantar Ollama y OpenWebUI con Docker Compose y configurar el RAG (embeddings, fragmentos, Top K) y el modelo personalizado. Aprendió que la memoria del equipo limita el modelo que se puede usar y que un detalle de configuración, como la llamada a funciones en «Nativa» o «Heredado», decide si el modelo consulta o no los documentos.


- **Victor:** escribir documentos pensados para que un modelo los recupere bien (secciones cortas, un tema por documento, datos exactos) y coordinar un trabajo en equipo con ramas, commits y un repositorio compartido.


- **Miyer:** diseñar un Golden Dataset que cubra tanto lo que el asistente debe responder como lo que debe negarse a hacer, y evaluar respuestas desde la interfaz revisando las fuentes que cita el modelo.


- **Javier:** automatizar la evaluación por API, combinar métricas objetivas (palabras clave, latencia) con un modelo juez, y descubrir que la API de OpenWebUI no aplica el RAG sola si no se envía la colección en la petición.

## Dificultades
Recursos de los equipos. Con 7-8 GB de RAM hubo que usar un modelo de 3B parámetros. En uno de los equipos, con otros contenedores encendidos, el modelo bajó a 0,01 tokens por segundo y las peticiones superaban el tiempo límite; hubo que apagar los demás servicios y correr la evaluación en un equipo con más capacidad.
El RAG no se aplicaba por la API. Las primeras pruebas por API respondían precios inventados porque solo llegaban la pregunta y el prompt (127 tokens de entrada). Se resolvió enviando la colección en el campo files de cada petición y dejando la llamada a funciones del modelo en «Heredado».
Sensibilidad a las tildes. La misma pregunta sin tildes no recuperaba la tabla de precios.
Medir la calidad no es trivial. Las palabras clave castigan respuestas correctas redactadas de otra forma, y el modelo juez de 3B fue indulgente con respuestas que sonaban bien aunque inventaran datos (por eso el 80,4 % sin RAG está inflado). Se usaron las dos métricas juntas.
Cambiar el tamaño de fragmento exige reindexar. Los documentos ya cargados no se vuelven a cortar solos: hay que reindexar o subirlos de nuevo a la base de conocimiento.

## Trabajos futuros
Mejorar las respuestas de PQRS: reforzar el documento 06 y el prompt para que siempre incluyan canal, datos necesarios y plazo, y repetir la evaluación.

Integrar el asistente en la plataforma BarberForge y conectar el flujo de PQRS para que se radique desde el chat con número de radicado.

Ampliar el Golden Dataset con preguntas reales de clientes (incluidas preguntas sin tildes) y medir también la calidad de la recuperación, es decir, qué fragmentos trae para cada pregunta.

Probar un modelo más grande (llama3.1:8b) en un equipo con GPU, búsqueda híbrida (BM25 + embeddings) y un juez más estricto, y comparar fidelidad y latencia.

Atender por WhatsApp, que es el canal que más usan los clientes.
