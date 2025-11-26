import os
import random
import argparse
import statistics as stats
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Tuple

import pygame


class Action(Enum):
    NONE = 0
    JUMP = auto()
    DUCK = auto()
    STAND = auto()


class ObstacleKind(Enum):
    LOW = "low"
    MID = "mid"
    HIGH = "high"


class PlayerState(Enum):
    RUN = auto()
    JUMP = auto()
    DUCK = auto()


@dataclass
class Config:
    # Parametros de simulacion, fisica y discretizacion para DP.
    width: int = 960
    height: int = 360
    player_x: int = 120
    ground_y: int = 300
    gravity: float = 2400.0
    jump_velocity: float = -1050.0
    player_width: int = 52
    run_height: int = 70
    duck_height: int = 40
    base_speed: float = 280.0
    speed_growth: float = 24.0
    min_difficulty: float = 0.35
    ramp_time: float = 35.0
    warmup_time: float = 1.6
    short_gap: int = 190
    long_gap: int = 320
    obstacle_max: int = 2
    dp_dt: float = 0.05
    dp_depth: int = 12
    rollout_steps: int = 2
    gamma: float = 0.98
    reward_alive: float = 1.0
    reward_progress: float = 0.05
    max_time: float = 60.0
    fast_dt: float = 0.008  # ~125 FPS equivalente en modo rapido (fidelidad razonable)
    # Discretizacion para iteracion de valor (PD)
    y_bucket: int = 4
    vy_bucket: int = 40
    x_bucket: int = 8
    speed_bucket: int = 20
    y_bucket_max: int = 80
    vy_bucket_min: int = -30
    vy_bucket_max: int = 30
    x_bucket_max: int = 200
    speed_bucket_max: int = 120


BLACK = (20, 20, 20)
WHITE = (240, 240, 240)
GREEN = (48, 204, 130)
ORANGE = (255, 170, 64)
RED = (230, 70, 70)
GRAY = (90, 90, 90)


class Player:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.x = cfg.player_x
        self.height = cfg.run_height
        self.width = cfg.player_width
        self.y = cfg.ground_y - self.height
        self.vy = 0.0
        self.state = PlayerState.RUN
        self.on_ground = True

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def _set_height(self, height: int):
        delta = self.height - height
        self.height = height
        self.y += delta

    def update(self, action: Action, dt: float):
        # Integracion simple de movimiento vertical y cambio de postura.
        if action == Action.JUMP and self.on_ground:
            self.vy = self.cfg.jump_velocity
            self.state = PlayerState.JUMP
            self.on_ground = False
        elif action == Action.DUCK and self.on_ground and self.state != PlayerState.DUCK:
            self.state = PlayerState.DUCK
            self._set_height(self.cfg.duck_height)
        elif action == Action.STAND and self.on_ground and self.state == PlayerState.DUCK:
            self.state = PlayerState.RUN
            self._set_height(self.cfg.run_height)

        self.vy += self.cfg.gravity * dt
        self.y += self.vy * dt
        if self.y >= self.cfg.ground_y - self.height:
            self.y = self.cfg.ground_y - self.height
            self.vy = 0
            self.on_ground = True
            if self.state == PlayerState.JUMP:
                self.state = PlayerState.RUN
        else:
            self.on_ground = False


class Obstacle:
    def __init__(self, kind: ObstacleKind, x: float, cfg: Config):
        self.kind = kind
        self.width, self.height, self.y = self._spec(cfg)
        self.x = x

    def _spec(self, cfg: Config) -> Tuple[int, int, int]:
        if self.kind == ObstacleKind.LOW:
            h = 38
            y = cfg.ground_y - h
            w = 32
        elif self.kind == ObstacleKind.MID:
            h = 34
            y = cfg.ground_y - 140  # vuelo alto, se pasa sin saltar
            w = 46
        else:
            h = 34
            y = cfg.ground_y - 90  # obstaculo volador bajo: requiere agacharse
            w = 46
        return w, h, y

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)


