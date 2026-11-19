"""
Puntos 1, 2 y 3 del problema bancario (resultados descriptivos).

Lee resultados/clientes.csv (generado por src/experimentos.py) y produce:
  resultados/p1_atencion_por_cajero.csv   Punto 1: atención por cajero (media, DE, mín, máx, IC 95 %)
  resultados/p1_pruebas.csv               Punto 1: ¿difieren los cajeros? (ANOVA y Kruskal-Wallis)
  resultados/p2_usuarios_por_tipo.csv     Punto 2: usuarios promedio por tipo (total y por cajero)
  resultados/p3_usuarios_por_replica.csv  Punto 3: total de usuarios por tipo en cada réplica
  figuras/fig_p1_atencion_cajeros.png     Punto 1: barras con IC 95 % (300 dpi)
  figuras/fig_p2_usuarios_tipo.png        Punto 2: barras con IC 95 % y valor esperado (300 dpi)
  figuras/fig_p3_usuarios_replica.png     Punto 3: mapa de calor réplica x tipo (300 dpi)

Uso (desde la carpeta raíz del proyecto, después de src/experimentos.py):
    python src/analisis_puntos_1_3.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from matplotlib.lines import Line2D
from scipy import stats

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DIR_RES = os.path.join(RAIZ, "resultados")
DIR_FIG = os.path.join(RAIZ, "figuras")
os.makedirs(DIR_FIG, exist_ok=True)

ESC = ["E1_3_mixtas", "E2_1Retiro_2Pagos", "E3_2Retiros_1Pago", "E4_4_mixtas"]
ETQ_ESC = {"E1_3_mixtas": "E1: 3 mixtas", "E2_1Retiro_2Pagos": "E2: 1 retiro + 2 pagos",
           "E3_2Retiros_1Pago": "E3: 2 retiros + 1 pago", "E4_4_mixtas": "E4: 4 mixtas"}
TIPOS = ["Rápido", "Normal", "Lento", "Muy lento"]
ACCIONES = ["Retiro", "Pago"]
COLOR = {"Mixta": "#2a78d6", "Retiro": "#eb6834", "Pago": "#1baf7a"}

# Datos de las tablas del enunciado (para el número esperado de usuarios)
PROB_TIPO = {"Retiro": [0.23, 0.40, 0.17, 0.20], "Pago": [0.10, 0.20, 0.30, 0.40]}
LLEGADA = {"Retiro": [1, 2, 3, 3], "Pago": [1, 2, 3, 4]}
P_ACCION = {"Retiro": 0.70, "Pago": 0.30}
DURACION = 480

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#8a8a8a", "axes.labelcolor": "#333333",
                     "xtick.color": "#555555", "ytick.color": "#555555"})


def ic95(x):
    """Media, DE, mínimo, máximo e IC 95 % con t de Student."""
    x = np.asarray(x, dtype=float)
    n, m, s = len(x), x.mean(), x.std(ddof=1)
    h = stats.t.ppf(0.975, n - 1) * s / np.sqrt(n)
    return {"n": n, "media": m, "de": s, "minimo": x.min(), "maximo": x.max(),
            "ic95_inf": m - h, "ic95_sup": m + h}


d = pd.read_csv(os.path.join(DIR_RES, "clientes.csv"))
d["tipo_usuario"] = pd.Categorical(d["tipo_usuario"], TIPOS, ordered=True)
d["accion"] = pd.Categorical(d["accion"], ACCIONES, ordered=True)

# ---------------------------------------------------------------------------
# PUNTO 1. Tiempo promedio de atención (servicio) por cajero
# Unidad de análisis: el promedio de cada cajero en cada réplica (10 valores por cajero).
# ---------------------------------------------------------------------------
por_rep = (d.groupby(["escenario", "cajero", "tipo_caja", "replica"], observed=True)
           .agg(atencion=("servicio", "mean"), sistema=("tiempo_sistema", "mean"),
                clientes=("servicio", "size")).reset_index())
filas = []
for (e, c, t), g in por_rep.groupby(["escenario", "cajero", "tipo_caja"]):
    fila = {"escenario": e, "cajero": c, "tipo_caja": t,
            "clientes_prom": g["clientes"].mean()}
    fila |= ic95(g["atencion"])
    fila["sistema_prom"] = g["sistema"].mean()
    filas.append(fila)
p1 = pd.DataFrame(filas)
p1.to_csv(os.path.join(DIR_RES, "p1_atencion_por_cajero.csv"), index=False, encoding="utf-8-sig")

pruebas = []
for e, g in por_rep.groupby("escenario"):
    grupos = [x["atencion"].to_numpy() for _, x in g.groupby("cajero")]
    lento = p1[p1.escenario == e].sort_values("media")
    pruebas.append({"escenario": e,
                    "cajero_menor": int(lento.iloc[0].cajero), "media_menor": lento.iloc[0].media,
                    "cajero_mayor": int(lento.iloc[-1].cajero), "media_mayor": lento.iloc[-1].media,
                    "anova_F": stats.f_oneway(*grupos).statistic,
                    "anova_p": stats.f_oneway(*grupos).pvalue,
                    "kruskal_H": stats.kruskal(*grupos).statistic,
                    "kruskal_p": stats.kruskal(*grupos).pvalue})
p1_pruebas = pd.DataFrame(pruebas)
p1_pruebas.to_csv(os.path.join(DIR_RES, "p1_pruebas.csv"), index=False, encoding="utf-8-sig")

# Figura P1: barras por cajero, agrupadas por escenario, con IC 95 %
fig, ax = plt.subplots(figsize=(9, 4.6))
x0, ancho, xt, xl = 0.0, 0.8, [], []
for e in ESC:
    sub = p1[p1.escenario == e].sort_values("cajero")
    k = len(sub)
    xs = x0 + np.arange(k) * ancho
    for xi, (_, r) in zip(xs, sub.iterrows()):
        ax.bar(xi, r.media, width=ancho * 0.86, color=COLOR[r.tipo_caja], zorder=2)
        ax.errorbar(xi, r.media, yerr=[[r.media - r.ic95_inf], [r.ic95_sup - r.media]],
                    fmt="none", ecolor="#333333", elinewidth=1.2, capsize=3, zorder=3)
        ax.text(xi, 0.12, f"C{int(r.cajero)}", ha="center", va="bottom", fontsize=8,
                color="white", fontweight="bold", zorder=4)
    xt.append(xs.mean()); xl.append(ETQ_ESC[e])
    x0 = xs[-1] + ancho * 1.8
ax.set_xticks(xt, xl)
ax.set_ylabel("Tiempo promedio de atención (min)")
ax.set_xlabel("Escenario (C = cajero)")
ax.set_title("Tiempo promedio de atención por cajero (media de 10 réplicas, IC 95 %)", fontsize=11)
ax.grid(axis="y", color="#e5e5e5", zorder=0)
ax.legend(handles=[Patch(color=COLOR[k], label=f"Caja {k.lower()}") for k in COLOR] +
          [Line2D([], [], color="#333333", marker="_", markersize=10, lw=1.2, label="IC 95 %")],
          loc="upper right", frameon=False, fontsize=8, ncol=4)
ax.set_ylim(0, 6.6)
fig.tight_layout()
fig.savefig(os.path.join(DIR_FIG, "fig_p1_atencion_cajeros.png"), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# PUNTO 2. Promedio de usuarios de cada tipo en la totalidad de cajeros
# Se cuentan los usuarios de cada tipo en cada réplica (todos los cajeros juntos)
# y se promedian las 10 réplicas.
# ---------------------------------------------------------------------------
conteo = (d.groupby(["escenario", "replica", "accion", "tipo_usuario"], observed=False)
          .size().rename("usuarios").reset_index())
t_lleg = sum(P_ACCION[a] * sum(p * m for p, m in zip(PROB_TIPO[a], LLEGADA[a])) for a in ACCIONES)
llegadas_esperadas = DURACION / t_lleg
n_cajeros = d.groupby("escenario")["cajero"].max().to_dict()
filas = []
for (e, a, t), g in conteo.groupby(["escenario", "accion", "tipo_usuario"], observed=True):
    esperado = llegadas_esperadas * P_ACCION[a] * PROB_TIPO[a][TIPOS.index(t)]
    total_rep = conteo[(conteo.escenario == e)].groupby("replica")["usuarios"].sum()
    fila = {"escenario": e, "accion": a, "tipo_usuario": t}
    fila |= ic95(g["usuarios"])
    fila["por_cajero"] = fila["media"] / n_cajeros[e]
    fila["porcentaje_obs"] = 100 * g["usuarios"].sum() / total_rep.sum()
    fila["porcentaje_teo"] = 100 * P_ACCION[a] * PROB_TIPO[a][TIPOS.index(t)]
    fila["esperado"] = esperado
    filas.append(fila)
p2 = pd.DataFrame(filas)
p2.to_csv(os.path.join(DIR_RES, "p2_usuarios_por_tipo.csv"), index=False, encoding="utf-8-sig")

# Prueba chi-cuadrado de bondad de ajuste de las proporciones (E1, todas las réplicas)
obs = conteo[conteo.escenario == "E1_3_mixtas"].groupby(["accion", "tipo_usuario"],
                                                       observed=True)["usuarios"].sum()
prop = np.array([P_ACCION[a] * PROB_TIPO[a][TIPOS.index(t)] for a, t in obs.index])
chi2 = stats.chisquare(obs.to_numpy(), prop * obs.sum())

# Figura P2 (escenario E1, situación actual)
e1 = p2[p2.escenario == "E1_3_mixtas"]
fig, ax = plt.subplots(figsize=(8, 4.4))
w = 0.38
for j, a in enumerate(ACCIONES):
    s = e1[e1.accion == a].set_index("tipo_usuario").loc[TIPOS]
    xs = np.arange(4) + (j - 0.5) * w
    ax.bar(xs, s["media"], width=w * 0.92, color=COLOR[a], zorder=2, label=a)
    ax.errorbar(xs, s["media"], yerr=[s["media"] - s["ic95_inf"], s["ic95_sup"] - s["media"]],
                fmt="none", ecolor="#333333", elinewidth=1.2, capsize=3, zorder=3)
    ax.scatter(xs, s["esperado"], marker="D", s=30, color="white", edgecolor="#333333",
               zorder=4)
    for xi, v in zip(xs, s["media"]):
        ax.text(xi, v + (s["ic95_sup"] - s["media"]).max() + 1.2, f"{v:.1f}", ha="center",
                fontsize=8, color="#333333")
ax.set_xticks(np.arange(4), TIPOS)
ax.set_xlabel("Tipo de usuario")
ax.set_ylabel("Usuarios por día (promedio de 10 réplicas)")
ax.set_title("Usuarios promedio por tipo en el total de cajeros (E1, IC 95 %)", fontsize=11)
ax.grid(axis="y", color="#e5e5e5", zorder=0)
ax.legend(handles=[Patch(color=COLOR["Retiro"], label="Retiro"),
                   Patch(color=COLOR["Pago"], label="Pago"),
                   Line2D([], [], marker="D", ls="", mfc="white", mec="#333333",
                          label="Valor esperado (tablas 1 y 2)"),
                   Line2D([], [], color="#333333", marker="_", markersize=10, lw=1.2,
                          label="IC 95 %")],
          loc="upper right", frameon=False, fontsize=8)
ax.set_ylim(0, 75)
fig.tight_layout()
fig.savefig(os.path.join(DIR_FIG, "fig_p2_usuarios_tipo.png"), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# PUNTO 3. Total de usuarios de cada tipo en cada réplica
# ---------------------------------------------------------------------------
tabla = conteo.pivot_table(index=["escenario", "replica"], columns=["accion", "tipo_usuario"],
                           values="usuarios", aggfunc="sum", observed=False).astype(int)
tabla.columns = [f"{a} - {t}" for a, t in tabla.columns]
tabla["Total retiros"] = tabla.filter(like="Retiro").sum(axis=1)
tabla["Total pagos"] = tabla.filter(like="Pago -").sum(axis=1)
tabla["Total"] = tabla["Total retiros"] + tabla["Total pagos"]
tabla = tabla.reset_index()
tabla.insert(2, "semilla", tabla["replica"] + 42)
tabla.to_csv(os.path.join(DIR_RES, "p3_usuarios_por_replica.csv"), index=False, encoding="utf-8-sig")

# Figura P3: mapa de calor del escenario E1 (filas = réplicas, columnas = tipos)
t1 = tabla[tabla.escenario == "E1_3_mixtas"].set_index("replica")
cols = [f"{a} - {t}" for a in ACCIONES for t in TIPOS]
M = t1[cols].to_numpy()
# cada columna se escala a su propio rango para que el color compare réplicas
Z = (M - M.min(0)) / (M.max(0) - M.min(0))
fig, ax = plt.subplots(figsize=(9.5, 5.2))
from matplotlib.colors import LinearSegmentedColormap
cmap = LinearSegmentedColormap.from_list("azul", ["#e6f0fc", "#86b6ef", "#2a78d6", "#104281"])
ax.imshow(Z, cmap=cmap, aspect="auto", vmin=0, vmax=1)
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        ax.text(j, i, int(M[i, j]), ha="center", va="center", fontsize=9,
                color="white" if Z[i, j] > 0.55 else "#1a1a1a")
for j in range(M.shape[1]):
    i = int(np.argmin(M[:, j]))
    ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, ec="#eb6834", lw=2.2))
ax.set_xticks(range(len(cols)), [c.replace(" - ", "\n") for c in cols], fontsize=8.5)
ax.set_yticks(range(M.shape[0]), [f"R{r} (s={r + 42})" for r in t1.index], fontsize=8.5)
ax.set_xlabel("Operación y tipo de usuario")
ax.set_ylabel("Réplica (semilla)")
ax.set_title("Total de usuarios por tipo en cada réplica (E1). Recuadro: mínimo de cada tipo",
             fontsize=11)
for s in ax.spines.values():
    s.set_visible(False)
ax.axvline(3.5, color="white", lw=3)
fig.tight_layout()
fig.savefig(os.path.join(DIR_FIG, "fig_p3_usuarios_replica.png"), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# ¿Bastan 10 réplicas? Error relativo ER = ME / media y réplicas necesarias
# n = n0 × (ER / ER_objetivo)², con n0 = 10 (algoritmo de la Semana 7)
# ---------------------------------------------------------------------------
e1d = d[d.escenario == "E1_3_mixtas"]
metricas = {f"Atención cajero {c} (min)": g.groupby("replica")["servicio"].mean()
            for c, g in e1d.groupby("cajero")}
metricas["Usuarios totales por día"] = e1d.groupby("replica").size()
metricas["Retiros por día"] = e1d[e1d.accion == "Retiro"].groupby("replica").size()
metricas["Pagos por día"] = e1d[e1d.accion == "Pago"].groupby("replica").size()
metricas["Espera promedio (min)"] = e1d.groupby("replica")["espera"].mean()
filas = []
for nombre, x in metricas.items():
    r = ic95(x)
    me = r["ic95_sup"] - r["media"]
    er = 100 * me / r["media"]
    filas.append({"metrica": nombre, "media": r["media"], "margen_error": me,
                  "error_relativo_pct": er,
                  "replicas_para_10pct": int(np.ceil(10 * (er / 10) ** 2)),
                  "replicas_para_5pct": int(np.ceil(10 * (er / 5) ** 2))})
replicas = pd.DataFrame(filas)
replicas.to_csv(os.path.join(DIR_RES, "replicas_necesarias.csv"), index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------------------
# Resumen en pantalla
# ---------------------------------------------------------------------------
pd.set_option("display.width", 220)
print("PUNTO 1 - Atención por cajero (min)")
print(p1[["escenario", "cajero", "tipo_caja", "media", "de", "ic95_inf", "ic95_sup"]]
      .round(3).to_string(index=False))
print(p1_pruebas.round(4).to_string(index=False))
print("\nPUNTO 2 - Usuarios por tipo (E1)")
print(e1[["accion", "tipo_usuario", "media", "de", "ic95_inf", "ic95_sup", "por_cajero",
          "porcentaje_obs", "porcentaje_teo", "esperado"]].round(2).to_string(index=False))
print(f"Llegadas esperadas por día: {llegadas_esperadas:.1f}; "
      f"chi-cuadrado E1: {chi2.statistic:.2f}, p = {chi2.pvalue:.4f}")
print("\nPUNTO 3 - Usuarios por réplica (E1)")
print(t1.drop(columns=["escenario", "semilla"]).to_string())
print("\nRÉPLICAS NECESARIAS (E1)")
print(replicas.round(2).to_string(index=False))
