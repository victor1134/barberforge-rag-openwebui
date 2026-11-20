# BarberForge · Asistente de soporte y PQRS con RAG (OpenWebUI + Ollama)

**Actividad 2 · Módulo 6 · Servicio de IA generativa para proyecto (grupal)** · Diplomado CloudForge AI 5.0 · Unicomfacauca

Asistente de IA generativa **local** que atiende a los clientes de la barbería **BarberForge Popayán**: responde sobre
servicios, precios, horarios, cómo agendar y cancelar, recordatorios, políticas, tratamiento de datos, PQRS y cuidado del
cabello y la barba. Usa **RAG** (Retrieval-Augmented Generation): antes de responder busca en una base de conocimiento
de 9 documentos de la barbería, y un **system prompt** con políticas le impide inventar datos, dar consejos médicos o
entregar datos de otras personas.

Proyecto principal: BarberForge AI (plataforma de agenda con IA), del que se toman los datos de la barbería.

## Cómo está armado
| Pieza | Valor |
|---|---|
| Interfaz y RAG | OpenWebUI (`http://localhost:3080`) |
| Modelo base | `llama3.2:3b` en Ollama (local) |
| Embeddings | `nomic-embed-text` |
| Corte / solapamiento | **500 tokens / 100 tokens** (divisor por tokens, Top K = 4) |
| Modelo personalizado | `barberforge-soporte` (system prompt + Knowledge «Base BarberForge», temperatura 0.2) |
| Evaluación | Golden Dataset de **56 pruebas** + `evaluate_rag.py` (latencia, palabras clave y juez 1-5) |

## Estructura
```
base-conocimiento/   9 documentos .md de la barbería (la Knowledge de OpenWebUI)
modelo/              system-prompt.md y configuracion.md (decisiones del modelo y del RAG)
evaluacion/          golden_dataset.csv, evaluate_rag.py y resultados/
evidencias/          capturas de la interfaz, la configuración y la API
informe/             Informe-modelo-rag-BarberForge.pdf y sus secciones
docker-compose.yml   Ollama + OpenWebUI
```

## Cómo correrlo
```bash
docker compose up -d
docker compose exec ollama ollama pull llama3.2:3b
docker compose exec ollama ollama pull nomic-embed-text
```
1. Abrir `http://localhost:3080` y crear la cuenta de administrador (la primera que se registra).
2. Configurar el RAG, la Knowledge y el modelo como dice `modelo/configuracion.md`.
3. Crear una API key y correr la evaluación como dice `evaluacion/README.md`:
   `python evaluacion/evaluate_rag.py --juez`

## Resultados
| Configuración | Chunk / overlap | % éxito | % error | Latencia media | Fidelidad / completitud |
|---|---|---|---|---|---|
| A (principal) | 500 / 100 | _completar_ | _completar_ | _completar_ | _completar_ |
| B (comparación) | 250 / 50 | _completar_ | _completar_ | _completar_ | _completar_ |

Meta de la actividad: **≥ 70 % de eficiencia**. Detalle en `evaluacion/resultados/` y en el informe.

## Aportes de cada integrante
| Integrante | GitHub | Aporte |
|---|---|---|
| Victor | @victor1134 | Coordinación y repositorio; documentos 01 (servicios y precios), 02 (horarios), 05 (políticas) y 09 (datos personales); README; secciones A, B, C, D y G del informe y consolidación del PDF |
| Eli Rebolledo | @Eli-rebolledo | Infraestructura (docker-compose con Ollama y OpenWebUI); configuración del RAG (embeddings, chunk, overlap, Top K); modelo personalizado y system prompt con sus políticas; sección E del informe |
| Miyer | @MiyerACI | Golden Dataset de 56 pruebas; documentos 03 (agendar y cancelar), 04 (recordatorios) y 06 (PQRS); pruebas y evidencias desde la interfaz; sección F (pruebas en interfaz) |
| Javier | @JavierGalindez | Script `evaluate_rag.py` (latencia, palabras clave, juez); ejecución del Golden Dataset y comparación de configuraciones; pruebas por API y de seguridad; documentos 07 (cuidado) y 08 (preguntas frecuentes); sección F (resultados) |

## Uso de IA
Parte de los documentos, el script y los borradores del informe se generaron con ayuda de un asistente de IA (Claude) y
fueron revisados, ajustados y probados por el equipo.
