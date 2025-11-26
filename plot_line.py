import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


def read_scores(csv_path: Path):
    scores = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            scores.append(float(row["score"]))
    return scores


def plot_line(scores, out: Path, color: str = "blue"):
    episodes = list(range(1, len(scores) + 1))
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(episodes, scores, marker="o", linewidth=1.2, markersize=4, alpha=0.8, color=color)
    ax.set_xlabel("Episodio")
    ax.set_ylabel("Puntaje")
    ax.set_title("Puntaje por episodio")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    print(f"Grafico guardado en {out}")


def main():
    parser = argparse.ArgumentParser(description="Grafico de linea de puntajes por episodio")
    parser.add_argument("--csv", type=Path, required=True, help="CSV con columna 'score'")
    parser.add_argument("--out", type=Path, default=Path("line_scores.png"), help="Ruta de salida del grafico")
    parser.add_argument("--color", type=str, default="blue", help="Color de la linea (ej: blue, red, green)")
    args = parser.parse_args()

    scores = read_scores(args.csv)
    if not scores:
        print("No se encontraron puntajes en el CSV")
        return
    plot_line(scores, args.out, color=args.color)


if __name__ == "__main__":
    main()
