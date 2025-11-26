# Dino de Google - POO + Programacion Dinamica

## Como ejecutar
- Humano: `python main.py --mode human`
- Agente DP: `python main.py --mode agent --episodes 10 --headless --seed 1 --max_time 30 --save_csv agent.csv`
- Baseline aleatorio: `python main.py --mode random --episodes 10 --headless --seed 1 --max_time 30 --save_csv random.csv`
- Graficar comparacion (requiere matplotlib): `python plot_results.py --agent_csv agent.csv --random_csv random.csv --out scores.png`

## Diseno
- Entidades POO: Player (fisica salto/duck), Obstacle/ObstacleManager (spawns con ramp-up de dificultad y clusters bajos), DPAgent (backup Bellman con memoizacion y discretizacion), Game (loop/render/UI), RandomPolicy (baseline).
- MDP del agente: estado (y, vy, duck, obstaculos cercanos (x,y,w,h,kind)); acciones {NONE, JUMP, DUCK, STAND}; recompensa = supervivencia + progreso, penalizacion por colision, descuento gamma.
- Dificultad: warmup sin obstaculos, gaps largos al inicio, velocidad con rampa suave, clusters de bajos (1-3), voladores alto/bajo.

## Resultados sugeridos
1) Corre 10+ episodios para agente y aleatorio (headless) con la misma semilla y guarda CSV.
2) Usa `plot_results.py` para generar boxplot `scores.png` y reporta estadisticas (media/mediana/max/min).
3) Opcional: registra una corrida humana y compara puntaje promedio.

## Recoleccion de datos automatizada
Para recolectar y graficar en un paso, usa `bench.py` (headless, con semilla). Modo rapido `--fast` evita limitar FPS (recomendado para muchos episodios):
```
python bench.py --episodes 50 --seed 1 --max_time 15 --fast --out_dir results
```
Genera:
- `results/agent.csv` y `results/random.csv`
- `results/summary.json` con estadisticas (mean/median/min/max)
- `results/scores.png` (boxplot) salvo que pases `--no_plot`.

## Mejoras posibles
- Sprites y sonido para mayor fidelidad.
- Ajustar horizonte y discretizacion del DP para mayor performance en secuencias mixtas.
- Anadir modo pausa/reset en Game si se necesita para demos.
