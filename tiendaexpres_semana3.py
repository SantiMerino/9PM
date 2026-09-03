"""
PEML - Key Institute | Semana 3 - Distribuciones de probabilidad
Caso TiendaExpres: decision de cajero adicional y garantia de tiempo de entrega.

Ejecutar:  python3 tiendaexpres_semana3.py
Dependencias: solo libreria estandar (math, random, statistics).
              matplotlib es opcional y solo se usa para exportar los graficos.
"""

import math
import random
import statistics as st
from collections import Counter

SEMILLA = 42  # fija la simulacion Monte Carlo para que los resultados sean reproducibles

# =====================================================================
# DATOS PROPORCIONADOS POR GERENCIA (Seccion 3 de la guia). No se modifican.
# =====================================================================

compras_completadas = [9, 9, 7, 9, 10, 7, 8, 10, 7, 8, 7, 7, 10, 9, 9,
                       8, 5, 8, 8, 9, 8, 7, 5, 9, 9, 6, 5, 4, 8, 8]
n_clientes_por_turno = 12
tasa_historica_conversion = 0.65  # 65%, dato de referencia de Gerencia

tiempos_entrega = [30, 35, 26, 32, 22, 22, 34, 29, 38, 35, 28, 30, 39, 35, 9,
                   34, 31, 37, 42, 30, 28, 36, 35, 35, 33, 34, 28, 22, 33, 27,
                   31, 31, 33, 35, 29, 28, 61, 26, 39, 34]


def titulo(texto):
    print("\n" + "=" * 68)
    print(texto)
    print("=" * 68)


# =====================================================================
# TAREA 1 - EXPLORACION DE DATOS
# =====================================================================

def descriptivos(datos, nombre, unidad=""):
    """Media, varianza y desviacion estandar. Se reportan las dos versiones:
    poblacional (divide entre N) y muestral (divide entre N-1)."""
    n = len(datos)
    media = st.mean(datos)
    var_pob, sd_pob = st.pvariance(datos), st.pstdev(datos)
    var_mue, sd_mue = st.variance(datos), st.stdev(datos)
    print(f"\n{nombre}  (n = {n})")
    print(f"  Media                  = {media:.4f} {unidad}")
    print(f"  Mediana                = {st.median(datos):.4f} {unidad}")
    print(f"  Varianza poblacional   = {var_pob:.4f}")
    print(f"  Desv. est. poblacional = {sd_pob:.4f} {unidad}")
    print(f"  Varianza muestral      = {var_mue:.4f}")
    print(f"  Desv. est. muestral    = {sd_mue:.4f} {unidad}")
    return {"n": n, "media": media, "var_pob": var_pob, "sd_pob": sd_pob,
            "var_mue": var_mue, "sd_mue": sd_mue}


titulo("TAREA 1 - EXPLORACION DE DATOS")
A = descriptivos(compras_completadas, "Dataset A - compras completadas por turno", "clientes")
B = descriptivos(tiempos_entrega, "Dataset B - tiempos de entrega", "min")

print("\nTabla de frecuencias del Dataset A:")
frec_A = Counter(compras_completadas)
for k in sorted(frec_A):
    print(f"  {k:2d} compras -> {frec_A[k]:2d} dias ({frec_A[k] / len(compras_completadas):.3f})")

print("\nDataset A: variable DISCRETA (conteo de exitos entre 12 clientes, sin valores intermedios).")
print("Dataset B: variable CONTINUA (tiempo medido en una escala real, redondeado a minutos).")

p_observada = A["media"] / n_clientes_por_turno
print(f"\nTasa de conversion observada = {A['media']:.4f}/12 = {p_observada:.4f} "
      f"(historica de Gerencia: {tasa_historica_conversion})")


# =====================================================================
# TAREA 2 - MODELO BINOMIAL (DECISION 1: CAJERO ADICIONAL)
# =====================================================================

def binom_pmf(k, n, p):
    """P(X = k) para X ~ Binomial(n, p). C(n,k) * p^k * (1-p)^(n-k)."""
    return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))


titulo("TAREA 2 - MODELO BINOMIAL  X ~ Bin(n=12, p=0.65)")

