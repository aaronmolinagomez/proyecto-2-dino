# Dino de Google - POO + Programación Dinámica

## Cómo ejecutar
- Jugar humano: python main.py --mode human
- Agente DP (headless, 10 eps, semilla fija): python main.py --mode agent --episodes 10 --headless --seed 1 --save_csv agent.csv
- Baseline aleatorio: python main.py --mode random --episodes 10 --headless --seed 1 --save_csv random.csv
- Graficar comparación (requiere matplotlib): python plot_results.py --agent_csv agent.csv --random_csv random.csv --out scores.png

## Diseño
- Entidades POO: Player (física salto/duck), Obstacle/ObstacleManager (spawns con ramp-up de dificultad), DPAgent (backup Bellman con memoización y discretización), Game (loop/render/UI), RandomPolicy (baseline).
- MDP/estado para DP: (y, vy, duck, obstáculos cercanos (x,y,w,h,kind)). Acciones: NONE, JUMP, DUCK, STAND. Recompensa: supervivencia + progreso; colisión penalizada; descuento gamma.
- Dificultad: warmup sin obstáculos, gaps largos al inicio, velocidad con rampa suave.

## Resultados sugeridos
1) Corre 10+ episodios para agente y aleatorio (headless) con la misma semilla y guarda CSV.
2) Usa plot_results.py para generar boxplot scores.png y reporta estadísticas (media/mediana/máx/mín) impresas por el script.
3) Opcional: registra una corrida humana y compara puntaje promedio.

## Mejoras posibles
- Sprites y sonido para mayor fidelidad.
- Ajustar horizonte y discretización del DP para mayor performance en secuencias mixtas.
- Añadir modo pausa/reset en Game si se necesita para demos.
