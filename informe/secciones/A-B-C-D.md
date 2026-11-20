# A. Portada
**Informe: modelo de IA generativa con RAG para BarberForge**
Asistente de soporte y PQRS de BarberForge Popayán
Actividad 2 · Módulo 6 · Servicio de IA generativa para proyecto (grupal)
Diplomado CloudForge AI 5.0 · Docente: Diego Fernando Rivera Vásquez
Integrantes: Elizabeth rebolledo, Victor campo, Miyer cuetia, Javier guaca
Unicomfacauca · Popayán, noviembre 19 de 2026
Repositorio: https://github.com/victor1134/barberforge-rag-openwebui

# B. Índice
Este documento describe el diseño, la implementación y la evaluación de un asistente de inteligencia artificial generativa para la barbería BarberForge Popayán, construido con la estrategia RAG (Retrieval-Augmented Generation) sobre OpenWebUI y Ollama, ejecutándose completamente en local.

El asistente se apoya en una base de conocimiento de nueve documentos de la barbería (servicios, precios, horarios, agendamiento, recordatorios, políticas, PQRS, cuidado y tratamiento de datos) y en un prompt de sistema con políticas que delimitan su comportamiento. Para medir su calidad se construyó un Golden Dataset de 56 pruebas y un script que mide latencia, presencia de palabras clave y una calificación de fidelidad y completitud con un modelo juez. Con la configuración elegida (fragmentos de 500 tokens con solapamiento de 100) el asistente alcanzó un 82,1 % de éxito, por encima de la meta del 70 %.

El informe presenta el problema que resuelve (sección D), las decisiones de diseño del modelo (E), las pruebas desde la interfaz y la API con sus resultados (F) y las conclusiones y trabajos futuros (G).

# C. Introducción
Este documento describe el diseño, la implementación y la evaluación de un asistente de inteligencia artificial
generativa para la barbería BarberForge Popayán, construido con la estrategia RAG (Retrieval-Augmented Generation) sobre
OpenWebUI y Ollama, ejecutándose completamente en local.

El asistente se apoya en una base de conocimiento de nueve documentos de la barbería (servicios, precios, horarios,
agendamiento, recordatorios, políticas, PQRS, cuidado y tratamiento de datos) y en un prompt de sistema con políticas
que delimitan su comportamiento. Para medir su calidad se construyó un Golden Dataset de 56 pruebas y un script que
mide latencia, presencia de palabras clave y una calificación de fidelidad y completitud con un modelo juez.

El informe presenta el problema que resuelve (sección D), las decisiones de diseño del modelo (E), las pruebas desde la
interfaz y la API con sus resultados (F) y las conclusiones y trabajos futuros (G).

# D. Problema que resuelve
BarberForge es una plataforma de agenda en línea para barberías que ya permite agendar, cancelar y recibir
recordatorios por correo. Sin embargo, los clientes siguen teniendo dudas que hoy se resuelven por teléfono o en el
local: cuánto cuesta un servicio, si abren los domingos, cómo cancelar, por qué llegaron dos correos antes de la cita,
qué pasa si no confirman o cómo poner una queja. Atender esas preguntas quita tiempo a los barberos y, fuera del
horario, nadie las responde.

**Servicio propuesto:** un asistente de soporte disponible 24/7 que responde esas preguntas en lenguaje natural usando
**solo la información oficial de la barbería** y que guía al cliente en el procedimiento de **PQRS** (peticiones, quejas,
reclamos y sugerencias), con los canales, los datos necesarios y el plazo de respuesta de 15 días hábiles.

**Por qué con RAG y no solo con un modelo de lenguaje:** un modelo sin contexto inventaría precios, horarios y
políticas. Con RAG, cada respuesta se basa en los documentos de la barbería; si el dato cambia, basta con actualizar
el documento, sin reentrenar el modelo.

**Límites definidos desde el diseño:** el asistente informa, pero no agenda, no cancela ni radica PQRS (eso se hace en
la plataforma o por los canales oficiales); no da consejos médicos y no entrega datos personales de otras personas
(Ley 1581 de 2012).

**Usuarios:** clientes registrados, visitantes que aún no tienen cuenta y el personal de la barbería, que puede
remitir a los clientes al asistente.
