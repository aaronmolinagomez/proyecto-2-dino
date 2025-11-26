# Dino de Google - POO + Programacion Dinamica

## Ejecucion recomendada (sin fast, para resultados finales)
- Agente DP (100 episodios, headless, sin limite bajo de tiempo):  
  `python main.py --mode agent --episodes 100 --headless --max_time 9999 --save_csv results100/agent.csv`
- Baseline aleatorio (100 episodios):  
  `python main.py --mode random --episodes 100 --headless --max_time 9999 --save_csv results100/random.csv`
- Baseline humano (jugar manual, abre ventana):  
  `python main.py --mode human --episodes 100 --save_csv results100/human.csv`

## Graficas
- Linea por episodio (color opcional):  
  `python plot_line.py --csv results100/agent.csv --out results100_v2/line_agent.png --color blue`  
  `python plot_line.py --csv results100/random.csv --out results100_v2/line_random.png --color red`  
  `python plot_line.py --csv results100/human.csv --out results100_v2/line_human.png --color green`
- Comparacion de puntajes (lineas y medias agente/aleatorio):  
  `python plot_results.py --agent_csv results100/agent.csv --random_csv results100/random.csv --out results100_v2/scores.png`
- Comparacion agente vs aleatorio vs humano:  
  `python plot_compare_lines.py --agent_csv results100/agent.csv --random_csv results100/random.csv --human_csv results100/human.csv --out results100_v2/lines_compare.png`

## Diseno del agente (PD online)
- Estado discreto: (y, vy, duck, obstaculos cercanos (x,y,w,h,kind)), acciones {NONE, JUMP, DUCK, STAND}.
- Politica: busqueda DP recursiva con memoizacion sobre estado discretizado; recompensa = supervivencia + progreso; penalizacion fuerte por colision; descuento gamma.
- Juego: modos human/agent/random; dificultad con ramp-up de velocidad y spawns agrupados; warmup sin obstaculos.
- Se removio la iteracion de valor (VI) para simplificar; la DP online es el agente entregado.

## Resultados actuales (100 episodios, sin fast)
- Agente DP: media 3387.1, mediana 2688.8, min 656.2, max 7179.1.
- Humano: media 2972.4, mediana 2981.7, min 554.0, max 6249.7.
- Aleatorio: media 822.6, mediana 724.4, min 548.1, max 1603.5.
Archivos en `results100/` (CSV) y graficas en `results100_v2/`.

## Notas
- `--fast` acelera la simulacion pero se uso sin fast para los resultados finales.
- Si quieres rapidez en pruebas, agrega `--fast` y reduce `--max_time`; para reportes finales usa los comandos de arriba.
