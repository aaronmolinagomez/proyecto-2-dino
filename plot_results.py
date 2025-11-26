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
    parser.add_argument("--out", type=Path, default=Path("scores.png"), help="Ruta de salida de la imagen")
    args = parser.parse_args()

    agent_scores, _ = read_scores(args.agent_csv)
    random_scores, _ = read_scores(args.random_csv)

    describe("Agente DP", agent_scores)
    describe("Aleatorio", random_scores)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.boxplot([agent_scores, random_scores], labels=["Agente DP", "Aleatorio"], showmeans=True)
    ax.set_ylabel("Puntaje")
    ax.set_title("Comparacion de puntajes por episodio")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(args.out, dpi=150)
    print(f"Grafico guardado en {args.out}")


if __name__ == "__main__":
    main()