n, p = n_clientes_por_turno, tasa_historica_conversion
print("\n  k     P(X = k)")
for k in range(n + 1):
    marca = "  <-- cuenta para P(X > 8)" if k > 8 else ""
    print(f"  {k:2d}    {binom_pmf(k, n, p):.6f}{marca}")

p_teorica = sum(binom_pmf(k, n, p) for k in range(9, n + 1))
dias_criticos = sum(1 for x in compras_completadas if x > 8)
p_empirica = dias_criticos / len(compras_completadas)

print(f"\nP(X > 8) teorica  = {p_teorica:.6f}  ->  {p_teorica * 100:.2f}%")
print(f"Proporcion empirica = {dias_criticos}/{len(compras_completadas)} = "
      f"{p_empirica:.6f}  ->  {p_empirica * 100:.2f}%")
print(f"Diferencia = {(p_empirica - p_teorica) * 100:.2f} puntos porcentuales")

print(f"\nMedia teorica  n*p     = {n * p:.4f}   vs media observada    = {A['media']:.4f}")
print(f"Varianza teorica n*p*q = {n * p * (1 - p):.4f}   vs varianza observada = {A['var_pob']:.4f}")

# Intervalo de confianza del 95% para la proporcion empirica (aproximacion normal)
ee = math.sqrt(p_empirica * (1 - p_empirica) / len(compras_completadas))
ic_bajo, ic_alto = p_empirica - 1.96 * ee, p_empirica + 1.96 * ee
print(f"IC 95% de la proporcion empirica: [{ic_bajo:.4f}, {ic_alto:.4f}] "
      f"-> contiene a {p_teorica:.4f}, la diferencia no es estadisticamente significativa.")


# =====================================================================
# TAREA 3 - VERIFICACION POR SIMULACION MONTE CARLO
# =====================================================================

def simular_turnos(n_turnos, n=12, p=0.65, semilla=SEMILLA):
    """Simula n_turnos turnos. Cada turno son 12 ensayos Bernoulli independientes."""
    random.seed(semilla)
    turnos = [sum(1 for _ in range(n) if random.random() < p) for _ in range(n_turnos)]
    return turnos


titulo("TAREA 3 - SIMULACION MONTE CARLO")

print("\n  turnos      P(X > 8) simulada    error vs teorica")
resultados_sim = {}
for n_turnos in (1_000, 10_000, 100_000):
    turnos = simular_turnos(n_turnos)
    p_sim = sum(1 for x in turnos if x > 8) / n_turnos
    resultados_sim[n_turnos] = p_sim
    print(f"  {n_turnos:>7,}     {p_sim:.4f}               {abs(p_sim - p_teorica):.4f}")

turnos_10k = simular_turnos(10_000)
print(f"\nMedia de la simulacion (10,000 turnos) = {st.mean(turnos_10k):.4f} (teorica {n * p:.2f})")
print("La frecuencia simulada converge al valor teorico conforme crece el numero de turnos.")


# =====================================================================
# TAREA 4 - MODELO NORMAL Y ATIPICOS (DECISION 2: GARANTIA DE ENTREGA)
# =====================================================================

titulo("TAREA 4 - MODELO NORMAL Y VALORES ATIPICOS")


def regla_empirica(datos, etiqueta):
    media, sd = st.mean(datos), st.pstdev(datos)
    print(f"\nRegla empirica - {etiqueta} (media {media:.4f}, sigma {sd:.4f})")
    esperado = {1: 68, 2: 95, 3: 99.7}
    for k in (1, 2, 3):
        lo, hi = media - k * sd, media + k * sd
        dentro = sum(1 for x in datos if lo <= x <= hi)
        print(f"  +/-{k} sigma  [{lo:6.2f}, {hi:6.2f}]  ->  {dentro:2d}/{len(datos)} = "
              f"{dentro / len(datos) * 100:5.1f}%   (esperado {esperado[k]}%)")


regla_empirica(tiempos_entrega, "datos completos")


def cuartiles_iqr(datos):
    """Cuartiles por el metodo de la mediana de las mitades (excluyente)."""
    ordenados = sorted(datos)
    mitad = len(ordenados) // 2
    q1 = st.median(ordenados[:mitad])
    q3 = st.median(ordenados[mitad:])
    return q1, q3, q3 - q1


