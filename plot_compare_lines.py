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

def plot_lines(agent_scores, random_scores, human_scores, out: Path):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(range(1, len(agent_scores)+1), agent_scores, color="blue", marker="o", label="Agente DP")
    ax.plot(range(1, len(random_scores)+1), random_scores, color="red", marker="o", label="Aleatorio")
    if human_scores:
        ax.plot(range(1, len(human_scores)+1), human_scores, color="green", marker="o", label="Humano")
    ax.set_xlabel("Episodio")
    ax.set_ylabel("Puntaje")
    ax.set_title("Comparacion de puntajes por episodio")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    print(f"Grafico guardado en {out}")

def main():
    parser = argparse.ArgumentParser(description="Grafico de lineas agente vs aleatorio vs humano")
    parser.add_argument("--agent_csv", type=Path, required=True, help="CSV agente DP")
    parser.add_argument("--random_csv", type=Path, required=True, help="CSV aleatorio")
    parser.add_argument("--human_csv", type=Path, default=None, help="CSV humano (opcional)")
    parser.add_argument("--out", type=Path, default=Path("results/lines_compare.png"), help="Ruta de salida")
    args = parser.parse_args()

    agent_scores = read_scores(args.agent_csv)
    random_scores = read_scores(args.random_csv)
    human_scores = read_scores(args.human_csv) if args.human_csv else []

    plot_lines(agent_scores, random_scores, human_scores, args.out)

if __name__ == "__main__":
    main()
