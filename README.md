# Simulación de colas bancarias — Banco de Colombia (M/M/1)

Simulación de eventos discretos de los cajeros del Banco de Colombia para decidir cuántas cajas
deben atender exclusivamente pagos y cuántas retiros, y si hace falta un cajero adicional.

Actividad didáctica 2-M3 — Simulación, IU Digital de Antioquia. Grupo 31:
Gilliam Argel Monterroza, Leydi Correa Herrera, Sergio Andrés Agudelo Marulanda, Arley Steven Franco Galeano.

## Estructura

```
├── src/
│   ├── banco.py          # Modelo: datos de las tablas, simulación de un día y valores teóricos M/M/1
│   └── experimentos.py   # 4 escenarios x 10 réplicas -> Excel y CSV
├── resultados/
│   ├── resultados_simulacion_banco.xlsx   # todas las tablas (ver hojas abajo)
│   ├── clientes.csv                       # un registro por cliente atendido
│   └── ejecucion.png                      # captura de la terminal (evidencia de ejecución)
├── figuras/              # gráficas del análisis
└── requirements.txt
```

## Instalación y ejecución

```bash
git clone https://github.com/sergioagudelo58-rgb/simulacion-colas-bancarias-grupo31.git
cd simulacion-colas-bancarias-grupo31
pip install -r requirements.txt
python src/experimentos.py
```

### Evidencia de ejecución

Captura de la terminal al ejecutar `python src/experimentos.py`:

![Evidencia de ejecución](resultados/ejecucion.png)

## Datos del modelo

| Operación | Tipo de usuario | Probabilidad | Media de servicio (min) | Media de llegada (min) |
|---|---|---|---|---|
| Retiro (70 %) | Rápido | 0.23 | 1 | 1 |
| | Normal | 0.40 | 2 | 2 |
| | Lento | 0.17 | 3 | 3 |
| | Muy lento | 0.20 | 4 | 3 |
| Pago (30 %) | Rápido | 0.10 | 3 | 1 |
| | Normal | 0.20 | 3 | 2 |
| | Lento | 0.30 | 5 | 3 |
| | Muy lento | 0.40 | 7 | 4 |

## Supuestos

1. Cada cajero es una cola M/M/1 independiente, con su propia fila y disciplina FIFO.
2. Al llegar, se sortea la operación (70 % retiro, 30 % pago) y el tipo de usuario (Tabla 2).
3. El tiempo hasta la siguiente llegada es exponencial con la media del tipo de cliente que llega (Tabla 1).
4. El cliente se asigna al azar, con igual probabilidad, a uno de los cajeros que atienden su operación.
5. El tiempo de servicio es exponencial con la media de su operación y tipo de usuario (Tabla 1).
6. El banco recibe clientes durante 480 minutos (8 horas); quienes ya están en fila se atienden hasta terminar.
7. La atención es inmediata cuando el cajero está libre y el desplazamiento es despreciable.

## Escenarios y réplicas

| Escenario | Cajeros |
|---|---|
| E1 | 3 cajas mixtas (situación actual) |
| E2 | 1 caja de retiros + 2 cajas de pagos |
| E3 | 2 cajas de retiros + 1 caja de pagos |
| E4 | 4 cajas mixtas (evaluar un cajero adicional) |

10 réplicas por escenario; la réplica r usa la semilla `42 + r` (43 a 52), la misma en todos los escenarios.

## Hojas del Excel de resultados

| Hoja | Contenido | Punto |
|---|---|---|
| `clientes` | Un registro por cliente: escenario, réplica, cajero, operación, tipo, llegada, espera, servicio | Todos |
| `por_cajero_replica` | Clientes, atención promedio, espera promedio y máxima, utilización por cajero y réplica | 1, 4 |
| `atencion_por_cajero` | Tiempo de atención por cajero: media, DE e IC 95 % | 1 |
| `usuarios_por_replica` | Total de usuarios de cada tipo en cada réplica | 2, 3 |
| `espera_por_escenario` | Espera promedio por escenario con IC 95 % | 4, 5 |
| `espera_por_tipo` | Espera promedio por escenario, operación y tipo de usuario | 4, 5 |
| `teorico_MM1` | λ, μ, ρ, Lq, Wq, W y L teóricos de cada cajero | Metodología |

## Reproducibilidad

Con las mismas semillas, ejecutar el script varias veces produce resultados idénticos.
Entorno probado: Python 3.13, numpy 2.5, pandas 3.0, scipy 1.18, openpyxl 3.1.