q1, q3, iqr = cuartiles_iqr(tiempos_entrega)
lim_inf, lim_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
atipicos = [x for x in tiempos_entrega if x < lim_inf or x > lim_sup]
tiempos_limpios = [x for x in tiempos_entrega if lim_inf <= x <= lim_sup]

print(f"\nMetodo IQR:  Q1 = {q1:.1f}   Q3 = {q3:.1f}   IQR = {iqr:.1f}")
print(f"  Limite inferior Q1 - 1.5*IQR = {lim_inf:.1f} min")
print(f"  Limite superior Q3 + 1.5*IQR = {lim_sup:.1f} min")
print(f"  Valores atipicos detectados  = {atipicos}")
print(f"  Serie depurada: n = {len(tiempos_limpios)} pedidos")

L = descriptivos(tiempos_limpios, "Dataset B depurado (sin atipicos)", "min")
regla_empirica(tiempos_limpios, "datos depurados")

# Tiempo de garantia: percentil 90 de la Normal ajustada a los datos depurados.
z90 = st.NormalDist().inv_cdf(0.90)
x_garantia = L["media"] + z90 * L["sd_pob"]
print(f"\nz para el percentil 90 = {z90:.4f}")
print(f"X = media + z*sigma = {L['media']:.4f} + {z90:.4f} * {L['sd_pob']:.4f} = {x_garantia:.4f} min")

normal_limpia = st.NormalDist(mu=L["media"], sigma=L["sd_pob"])
print("\nCumplimiento segun el valor prometido:")
for x in (37, 38, 39, 40):
    teorico = normal_limpia.cdf(x)
    emp_limpio = sum(1 for t in tiempos_limpios if t <= x) / len(tiempos_limpios)
    emp_total = sum(1 for t in tiempos_entrega if t <= x) / len(tiempos_entrega)
    print(f"  X = {x} min -> teorico {teorico * 100:5.2f}%   empirico depurado "
          f"{emp_limpio * 100:5.2f}%   empirico con atipicos {emp_total * 100:5.2f}%")

print(f"\nRecomendacion: prometer {38} minutos "
      f"(incumplimiento teorico {(1 - normal_limpia.cdf(38)) * 100:.2f}%, "
      f"real observado {sum(1 for t in tiempos_entrega if t > 38) / len(tiempos_entrega) * 100:.2f}%).")


# =====================================================================
# TAREA 5 - VISUALIZACION
# =====================================================================

