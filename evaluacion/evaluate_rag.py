"""Evalúa el asistente «barberforge-soporte» de OpenWebUI con el Golden Dataset.

Para cada prueba de golden_dataset.csv:
  1. Envía la pregunta a la API de OpenWebUI (/api/chat/completions) y mide la LATENCIA.
  2. PALABRAS CLAVE: busca las palabras esperadas en la respuesta (sin tildes, sin mayúsculas y sin puntos de miles).
       - tipo «responder»: pasa si aparece al menos la mitad de las palabras clave.
       - tipo «negarse»:   pasa si aparece al menos una (señales de que se negó o redirigió).
  3. JUEZ (opcional, --juez): otro modelo de Ollama califica FIDELIDAD y COMPLETITUD de 1 a 5 comparando la respuesta
     con la respuesta esperada. Pasa si el promedio es 4 o más.
  4. ÉXITO de la prueba = pasa por palabras clave, o (si se usó el juez) pasa por el juez.

Al final calcula el % de éxito y de error (meta de la actividad: 70 % o más de eficiencia), la latencia media,
p50 y p95, y los resultados por categoría. Guarda todo en evaluacion/resultados/.

Uso (desde la carpeta raíz del repositorio):
    python evaluacion/evaluate_rag.py --api-key sk-xxxx                 # solo latencia y palabras clave
    python evaluacion/evaluate_rag.py --api-key sk-xxxx --juez          # + juez con llama3.2:3b
    python evaluacion/evaluate_rag.py --api-key sk-xxxx --limite 5      # prueba rápida con 5 preguntas
    python evaluacion/evaluate_rag.py --api-key sk-xxxx --etiqueta configB   # para comparar configuraciones

La clave también se puede poner en la variable de entorno OPENWEBUI_API_KEY (no la suban a GitHub).
Solo usa la biblioteca estándar de Python; si matplotlib está instalado, además dibuja las gráficas.
"""
import argparse
import csv
import json
import os
import re
import statistics
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
UMBRAL_PALABRAS = 0.5   # proporción mínima de palabras clave (tipo «responder»)
UMBRAL_JUEZ = 4.0       # promedio mínimo de fidelidad y completitud
META = 0.70             # eficiencia mínima pedida por la actividad

PROMPT_JUEZ = """Eres un evaluador estricto de un asistente de soporte de una barbería.
Compara la RESPUESTA OBTENIDA con la RESPUESTA ESPERADA para la PREGUNTA y califica de 1 a 5:
- fidelidad: la respuesta obtenida no inventa datos y no contradice la esperada (5 = totalmente fiel, 1 = inventa o contradice).
- completitud: la respuesta obtenida cubre lo esencial de la esperada (5 = completa, 1 = no responde).
Si la respuesta esperada indica que el asistente debe negarse o redirigir, calificar alto solo si se negó o redirigió.

PREGUNTA: {pregunta}
RESPUESTA ESPERADA: {esperada}
RESPUESTA OBTENIDA: {obtenida}

Responde SOLO con JSON, sin texto adicional: {{"fidelidad": n, "completitud": n, "comentario": "una frase"}}"""


# ---------- utilidades ----------

def normalizar(texto: str) -> str:
    """minúsculas, sin tildes y sin separador de miles: «$25.000» → «$25000»."""
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"(?<=\d)[.,](?=\d{3}\b)", "", texto)


def contiene(texto_norm: str, palabra: str) -> bool:
    """Palabras cortas (≤ 3 letras, p. ej. «no», «15») se buscan como palabra completa; las demás, como inicio de
    palabra, para aceptar variaciones («cancel» encuentra «cancelar» y «cancelación»)."""
    p = re.escape(normalizar(palabra.strip()))
    if len(palabra.strip()) <= 3:
        return re.search(rf"(?<![a-z0-9]){p}(?![a-z0-9])", texto_norm) is not None
    return re.search(rf"(?<![a-z0-9]){p}", texto_norm) is not None


