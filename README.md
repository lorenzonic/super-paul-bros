# Super Paul Bros 🍄

A Mario-style platformer built with **Python + Pygame**, playable in the browser via [GitHub Pages](https://YOUR_USERNAME.github.io/YOUR_REPO/).

## Controls

| Action | Keyboard | Mobile |
|--------|----------|--------|
| Move left | `A` / `←` | ◀ button |
| Move right | `D` / `→` | ▶ button |
| Jump | `Space` / `↑` / `W` | ▲ button |
| Pause / back | `Esc` | — |

## Run locally

```bash
pip install pygame
python main.py
```

## Build for web (Pygbag)

```bash
pip install pygbag
python -m pygbag --ume_block 0 .
# then open http://localhost:8000
```

## Deploy

Push to `main` – GitHub Actions automatically builds with Pygbag and deploys to the `gh-pages` branch.  
Enable **GitHub Pages → Source: Deploy from branch → gh-pages** in the repo settings.

## Leaderboard

- **Desktop**: scores saved in `leaderboard.json` (git-ignored).  
- **Browser**: scores persisted in `localStorage` (no server needed).
