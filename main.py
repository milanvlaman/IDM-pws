import pygame
import random
import math
import copy
from random import randint

# initiële plaatsing
Initieel_P = .035  # auto #0.0367 2 sec regel
Initieel_V = 60 / 3.6
Filleverkeer = True
Fille_Size = 60

# variabelen
Confortabel_Deceleratie = 1.67
Max_Acceleratie = 0.73
Reactietijd_Gem = (1, 0.2)  # (gemiddeld in s, maximale afwijking van gemiddeld per auto)
Component_Acceleratie = 3
Max_Vel = 100 / 3.6
Min_Afstand = 6
Remkans = 0.05
# reactietijd
T_Basis = 0.5
T_Extra = 1.9
p_T = 0.015

# grafiek
WIDTH, HEIGHT = 2500, 1300  # window dimenties
graph_WIDTH, graph_HEIGHT = 2470, 1250  # reele dimenties grafiek
domein_grafiek, bereik_grafiek = 1200, 1100  # domein en bereik grafiek

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("IDM model")
time = 0
dt = 0.4

n = 8  # inverse of probability
rand_bool = randint(0, n * n - 1) % n == 0


def rand_bool(prob):
    s = str(prob)
    p = s.index('.')
    d = 10 ** (len(s) - p)
    return randint(0, d * d - 1) % d < int(s[p + 1:])


class Graph():  # plotten en opmaken van grafiek
    def __init__(self, x_Coordinaat, y_Coordinaat, WIDTH, HEIGHT, Y_AS_data, X_AS_data, voertuigen):

        # AS_data = (max variabele AS, naam AS)
        self.x = x_Coordinaat
        self.y = y_Coordinaat
        self.width = WIDTH
        self.height = HEIGHT
        self.Y_max = Y_AS_data[0]
        self.X_max = X_AS_data[0]
        self.Y_name = Y_AS_data[1]
        self.x_name = X_AS_data[1]
        self.voertuigen = voertuigen
        self.border_width = 2

    def punt_out_of_domein(self, punt):  # check of punt buiten domein of bereik grafiek valt
        if punt[0] > self.X_max or punt[0] < 0:
            return True

    def punt_out_of_bereik(self, punt):
        if punt[1] >= self.Y_max or punt[0] < 0:
            return True

    def reeel_punt_coordinaat(self, punt):  # geef de coordinaten in pygame waarde
        coordinaat = [0, 0]
        coordinaat[0] = self.x + ((self.width - self.border_width) * (punt[0] / self.X_max))
        coordinaat[1] = self.y + self.height - ((self.height - self.border_width) * (punt[1] / self.Y_max))
        return coordinaat

    def border(self):
        pygame.draw.rect(WIN, BLACK, pygame.Rect(self.x, self.y, self.width, self.height), self.border_width, 0)

    def draw_line(self, first, lead, vel):
        kleur = (max(0, round(255 * (1 - vel / Max_Vel) ** 5 - 5)),
                 min(125, (round(240 * (vel / Max_Vel)))), 0)
        pygame.draw.line(WIN, kleur, self.reeel_punt_coordinaat(first), self.reeel_punt_coordinaat(lead), 1)

    def plot_graph(self):
        self.border()
        for voertuig in self.voertuigen:
            coordinaten = voertuig.coordinaten
            for i in range(len(coordinaten) - 1):
                first = coordinaten[i]
                vel = first[2]
                try:
                    lead = coordinaten[i + 1]
                except:
                    lead = coordinaten[-1]
                first = first[:2]
                lead = lead[:2]
                if self.punt_out_of_bereik(lead):
                    a = (lead[1] - first[1]) / dt
                    x_snij = (self.Y_max - first[1]) / a + first[0]
                    lead_snij = (x_snij, self.Y_max)
                    self.draw_line(first, lead_snij, vel)
                    self.draw_line((lead_snij[0], 0), (lead[0], lead[1] - self.Y_max), vel)
                elif self.punt_out_of_bereik(first):
                    self.draw_line((first[0], first[1] - self.Y_max), lead, vel)
                elif not (self.punt_out_of_domein(lead) or self.punt_out_of_bereik(lead) or self.punt_out_of_bereik(
                        first)):
                    self.draw_line(first, lead, vel)