def evaluar_palabras(respuesta: str, palabras: list[str], tipo: str) -> tuple[float, bool, list[str]]:
    texto = normalizar(respuesta)
    encontradas = [p for p in palabras if contiene(texto, p)]
    proporcion = len(encontradas) / len(palabras) if palabras else 0.0
    paso = bool(encontradas) if tipo == "negarse" else proporcion >= UMBRAL_PALABRAS
    return round(proporcion, 2), paso, encontradas


def post_json(url: str, cuerpo: dict, cabeceras: dict, timeout: int) -> dict:
    datos = json.dumps(cuerpo).encode("utf-8")
    req = urllib.request.Request(url, data=datos, headers={"Content-Type": "application/json", **cabeceras})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


# ---------- llamadas ----------

def preguntar(args, pregunta: str) -> tuple[str, float, str]:
    """Devuelve (respuesta, latencia_en_segundos, error)."""
    cuerpo = {"model": args.modelo, "messages": [{"role": "user", "content": pregunta}], "stream": False}
    if args.knowledge_id:  # por si la versión de OpenWebUI no aplica la Knowledge del modelo desde la API
        cuerpo["files"] = [{"type": "collection", "id": args.knowledge_id}]
    inicio = time.perf_counter()
    try:
        r = post_json(f"{args.url.rstrip('/')}/api/chat/completions", cuerpo,
                      {"Authorization": f"Bearer {args.api_key}"}, args.timeout)
        return r["choices"][0]["message"]["content"], round(time.perf_counter() - inicio, 2), ""
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as e:
        return "", round(time.perf_counter() - inicio, 2), f"{type(e).__name__}: {e}"


def juzgar(args, pregunta: str, esperada: str, obtenida: str) -> tuple[float | None, float | None, str]:
    cuerpo = {"model": args.juez_modelo, "stream": False, "format": "json", "options": {"temperature": 0},
              "messages": [{"role": "user", "content": PROMPT_JUEZ.format(
                  pregunta=pregunta, esperada=esperada, obtenida=obtenida or "(sin respuesta)")}]}
    try:
        r = post_json(f"{args.ollama_url.rstrip('/')}/api/chat", cuerpo, {}, args.timeout)
        nota = json.loads(r["message"]["content"])
        return float(nota["fidelidad"]), float(nota["completitud"]), str(nota.get("comentario", ""))[:200]
    except Exception as e:  # noqa: BLE001 - si el juez falla, la prueba se decide solo por palabras clave
        return None, None, f"juez no disponible: {type(e).__name__}"


# ---------- resumen ----------

def percentil(valores: list[float], p: float) -> float:
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    k = (len(ordenados) - 1) * p
    i = int(k)
    return round(ordenados[i] + (ordenados[min(i + 1, len(ordenados) - 1)] - ordenados[i]) * (k - i), 2)


def resumir(filas: list[dict], args) -> dict:
    n = len(filas)
    exitos = sum(f["exito"] for f in filas)
    latencias = [f["latencia_s"] for f in filas if not f["error"]]
    con_juez = [f for f in filas if f["fidelidad"] != ""]
    por_categoria = {}
    for f in filas:
        c = por_categoria.setdefault(f["categoria"], {"pruebas": 0, "exitos": 0})
        c["pruebas"] += 1
        c["exitos"] += f["exito"]
    for c in por_categoria.values():
        c["porcentaje_exito"] = round(100 * c["exitos"] / c["pruebas"], 1)
    return {
        "etiqueta": args.etiqueta, "fecha": datetime.now().isoformat(timespec="seconds"),
        "modelo": args.modelo, "juez": args.juez_modelo if args.juez else None, "pruebas": n,
        "exitos": exitos, "fallos": n - exitos,
        "porcentaje_exito": round(100 * exitos / n, 1) if n else 0.0,
        "porcentaje_error": round(100 * (n - exitos) / n, 1) if n else 0.0,
        "cumple_meta_70": n > 0 and exitos / n >= META,
        "exito_por_palabras_clave": round(100 * sum(f["paso_palabras"] for f in filas) / n, 1) if n else 0.0,
        "fidelidad_media": round(statistics.mean(float(f["fidelidad"]) for f in con_juez), 2) if con_juez else None,
        "completitud_media": round(statistics.mean(float(f["completitud"]) for f in con_juez), 2) if con_juez else None,
        "errores_de_api": sum(1 for f in filas if f["error"]),
        "latencia_media_s": round(statistics.mean(latencias), 2) if latencias else None,
        "latencia_p50_s": percentil(latencias, 0.5), "latencia_p95_s": percentil(latencias, 0.95),
        "por_categoria": por_categoria,
    }


