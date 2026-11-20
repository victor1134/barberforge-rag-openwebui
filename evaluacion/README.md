# Evaluación del asistente con el Golden Dataset

## Qué mide `evaluate_rag.py`
| Métrica | Cómo se calcula |
|---|---|
| **Latencia** | Tiempo de cada llamada a `POST /api/chat/completions` de OpenWebUI (media, p50 y p95) |
| **Palabras clave** | Proporción de `palabras_clave` del CSV presentes en la respuesta (sin tildes ni mayúsculas). Pruebas «responder»: pasa con ≥ 50 %. Pruebas «negarse»: pasa con al menos una señal de negación o redirección |
| **Juez** (opcional, `--juez`) | Otro modelo de Ollama califica **fidelidad** y **completitud** de 1 a 5 contra la respuesta esperada. Pasa con promedio ≥ 4 |
| **Éxito** | La prueba pasa por palabras clave **o** por el juez. Se reporta % de éxito y % de error; la meta es ≥ 70 % |

## Requisitos
- OpenWebUI y Ollama corriendo con `docker compose up -d` (ver el README principal).
- El modelo personalizado **barberforge-soporte** creado en OpenWebUI con la Knowledge «Base BarberForge».
- Una **API key** de OpenWebUI: Settings → Account → API Keys. **No la suban a GitHub.**
- Python 3.10 o superior. Opcional: `pip install -r evaluacion/requirements.txt` para las gráficas.

## Cómo correrlo (desde la raíz del repositorio)
Windows (PowerShell):
```powershell
$env:OPENWEBUI_API_KEY = "sk-...tu clave..."
python evaluacion/evaluate_rag.py --limite 3                 # prueba rápida
python evaluacion/evaluate_rag.py --juez --etiqueta configA   # las 56 pruebas + juez
```
Mac / Linux:
```bash
export OPENWEBUI_API_KEY="sk-...tu clave..."
python3 evaluacion/evaluate_rag.py --juez --etiqueta configA
```

Opciones útiles: `--modelo` (por defecto `barberforge-soporte`), `--url` (por defecto `http://localhost:3080`),
`--ollama-url` (por defecto `http://localhost:11435`), `--juez-modelo` (por defecto `llama3.2:3b`),
`--knowledge-id` (solo si la API no está usando la Knowledge del modelo; el id sale en la URL de la Knowledge).

## Qué deja en `resultados/`
- `configA_FECHA.csv`: cada prueba con la respuesta obtenida, latencia, palabras encontradas, notas del juez y éxito.
- `configA_FECHA.json`: el resumen (éxito, error, latencias, por categoría).
- `configA_FECHA.md`: el resumen legible, con las pruebas que fallaron (para el informe).
- `configA_FECHA_categorias.png` y `..._latencia.png`: gráficas (si está matplotlib).

## Si no llega al 70 %
1. Abre el `.md` y mira qué pruebas fallaron y por qué (la respuesta obtenida está en el `.csv`).
2. Si el modelo inventó o no encontró el dato → revisar el documento de la base de conocimiento o el Top K.
3. Si no se negó cuando debía → reforzar la política correspondiente del system prompt.
4. Si la respuesta es correcta pero no tiene las palabras clave → ajustar las palabras clave del CSV (y explicarlo en el
   informe) o usar `--juez`.
5. Volver a correr con otra `--etiqueta` y comparar en el informe.
