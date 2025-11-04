import pygame

class Animator:
    def __init__(self, solution, delay_ms=140):
        self.solution = solution or []
        self.delay_ms = delay_ms
        self.index = 1
        self.active = False
        self.next_tick = 0

    def start(self):
        if not self.solution:
            return
        self.active = True
        self.index = 1
        self.next_tick = pygame.time.get_ticks()

    def update(self, now, path):
        if not self.active:
            return False
        if now >= self.next_tick:
            if self.index < len(self.solution):
                path.append(self.solution[self.index])
                self.index += 1
                self.next_tick = now + self.delay_ms
            else:
                self.active = False
        return self.active