def escribir_markdown(resumen: dict, filas: list[dict], ruta: Path) -> None:
    lineas = [f"# Resultados de la evaluación · {resumen['etiqueta']}", "",
              f"- Fecha: {resumen['fecha']} · Modelo: `{resumen['modelo']}` · Juez: `{resumen['juez'] or 'no usado'}`",
              f"- **Éxito: {resumen['porcentaje_exito']} %** ({resumen['exitos']} de {resumen['pruebas']}) · "
              f"Error: {resumen['porcentaje_error']} % · "
              f"Meta 70 %: {'✅ cumple' if resumen['cumple_meta_70'] else '❌ no cumple'}",
              f"- Éxito solo por palabras clave: {resumen['exito_por_palabras_clave']} %",
              f"- Fidelidad media: {resumen['fidelidad_media']} · Completitud media: {resumen['completitud_media']}",
              f"- Latencia: media {resumen['latencia_media_s']} s · p50 {resumen['latencia_p50_s']} s · "
              f"p95 {resumen['latencia_p95_s']} s · errores de API: {resumen['errores_de_api']}", "",
              "## Por categoría", "", "| Categoría | Pruebas | Éxitos | % éxito |", "|---|---|---|---|"]
    lineas += [f"| {c} | {v['pruebas']} | {v['exitos']} | {v['porcentaje_exito']} % |"
               for c, v in sorted(resumen["por_categoria"].items())]
    lineas += ["", "## Pruebas que fallaron", "", "| ID | Pregunta | Palabras encontradas | Juez (F/C) |", "|---|---|---|---|"]
    lineas += [f"| {f['id']} | {f['pregunta']} | {f['palabras_encontradas'] or '—'} | {f['fidelidad']}/{f['completitud']} |"
               for f in filas if not f["exito"]] or ["| — | Ninguna | | |"]
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def graficar(resumen: dict, filas: list[dict], base: Path) -> list[Path]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib no está instalado: no se dibujan gráficas (pip install matplotlib)")
        return []
    rutas = []
    cats = sorted(resumen["por_categoria"])
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(cats, [resumen["por_categoria"][c]["porcentaje_exito"] for c in cats], color="#2e5489")
    ax.axhline(70, color="#b3262e", linestyle="--", label="Meta 70 %")
    ax.set_ylabel("% de éxito"), ax.set_ylim(0, 105), ax.legend()
    ax.set_title(f"Éxito por categoría · total {resumen['porcentaje_exito']} %")
    plt.xticks(rotation=30, ha="right"), plt.tight_layout()
    rutas.append(base.with_name(base.name + "_categorias.png"))
    fig.savefig(rutas[-1], dpi=150), plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist([f["latencia_s"] for f in filas if not f["error"]], bins=15, color="#3f8a5c")
    ax.set_xlabel("Latencia (s)"), ax.set_ylabel("Pruebas")
    ax.set_title(f"Latencia · media {resumen['latencia_media_s']} s · p95 {resumen['latencia_p95_s']} s")
    plt.tight_layout()
    rutas.append(base.with_name(base.name + "_latencia.png"))
    fig.savefig(rutas[-1], dpi=150), plt.close(fig)
    return rutas


# ---------- programa ----------

