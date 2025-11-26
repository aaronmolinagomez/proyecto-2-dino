import argparse
import csv
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import statistics as stats


def read_scores(path: Path) -> Tuple[List[float], List[float]]:
    scores, durations = [], []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            scores.append(float(row["score"]))
            durations.append(float(row["duration_sec"]))
    return scores, durations


def describe(name: str, scores: List[float]):
    print(f"{name}: n={len(scores)}, mean={stats.mean(scores):.2f}, median={stats.median(scores):.2f}, min={min(scores):.2f}, max={max(scores):.2f}")


def main():
    parser = argparse.ArgumentParser(description="Grafica resultados de Dino")
    parser.add_argument("--agent_csv", type=Path, required=True, help="CSV de puntajes del agente DP")
    parser.add_argument("--random_csv", type=Path, required=True, help="CSV de puntajes del baseline aleatorio")
    parser.add_argument("--human_csv", type=Path, default=None, help="CSV de puntajes de humano (opcional)")
    parser.add_argument("--out", type=Path, default=Path("scores.png"), help="Ruta de salida de la imagen")
    args = parser.parse_args()

    agent_scores, _ = read_scores(args.agent_csv)
    random_scores, _ = read_scores(args.random_csv)
    human_scores = []
    if args.human_csv:
        human_scores, _ = read_scores(args.human_csv)

    describe("Agente DP", agent_scores)
    describe("Aleatorio", random_scores)
    if human_scores:
        describe("Humano", human_scores)

    fig, ax = plt.subplots(figsize=(9, 5))
    line_kwargs = dict(linewidth=1.2, markersize=4, alpha=0.8)

    episodes_agent = list(range(1, len(agent_scores) + 1))
    ax.plot(episodes_agent, agent_scores, marker="o", label="Agente DP", color="blue", **line_kwargs)
    ax.axhline(stats.mean(agent_scores), color="blue", linestyle="--", alpha=0.6, label="Media agente")

    episodes_random = list(range(1, len(random_scores) + 1))
    ax.plot(episodes_random, random_scores, marker="o", label="Aleatorio", color="red", **line_kwargs)
    ax.axhline(stats.mean(random_scores), color="red", linestyle="--", alpha=0.6, label="Media aleatorio")

    if human_scores:
        episodes_human = list(range(1, len(human_scores) + 1))
        ax.plot(episodes_human, human_scores, marker="o", label="Humano", color="green", **line_kwargs)
        ax.axhline(stats.mean(human_scores), color="green", linestyle="--", alpha=0.6, label="Media humano")

    ax.set_xlabel("Episodio")
    ax.set_ylabel("Puntaje")
    ax.set_title("Comparacion de puntajes por episodio")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.out, dpi=150)
    print(f"Grafico guardado en {args.out}")


if __name__ == "__main__":
    main()