def graficar():
    """Genera los graficos del reporte. Requiere matplotlib."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n[matplotlib no instalado: se omiten los graficos]")
        return

    TINTA, ACENTO, RIESGO, GRIS = "#1B2A4A", "#C8952B", "#A83A2E", "#8A8F9A"

    # Grafico 1: frecuencia observada vs modelo binomial
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ks = list(range(13))
    obs = [frec_A.get(k, 0) / len(compras_completadas) for k in ks]
    teo = [binom_pmf(k, n, p) for k in ks]
    ancho = 0.42
    ax.bar([k - ancho / 2 for k in ks], obs, ancho, color=TINTA, label="Observado (30 dias)")
    ax.bar([k + ancho / 2 for k in ks], teo, ancho, color=ACENTO, label="Binomial(12, 0.65)")
    ax.axvline(8.5, color=RIESGO, linestyle="--", linewidth=1.2)
    ax.text(8.65, max(max(obs), max(teo)) * 0.55, "X > 8", color=RIESGO, fontsize=9)
    ax.set_xlabel("Clientes que completan compra en el turno")
    ax.set_ylabel("Probabilidad / frecuencia relativa")
    ax.set_xticks(ks)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig("grafico_binomial.png", dpi=170)
    plt.close(fig)

    # Grafico 2: histograma de tiempos con curva normal ajustada
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.hist(tiempos_entrega, bins=range(5, 70, 5), density=True,
            color=TINTA, alpha=0.78, edgecolor="white")
    nd = st.NormalDist(mu=L["media"], sigma=L["sd_pob"])
    xs = [x / 2 for x in range(10, 140)]
    ax.plot(xs, [nd.pdf(x) for x in xs], color=ACENTO, linewidth=2,
            label=f"Normal({L['media']:.1f}, {L['sd_pob']:.1f})")
    ax.axvline(38, color=RIESGO, linewidth=1.6, label="Garantia propuesta: 38 min")
    for a in atipicos:
        ax.plot(a, 0.002, marker="v", color=RIESGO, markersize=8)
    ax.set_xlabel("Minutos desde la confirmacion del pedido")
    ax.set_ylabel("Densidad")
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig("grafico_normal.png", dpi=170)
    plt.close(fig)

    # Grafico 3: diagrama de caja con los limites IQR
    fig, ax = plt.subplots(figsize=(7.2, 2.4))
    # matplotlib >= 3.11 sustituye vert=False por orientation="horizontal"
    orientacion = ({"orientation": "horizontal"}
                   if tuple(int(v) for v in matplotlib.__version__.split(".")[:2]) >= (3, 11)
                   else {"vert": False})
    bp = ax.boxplot(tiempos_entrega, widths=0.5, patch_artist=True,
                    flierprops=dict(marker="o", markerfacecolor=RIESGO,
                                    markeredgecolor=RIESGO, markersize=7),
                    **orientacion)
    bp["boxes"][0].set_facecolor(TINTA)
    bp["medians"][0].set_color(ACENTO)
    bp["medians"][0].set_linewidth(2)
    ax.axvline(lim_inf, color=GRIS, linestyle=":", linewidth=1)
    ax.axvline(lim_sup, color=GRIS, linestyle=":", linewidth=1)
    ax.text(lim_inf, 1.36, f"{lim_inf:.1f}", ha="center", fontsize=8, color=GRIS)
    ax.text(lim_sup, 1.36, f"{lim_sup:.1f}", ha="center", fontsize=8, color=GRIS)
    ax.set_yticks([])
    ax.set_xlabel("Minutos")
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.tight_layout()
    fig.savefig("grafico_boxplot.png", dpi=170)
    plt.close(fig)

    # Grafico 4: convergencia de la simulacion Monte Carlo
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    random.seed(SEMILLA)
    acumulado, exitos = [], 0
    for i in range(1, 5001):
        x = sum(1 for _ in range(12) if random.random() < p)
        exitos += 1 if x > 8 else 0
        acumulado.append(exitos / i)
    ax.plot(range(1, 5001), acumulado, color=TINTA, linewidth=1)
    ax.axhline(p_teorica, color=ACENTO, linewidth=1.6,
               label=f"Valor teorico {p_teorica:.4f}")
    ax.set_xlabel("Turnos simulados")
    ax.set_ylabel("P(X > 8) acumulada")
    ax.set_ylim(0.15, 0.55)
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig("grafico_convergencia.png", dpi=170)
    plt.close(fig)

    print("\nGraficos exportados: grafico_binomial.png, grafico_normal.png, "
          "grafico_boxplot.png, grafico_convergencia.png")


titulo("TAREA 5 - VISUALIZACION")
graficar()


# =====================================================================
# TAREA 6 - RESUMEN PARA LA RECOMENDACION DE NEGOCIO
# =====================================================================

titulo("TAREA 6 - CIFRAS QUE SOSTIENEN LA RECOMENDACION")
print(f"""
DECISION 1 - Cajero adicional
  P(X > 8) teorica ................. {p_teorica * 100:.2f}%
  Proporcion empirica .............. {p_empirica * 100:.2f}% ({dias_criticos} de 30 dias)
  Simulacion (10,000 turnos) ....... {resultados_sim[10_000] * 100:.2f}%
  Lectura: la saturacion ocurre en 1 de cada 3 turnos pico.

DECISION 2 - Garantia de entrega
  Media depurada ................... {L['media']:.2f} min
  Desviacion estandar depurada ..... {L['sd_pob']:.2f} min
  Atipicos excluidos ............... {atipicos}
  Percentil 90 ..................... {x_garantia:.2f} min  ->  se promete 38 min
  Incumplimiento esperado .......... {(1 - normal_limpia.cdf(38)) * 100:.2f}%
""")
