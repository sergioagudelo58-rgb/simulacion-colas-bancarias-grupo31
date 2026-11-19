"""
Corre los 4 escenarios x 10 réplicas y guarda todo en Excel y CSV.

Uso (desde la carpeta raíz del proyecto):
    python src/experimentos.py
"""
import os
import sys
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from banco import ESCENARIOS, DURACION, simular_dia, valores_teoricos

REPLICAS = 10
SEMILLA_BASE = 42          # réplica r usa la semilla 42 + r (la misma en todos los escenarios)
CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resultados")


def ic95(x):
    """Media e intervalo de confianza del 95 % (t de Student)."""
    x = np.asarray(x, dtype=float)
    m, s, n = x.mean(), x.std(ddof=1), len(x)
    h = stats.t.ppf(0.975, n - 1) * s / np.sqrt(n)
    return m, s, m - h, m + h


def resumir(df, por, col):
    """Promedio por réplica y luego media, DE e IC 95 % entre las 10 réplicas."""
    por_rep = df.groupby(por + ["replica"])[col].mean().reset_index()
    filas = []
    for clave, g in por_rep.groupby(por):
        m, s, lo, hi = ic95(g[col])
        clave = clave if isinstance(clave, tuple) else (clave,)
        filas.append(dict(zip(por, clave)) | {"media": m, "de": s, "ic95_inf": lo, "ic95_sup": hi})
    return pd.DataFrame(filas)


def correr():
    os.makedirs(CARPETA, exist_ok=True)
    registros, cajeros = [], []
    for esc, cajas in ESCENARIOS.items():
        for r in range(1, REPLICAS + 1):
            semilla = SEMILLA_BASE + r
            dia = simular_dia(cajas, semilla)
            df = pd.DataFrame(dia)
            df.insert(0, "replica", r)
            df.insert(0, "escenario", esc)
            registros.append(df)
            cierre = max(DURACION, df["fin"].max())
            for i, caja in enumerate(cajas, start=1):
                d = df[df["cajero"] == i]
                cajeros.append({"escenario": esc, "replica": r, "semilla": semilla, "cajero": i,
                                "tipo_caja": caja, "clientes": len(d),
                                "atencion_prom": d["servicio"].mean(),
                                "espera_prom": d["espera"].mean(),
                                "espera_max": d["espera"].max(),
                                "utilizacion": d["servicio"].sum() / cierre})
        print(f"{esc}: {REPLICAS} réplicas listas")

    clientes = pd.concat(registros, ignore_index=True)
    por_cajero = pd.DataFrame(cajeros)

    # Totales de usuarios por tipo en cada réplica (Punto 3)
    usuarios = (clientes.groupby(["escenario", "replica", "accion", "tipo_usuario"])
                .size().rename("usuarios").reset_index())

    # Valores teóricos M/M/1
    teorico = pd.concat([pd.DataFrame(valores_teoricos(c)).assign(escenario=e)
                         for e, c in ESCENARIOS.items()], ignore_index=True)

    # Resúmenes con IC 95 %
    res_atencion = resumir(clientes, ["escenario", "cajero"], "servicio")        # Punto 1
    res_espera_esc = resumir(clientes, ["escenario"], "espera")                  # Puntos 4 y 5
    res_espera_tipo = resumir(clientes, ["escenario", "accion", "tipo_usuario"], "espera")

    clientes.to_csv(os.path.join(CARPETA, "clientes.csv"), index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(os.path.join(CARPETA, "resultados_simulacion_banco.xlsx")) as xl:
        clientes.round(4).to_excel(xl, sheet_name="clientes", index=False)
        por_cajero.round(4).to_excel(xl, sheet_name="por_cajero_replica", index=False)
        usuarios.to_excel(xl, sheet_name="usuarios_por_replica", index=False)
        res_atencion.round(4).to_excel(xl, sheet_name="atencion_por_cajero", index=False)
        res_espera_esc.round(4).to_excel(xl, sheet_name="espera_por_escenario", index=False)
        res_espera_tipo.round(4).to_excel(xl, sheet_name="espera_por_tipo", index=False)
        teorico.round(4).to_excel(xl, sheet_name="teorico_MM1", index=False)

    # Resumen rápido en pantalla
    pd.set_option("display.width", 200)
    print("\nEspera promedio por escenario (min):")
    print(res_espera_esc.round(3).to_string(index=False))
    print("\nUtilización promedio por cajero:")
    print(por_cajero.groupby(["escenario", "cajero", "tipo_caja"])["utilizacion"].mean()
          .round(3).to_string())
    print(f"\nClientes simulados: {len(clientes)} | Archivos guardados en resultados/")
    return clientes


if __name__ == "__main__":
    correr()