def main() -> None:
    p = argparse.ArgumentParser(description="Evalúa el asistente RAG con el Golden Dataset")
    p.add_argument("--url", default=os.environ.get("OPENWEBUI_URL", "http://localhost:3080"))
    p.add_argument("--api-key", default=os.environ.get("OPENWEBUI_API_KEY", ""))
    p.add_argument("--modelo", default=os.environ.get("MODELO", "barberforge-soporte"))
    p.add_argument("--knowledge-id", default=os.environ.get("KNOWLEDGE_ID", ""))
    p.add_argument("--dataset", default=str(CARPETA / "golden_dataset.csv"))
    p.add_argument("--juez", action="store_true", help="califica fidelidad y completitud con un modelo de Ollama")
    p.add_argument("--juez-modelo", default=os.environ.get("JUEZ_MODELO", "llama3.2:3b"))
    p.add_argument("--ollama-url", default=os.environ.get("OLLAMA_URL", "http://localhost:11435"))
    p.add_argument("--limite", type=int, default=0, help="correr solo las primeras N pruebas")
    p.add_argument("--etiqueta", default="configA", help="nombre de la corrida, p. ej. configA o configB")
    p.add_argument("--timeout", type=int, default=180)
    args = p.parse_args()
    if not args.api_key:
        raise SystemExit("Falta la clave: --api-key sk-... o la variable OPENWEBUI_API_KEY")

    with open(args.dataset, encoding="utf-8") as f:
        pruebas = list(csv.DictReader(f))
    if args.limite:
        pruebas = pruebas[:args.limite]

    filas = []
    for i, t in enumerate(pruebas, 1):
        respuesta, latencia, error = preguntar(args, t["pregunta"])
        palabras = [x for x in t["palabras_clave"].split("|") if x.strip()]
        proporcion, paso_palabras, encontradas = evaluar_palabras(respuesta, palabras, t["tipo"])
        fidelidad = completitud = ""
        comentario = ""
        paso_juez = False
        if args.juez and not error:
            f_, c_, comentario = juzgar(args, t["pregunta"], t["respuesta_esperada"], respuesta)
            if f_ is not None:
                fidelidad, completitud = f_, c_
                paso_juez = (f_ + c_) / 2 >= UMBRAL_JUEZ
        exito = int(not error and (paso_palabras or paso_juez))
        filas.append({"id": t["id"], "categoria": t["categoria"], "tipo": t["tipo"], "pregunta": t["pregunta"],
                      "respuesta_esperada": t["respuesta_esperada"], "respuesta_obtenida": respuesta,
                      "latencia_s": latencia, "proporcion_palabras": proporcion, "paso_palabras": int(paso_palabras),
                      "palabras_encontradas": "|".join(encontradas), "fidelidad": fidelidad,
                      "completitud": completitud, "comentario_juez": comentario, "exito": exito, "error": error})
        print(f"[{i:02d}/{len(pruebas)}] {t['id']} {'✅' if exito else '❌'} {latencia:6.2f} s  "
              f"palabras {proporcion:.0%}{f'  juez {fidelidad}/{completitud}' if fidelidad != '' else ''}"
              f"{f'  ERROR {error}' if error else ''}")

    resumen = resumir(filas, args)
    salida = CARPETA / "resultados"
    salida.mkdir(exist_ok=True)
    base = salida / f"{args.etiqueta}_{datetime.now():%Y%m%d_%H%M}"
    with open(base.with_suffix(".csv"), "w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig: abre bien en Excel
        escritor = csv.DictWriter(f, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)
    base.with_suffix(".json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    escribir_markdown(resumen, filas, base.with_suffix(".md"))
    graficas = graficar(resumen, filas, base)

    print("\n" + "=" * 60)
    print(f"Éxito: {resumen['porcentaje_exito']} %  ·  Error: {resumen['porcentaje_error']} %  ·  "
          f"Meta 70 %: {'CUMPLE' if resumen['cumple_meta_70'] else 'NO CUMPLE'}")
    print(f"Latencia media {resumen['latencia_media_s']} s · p95 {resumen['latencia_p95_s']} s")
    print(f"Archivos: {base.with_suffix('.csv').name}, .json, .md" + (f" y {len(graficas)} gráficas" if graficas else ""))


if __name__ == "__main__":
    main()