class ObstacleManager:
    def __init__(self, cfg: Config, rng: random.Random):
        self.cfg = cfg
        self.rng = rng
        self.obstacles: List[Obstacle] = []
        self.distance_since_last = 0.0
        self.difficulty = cfg.min_difficulty
        self.elapsed = 0.0
        self.next_gap = self._next_gap()

    def _next_gap(self) -> float:
        base = self.rng.choice([self.cfg.short_gap, self.cfg.long_gap])
        gap_scale = 1.8 - 0.8 * self.difficulty
        return base * gap_scale * self.rng.uniform(0.9, 1.15)

    def reset(self):
        self.obstacles.clear()
        self.distance_since_last = 0.0
        self.difficulty = self.cfg.min_difficulty
        self.elapsed = 0.0
        self.next_gap = self._next_gap()

    def set_difficulty(self, difficulty: float):
        self.difficulty = max(self.cfg.min_difficulty, min(1.0, difficulty))

    def update(self, dt: float, speed: float):
        # Mueve obstaculos existentes y decide spawns con dificultad creciente.
        self.elapsed += dt
        for ob in self.obstacles:
            ob.x -= speed * dt
        self.obstacles = [ob for ob in self.obstacles if ob.x + ob.width > 0]

        self.distance_since_last += speed * dt
        if self.elapsed < self.cfg.warmup_time:
            self.distance_since_last = 0.0
            return

        if self.distance_since_last >= self.next_gap and len(self.obstacles) < self.cfg.obstacle_max:
            spawn_x = self.cfg.width + self.rng.randint(0, 60)
            kind = self.rng.choice([ObstacleKind.LOW, ObstacleKind.MID, ObstacleKind.HIGH])
            if kind == ObstacleKind.LOW:
                roll = self.rng.random()
                count = 1 if roll < 1/3 else 2 if roll < 2/3 else 3
                gap_px = 2
                x_pos = spawn_x
                for _ in range(count):
                    if len(self.obstacles) >= self.cfg.obstacle_max:
                        break
                    ob = Obstacle(kind, x_pos, self.cfg)
                    self.obstacles.append(ob)
                    x_pos += ob.width + gap_px
            else:
                self.obstacles.append(Obstacle(kind, spawn_x, self.cfg))
            self.distance_since_last = 0.0
            self.next_gap = self._next_gap()


class DPAgent:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.memo = {}

    def decide(self, player: Player, obstacles: List[Obstacle], speed: float) -> Action:
        # Busca accion via backup Bellman recursivo sobre un estado discretizado.
        snapshot = self._snapshot(player, obstacles)
        self.memo.clear()
        action, _ = self._search(snapshot, speed, self.cfg.dp_depth)
        return action

    def _snapshot(self, player: Player, obstacles: List[Obstacle]):
        # Estado discreto: posicion y y velocidad del jugador, postura (duck) y obstaculos proximos (x, tipo, tamano).
        obs = sorted(obstacles, key=lambda o: o.x)
        obs_state = []
        for o in obs[:3]:
            obs_state.append((o.x, o.y, o.width, o.height, o.kind))
        return (player.y, player.vy, player.state == PlayerState.DUCK, tuple(obs_state))

    def _player_rect_from_state(self, y: float, duck: bool) -> pygame.Rect:
        height = self.cfg.duck_height if duck else self.cfg.run_height
        return pygame.Rect(self.cfg.player_x, int(y), self.cfg.player_width, height)

    def _collides(self, y: float, duck: bool, obstacles) -> bool:
        rect = self._player_rect_from_state(y, duck)
        for ob in obstacles:
            x, oy, w, h, _ = ob
            ob_rect = pygame.Rect(int(x), int(oy), w, h)
            if rect.colliderect(ob_rect):
                return True
        return False

    def _step_player(self, y: float, vy: float, duck: bool, action: Action) -> Tuple[float, float, bool]:
        height = self.cfg.duck_height if duck else self.cfg.run_height
        on_ground = y >= self.cfg.ground_y - height - 1e-3

        if action == Action.JUMP and on_ground:
            vy = self.cfg.jump_velocity
            duck = False
        elif action == Action.DUCK and on_ground:
            duck = True
        elif action == Action.STAND and on_ground:
            duck = False

        vy += self.cfg.gravity * self.cfg.dp_dt
        y += vy * self.cfg.dp_dt

        height = self.cfg.duck_height if duck else self.cfg.run_height
        if y >= self.cfg.ground_y - height:
            y = self.cfg.ground_y - height
            vy = 0.0

        return y, vy, duck

    def _step_obstacles(self, obstacles, speed: float):
        next_obs = []
        for x, y, w, h, kind in obstacles:
            x -= speed * self.cfg.dp_dt
            if x + w > 0:
                next_obs.append((x, y, w, h, kind))
        return next_obs

    def _state_key(self, y: float, vy: float, duck: bool, obstacles, speed: float):
        def bucket(val: float, size: float) -> int:
            return int(round(val / size))

        obs_key = []
        for x, _, _, _, kind in list(obstacles)[:2]:
            obs_key.append((bucket(x, 8), kind.value))
        return (bucket(y, 4), bucket(vy, 40), duck, tuple(obs_key), bucket(speed, 20))

    def _search(self, state, speed: float, depth: int) -> Tuple[Action, float]:
        # Programacion dinamica: backup estilo Bellman con memoizacion sobre estados discretizados.
        y, vy, duck, obstacles = state
        key = (self._state_key(y, vy, duck, obstacles, speed), depth)
        if key in self.memo:
            return self.memo[key]

        best_action = Action.NONE
        best_score = -1e9
        actions = (Action.NONE, Action.JUMP, Action.DUCK, Action.STAND)

        for action in actions:
            sim_y, sim_vy, sim_duck = y, vy, duck
            sim_obs = list(obstacles)
            alive = True
            gained = 0.0

            for _ in range(self.cfg.rollout_steps):
                sim_y, sim_vy, sim_duck = self._step_player(sim_y, sim_vy, sim_duck, action if _ == 0 else Action.NONE)
                sim_obs = self._step_obstacles(sim_obs, speed)
                if self._collides(sim_y, sim_duck, sim_obs):
                    alive = False
                    break
                gained += self.cfg.reward_alive * self.cfg.dp_dt + self.cfg.reward_progress * speed * self.cfg.dp_dt

            total_score = -1000.0 if not alive else gained
            if alive and depth > 1:
                next_state = (sim_y, sim_vy, sim_duck, tuple(sim_obs))
                _, child_score = self._search(next_state, speed, depth - 1)
                total_score += self.cfg.gamma * child_score

            if total_score > best_score:
                best_score = total_score
                best_action = action

        self.memo[key] = (best_action, best_score)
        return best_action, best_score