class Voertuig():
    def __init__(self, coordinaat, max_vel, min_afstand, confor_a, max_a, component_accelertie, reactietijd):
        # coordinaat = [(tijd, afstand, velocity)]
        self.coordinaten = coordinaat
        self.a = 0
        self.vel_max = max_vel
        self.s_min = min_afstand
        self.b_i = confor_a
        self.a_i = max_a
        self.T_i = T_Basis
        self.a_comp = component_accelertie
        self.run = True

    def move(self, next_voertuig):  # beweeg het voertuig en maak nieuwe coordinaat
        if self.run:
            self.pos = self.coordinaten[-1]
            self.vel = self.pos[2]
            next_pos = next_voertuig.coordinaten[-1]
            next_vel = next_pos[2]
            self.x = self.pos[1]
            self.sqrt_ab = math.sqrt(2 * self.a_i * self.b_i)
            d_v = self.vel - next_vel
            # tijdberekenen
            if rand_bool(p_T):
                self.T_i = self.T_i + T_Extra * 0.1
            else:
                self.T_i = T_Basis

            # d_s berekenen
            if next_pos[1] < self.pos[1]:
                d_s = bereik_grafiek - self.pos[1] + next_pos[1]
            else:
                d_s = next_pos[1] - self.pos[1]

            s_gelief = self.s_min + max(0, self.vel * self.T_i + (self.vel * d_v) / self.sqrt_ab)
            self.a = self.a_i * ((1 - (self.vel / self.vel_max) ** self.a_comp) - (s_gelief / d_s) ** 2)
            # update positie en velocity
            if self.vel + self.a * dt < 0:
                self.x -= 1 / 2 * self.vel * self.vel / self.a
                self.vel = 0

            else:
                self.vel += dt * self.a
                self.x += self.vel * dt + self.a * dt * dt / 2
            # remkans
            if rand_bool(Remkans):
                self.vel = max(self.vel - 2, 0)

            if self.pos[0] < domein_grafiek and self.pos[1] < bereik_grafiek:
                self.coordinaten.append((time, self.x, self.vel))
            elif self.pos[0] < domein_grafiek and self.pos[1] > bereik_grafiek:
                self.coordinaten.append((time, (self.x - bereik_grafiek), self.vel))
            else:
                self.run = False


voertuigen = []


def spawn_voertuigen(filleverkeer):
    reactietijd = random.uniform(Reactietijd_Gem[0] - Reactietijd_Gem[1], Reactietijd_Gem[0] + Reactietijd_Gem[1])
    afstand_onderling = 1 / Initieel_P
    if filleverkeer:
        fille_start = (bereik_grafiek / 2) - (Fille_Size / 2)
        fille_eind = bereik_grafiek / 2 + Fille_Size / 2

        for i in range(math.floor(fille_start / afstand_onderling)):
            voertuigen.append(Voertuig([(0, afstand_onderling * i, Initieel_V)], Max_Vel, Min_Afstand,
                                       Confortabel_Deceleratie, Max_Acceleratie, Component_Acceleratie, reactietijd))
        # fille
        afstand = Min_Afstand
        for i in range(math.floor(Fille_Size / afstand - 1)):
            voertuigen.append((Voertuig([(0, fille_start + afstand * i, 0)], Max_Vel, Min_Afstand,
                                        Confortabel_Deceleratie, Max_Acceleratie, Component_Acceleratie, reactietijd)))

        for i in range(math.floor((bereik_grafiek - fille_eind) / afstand_onderling)):
            voertuigen.append(Voertuig([(0, fille_eind + i * afstand_onderling, Initieel_V)], Max_Vel, Min_Afstand,
                                       Confortabel_Deceleratie, Max_Acceleratie, Component_Acceleratie, reactietijd))

    else:
        for i in range(math.floor(bereik_grafiek / afstand_onderling)):
            voertuigen.append(Voertuig([(0, afstand_onderling * i, Initieel_V)], Max_Vel, Min_Afstand,
                                       Confortabel_Deceleratie, Max_Acceleratie, Component_Acceleratie, reactietijd))


graph = Graph((WIDTH - graph_WIDTH) / 2, 5, graph_WIDTH, graph_HEIGHT, (bereik_grafiek, 'x in m'),
              (domein_grafiek, 'tijd in s'), voertuigen)


def draw_window():
    WIN.fill((WHITE))
    graph.plot_graph()
    pygame.display.update()


def main():
    global time, Filleverkeer
    spawn_voertuigen(Filleverkeer)

    run = True
    quit = False
    while run:
        time += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit = True
                break
        run = False
        if quit:
            break

        first_voertuig = copy.deepcopy(voertuigen[0])
        for i in range(len(voertuigen)):
            voertuig = voertuigen[i]
            try:
                next_voertuig = voertuigen[i + 1]
            except IndexError:
                next_voertuig = first_voertuig

            if voertuig.run:
                run = True
            voertuig.move(next_voertuig)
            # print('-----')
            # print('nummer: ', str(i))
            # print('coordinaat: ', str(voertuig.coordinaten))
            # print('next_coordinaat: ', str(next_voertuig.coordinaten))
        # draw_window()

    if not quit:
        draw_window()
        run = True
        clock = pygame.time.Clock()
        while run:
            clock.tick(10)
            keys = pygame.key.get_pressed()
            captured = False
            if keys[pygame.K_c] and not captured:
                pygame.image.save(WIN, 'screenshot.jpg')
                captured = True
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False


if __name__ == "__main__":
    main()
