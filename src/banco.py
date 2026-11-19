"""
Simulación del Banco de Colombia: 3 (o 4) cajeros, cada uno es una cola M/M/1 independiente.

Cómo funciona un día simulado:
  1. Llega un cliente. Se decide si hace RETIRO (70 %) o PAGO (30 %) y qué tipo de
     usuario es (rápido, normal, lento o muy lento) según la Tabla 2.
  2. El cliente se manda a uno de los cajeros que atienden su operación, elegido al azar.
     Cada cajero tiene su propia fila (el cliente no se cambia de fila).
  3. Si el cajero está libre lo atiende de inmediato; si no, espera su turno (primero
     en llegar, primero en ser atendido).
  4. El tiempo de servicio y el tiempo hasta la siguiente llegada son exponenciales con
     las medias de la Tabla 1.
  5. Las puertas se cierran a los 480 minutos (8 horas); los que ya estaban adentro
     se atienden hasta terminar.
"""
import numpy as np

TIPOS = ["Rápido", "Normal", "Lento", "Muy lento"]

# Tabla 1: medias en minutos [Rápido, Normal, Lento, Muy lento]
SERVICIO = {"Retiro": [1, 2, 3, 4], "Pago": [3, 3, 5, 7]}
LLEGADA = {"Retiro": [1, 2, 3, 3], "Pago": [1, 2, 3, 4]}

# Tabla 2: probabilidad de cada tipo de usuario dentro de cada operación
PROB_TIPO = {"Retiro": [0.23, 0.40, 0.17, 0.20], "Pago": [0.10, 0.20, 0.30, 0.40]}
PROB_RETIRO = 0.70

DURACION = 480  # minutos (8 horas)

# Escenarios: qué operación atiende cada cajero ("Mixta" = ambas)
ESCENARIOS = {
    "E1_3_mixtas": ["Mixta", "Mixta", "Mixta"],
    "E2_1Retiro_2Pagos": ["Retiro", "Pago", "Pago"],
    "E3_2Retiros_1Pago": ["Retiro", "Retiro", "Pago"],
    "E4_4_mixtas": ["Mixta", "Mixta", "Mixta", "Mixta"],
}


def nuevo_cliente(rng):
    """Decide la operación y el tipo de usuario del cliente que llega."""
    accion = "Retiro" if rng.random() < PROB_RETIRO else "Pago"
    tipo = rng.choice(4, p=PROB_TIPO[accion])
    return accion, tipo


def simular_dia(cajas, semilla):
    """Simula un día completo. Devuelve una lista con un registro por cliente."""
    rng = np.random.default_rng(semilla)
    libre_desde = [0.0] * len(cajas)          # momento en que cada cajero queda libre
    clientes = []
    t = 0.0
    accion, tipo = nuevo_cliente(rng)
    t += rng.exponential(LLEGADA[accion][tipo])  # llegada del primer cliente

    while t <= DURACION:
        # cajeros que pueden atender esta operación
        posibles = [i for i, c in enumerate(cajas) if c in ("Mixta", accion)]
        cajero = int(rng.choice(posibles))

        servicio = rng.exponential(SERVICIO[accion][tipo])
        inicio = max(t, libre_desde[cajero])       # espera si el cajero está ocupado
        fin = inicio + servicio
        libre_desde[cajero] = fin

        clientes.append({
            "cajero": cajero + 1,
            "tipo_caja": cajas[cajero],
            "accion": accion,
            "tipo_usuario": TIPOS[tipo],
            "llegada": t,
            "inicio": inicio,
            "fin": fin,
            "espera": inicio - t,
            "servicio": servicio,
            "tiempo_sistema": fin - t,
        })

        # siguiente cliente
        accion, tipo = nuevo_cliente(rng)
        t += rng.exponential(LLEGADA[accion][tipo])
    return clientes


def valores_teoricos(cajas):
    """Valores esperados de M/M/1 para cada cajero, usando las medias de las tablas.
    Sirve para comparar con lo simulado (λ, μ, ρ, Lq, Wq, L, W)."""
    # tiempo medio entre llegadas y de servicio de un cliente cualquiera
    t_lleg = sum(p_a * sum(p * m for p, m in zip(PROB_TIPO[a], LLEGADA[a]))
                 for a, p_a in (("Retiro", PROB_RETIRO), ("Pago", 1 - PROB_RETIRO)))
    lam_total = 1 / t_lleg
    filas = []
    for i, caja in enumerate(cajas):
        lam = 0.0
        serv = 0.0
        for a, p_a in (("Retiro", PROB_RETIRO), ("Pago", 1 - PROB_RETIRO)):
            if caja in ("Mixta", a):
                n = sum(1 for c in cajas if c in ("Mixta", a))     # cajeros que comparten
                lam_a = lam_total * p_a / n
                lam += lam_a
                serv += lam_a * sum(p * m for p, m in zip(PROB_TIPO[a], SERVICIO[a]))
        es = serv / lam                    # servicio medio en ese cajero
        mu = 1 / es
        rho = lam / mu
        wq = rho / (mu - lam) if rho < 1 else float("inf")
        filas.append({"cajero": i + 1, "tipo_caja": caja, "lambda": lam, "mu": mu, "rho": rho,
                      "Lq": lam * wq, "Wq": wq, "W": wq + es, "L": lam * (wq + es)})
    return filas