class RandomPolicy:
    def decide(self, player: Player) -> Action:
        # Baseline simple: elige aleatorio cuando esta en el suelo.
        if player.on_ground:
            return random.choice([Action.NONE, Action.JUMP, Action.DUCK])
        return Action.NONE


class Game:
    def __init__(self, cfg: Config, mode: str, episodes: int, headless: bool = False, rng: random.Random | None = None, fast: bool = False):
        self.cfg = cfg
        self.mode = mode
        self.episodes = episodes
        self.rng = rng or random.Random()
        self.fast = fast
        if headless:
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.init()
        flags = pygame.HIDDEN if headless else 0
        self.screen = pygame.display.set_mode((cfg.width, cfg.height), flags=flags)
        pygame.display.set_caption("Dino (POO + DP)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 18)
        self.agent = DPAgent(cfg)
        self.random_policy = RandomPolicy()

    def run(self):
        scores = []
        durations = []
        for ep in range(self.episodes):
            print(f"[EP {ep+1}/{self.episodes}] inicio")
            score, duration = self._run_episode(ep)
            scores.append(score)
            durations.append(duration)
            print(f"[EP {ep+1}/{self.episodes}] fin - score={score:.1f}, tiempo={duration:.2f}s")
        return scores, durations

    def _run_episode(self, episode_idx: int) -> float:
        # Bucle principal de simulacion por episodio.
        player = Player(self.cfg)
        obstacles = ObstacleManager(self.cfg, self.rng)
        speed = self.cfg.base_speed
        t = 0.0
        alive = True
        score = 0.0

        while alive and t < self.cfg.max_time:
            if self.fast:
                dt = self.cfg.fast_dt
                pygame.event.pump()
            else:
                dt = self.clock.tick(60) / 1000.0
            t += dt
            difficulty = min(1.0, self.cfg.min_difficulty + t / self.cfg.ramp_time)
            speed_factor = 0.55 + 0.45 * difficulty
            speed = self.cfg.base_speed + self.cfg.speed_growth * t * speed_factor
            action = Action.NONE

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

            if self.mode == "human":
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
                    action = Action.JUMP
                elif keys[pygame.K_DOWN]:
                    action = Action.DUCK
                elif player.state == PlayerState.DUCK and not keys[pygame.K_DOWN]:
                    action = Action.STAND
            elif self.mode == "agent":
                action = self.agent.decide(player, obstacles.obstacles, speed)
            elif self.mode == "random":
                action = self.random_policy.decide(player)

            player.update(action, dt)
            obstacles.set_difficulty(difficulty)
            obstacles.update(dt, speed)

            for ob in obstacles.obstacles:
                if player.rect().colliderect(ob.rect()):
                    alive = False
                    break

            score += dt * 100.0 + speed * dt * 0.05
            self._render(player, obstacles, score, episode_idx, t, speed, difficulty)
        return score, t

    def _render(self, player: Player, obstacles: ObstacleManager, score: float, episode_idx: int, t: float, speed: float, difficulty: float):
        if not pygame.display.get_active() and pygame.display.get_surface().get_flags() & pygame.HIDDEN:
            return
        self.screen.fill(WHITE)
        pygame.draw.line(self.screen, GRAY, (0, self.cfg.ground_y + 2), (self.cfg.width, self.cfg.ground_y + 2), 2)

        color = GREEN if player.state == PlayerState.RUN else ORANGE if player.state == PlayerState.DUCK else BLACK
        pygame.draw.rect(self.screen, color, player.rect(), border_radius=6)

        for ob in obstacles.obstacles:
            ob_color = BLACK if ob.kind == ObstacleKind.LOW else ORANGE
            pygame.draw.rect(self.screen, ob_color, ob.rect(), border_radius=4)

        info_lines = [
            f"Modo: {self.mode} | Episodio {episode_idx + 1}/{self.episodes} | Dificultad: {difficulty:0.2f}",
            f"Puntaje: {score:7.1f}   Velocidad: {speed:5.0f} px/s",
            f"Tiempo vivo: {t:4.2f}s   Obstaculos: {len(obstacles.obstacles)}",
            "Teclas: SPACE/UP saltar, DOWN agacharse, Cerrar ventana para salir",
        ]
        for i, text in enumerate(info_lines):
            surface = self.font.render(text, True, BLACK)
            self.screen.blit(surface, (16, 12 + 22 * i))

        pygame.display.flip()


def parse_args():
    parser = argparse.ArgumentParser(description="Dino de Google con POO + Programacion Dinamica")
    parser.add_argument("--mode", choices=["human", "agent", "random"], default="human", help="Control del jugador")
    parser.add_argument("--episodes", type=int, default=1, help="Cantidad de episodios a jugar")
    parser.add_argument("--headless", action="store_true", help="Ejecuta sin ventana (para evaluar agentes)")
    parser.add_argument("--seed", type=int, default=None, help="Semilla para reproducibilidad")
    parser.add_argument("--save_csv", type=str, default=None, help="Ruta para guardar puntajes por episodio")
    parser.add_argument("--max_time", type=float, default=None, help="Tiempo maximo por episodio (segundos)")
    parser.add_argument("--fast", action="store_true", help="Modo rapido (salta limitacion de FPS en headless)")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.seed is not None:
        random.seed(args.seed)
        os.environ["PYTHONHASHSEED"] = str(args.seed)
    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    cfg = Config()
    if args.max_time is not None:
        cfg.max_time = args.max_time
    game = Game(cfg, args.mode, args.episodes, headless=args.headless, rng=rng, fast=args.fast)
    try:
        scores, durations = game.run()
    finally:
        pygame.quit()
    avg = sum(scores) / len(scores)
    med = stats.median(scores)
    best = max(scores)
    worst = min(scores)
    print(f"Episodios: {len(scores)} | Puntajes: {[round(s,1) for s in scores]} | Promedio: {avg:.1f} | Mediana: {med:.1f} | Max: {best:.1f} | Min: {worst:.1f}")
    if args.save_csv:
        try:
            import csv

            with open(args.save_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["episode", "score", "duration_sec"])
                for i, (s, d) in enumerate(zip(scores, durations), start=1):
                    writer.writerow([i, f"{s:.3f}", f"{d:.3f}"])
            print(f"Resultados guardados en {args.save_csv}")
        except Exception as exc:
            print(f"No se pudo guardar CSV: {exc}")


if __name__ == "__main__":
    main()
