# assets/

Put your PNG sprites here for future use.

Expected files (future):
- paul_idle.png      – Paul standing
- paul_walk_0.png    – Walk frame 0
- paul_walk_1.png    – Walk frame 1
- paul_jump.png      – Paul jumping
- paul_dead.png      – Paul death pose
- goomba_walk_0.png
- goomba_walk_1.png
- goomba_stomped.png

In sprites.py, replace the procedural drawing in Player._render()
with:  self.image = pygame.image.load("assets/paul_idle.png").convert_alpha()
