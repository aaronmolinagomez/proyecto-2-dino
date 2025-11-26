import argparse
import csv
import json
import statistics as stats
from pathlib import Path
import random

from main import Config, Game


def run_mode(mode: str, episodes: int, seed: int | None, max_time: float | None, headless: bool, fast: bool) -> tuple[list[float], list[float]]:
    rng = random.Random(seed)
    cfg = Config()
    if max_time is not None:
        cfg.max_time = max_time
    game = Game(cfg, mode, episodes, headless=headless, rng=rng, fast=fast)
    return game.run()


def save_csv(path: Path, scores: list[float], durations: list[float]):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["episode", "score", "duration_sec"])
        for i, (s, d) in enumerate(zip(scores, durations), start=1):
            writer.writerow([i, f"{s:.3f}", f"{d:.3f}"])


def summarize(scores: list[float]) -> dict:
    return {
        "n": len(scores),
        "mean": stats.mean(scores) if scores else 0.0,
        "median": stats.median(scores) if scores else 0.0,
        "min": min(scores) if scores else 0.0,
        "max": max(scores) if scores else 0.0,
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark Dino agent vs baseline")
    parser.add_argument("--episodes", type=int, default=50, help="Episodios por modo")
    parser.add_argument("--seed", type=int, default=1, help="Semilla para reproducibilidad")
    parser.add_argument("--max_time", type=float, default=15.0, help="Tiempo maximo por episodio (s)")
    parser.add_argument("--out_dir", type=Path, default=Path("results"), help="Directorio de salida")
    parser.add_argument("--no_plot", action="store_true", help="No generar grafico")
    parser.add_argument("--fast", action="store_true", help="Modo rapido (simulacion sin limite de FPS)")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    agent_scores, agent_durs = run_mode("agent", args.episodes, args.seed, args.max_time, headless=True, fast=args.fast)
    rand_scores, rand_durs = run_mode("random", args.episodes, args.seed, args.max_time, headless=True, fast=args.fast)

    agent_csv = args.out_dir / "agent.csv"
    rand_csv = args.out_dir / "random.csv"
    save_csv(agent_csv, agent_scores, agent_durs)
    save_csv(rand_csv, rand_scores, rand_durs)

    summary = {
        "agent": summarize(agent_scores),
        "random": summarize(rand_scores),
        "seed": args.seed,
        "episodes": args.episodes,
        "max_time": args.max_time,
    }
    with (args.out_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("Agente:", summary["agent"])
    print("Aleatorio:", summary["random"])
    print(f"CSV guardados en {agent_csv} y {rand_csv}")

    if not args.no_plot:
        try:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(6, 4))
            ax.boxplot([agent_scores, rand_scores], labels=["Agente DP", "Aleatorio"], showmeans=True)
            ax.set_ylabel("Puntaje")
            ax.set_title("Comparacion de puntajes por episodio")
            ax.grid(True, axis="y", alpha=0.3)
            fig.tight_layout()
            out_path = args.out_dir / "scores.png"
            fig.savefig(out_path, dpi=150)
            print(f"Grafico guardado en {out_path}")
        except Exception as exc:
            print(f"No se pudo generar grafico: {exc}")


if __name__ == "__main__":
    main()
