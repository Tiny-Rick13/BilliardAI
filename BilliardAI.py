import pygame
import pymunk
import pymunk.pygame_util 
import math
import random

pygame.init()#initialise la lib pygame

width = 1200
height = 678
outerHeight = 50

#fenetre de jeu
screen = pygame.display.set_mode((width, height + outerHeight))
pygame.display.set_caption("Pool")

#crée l'espace pymunk
space = pymunk.Space()
staticBody = space.static_body#pour donner impression de friction, attacher boules à space pour qu'elles ralentissent avec le temps
draw_options = pymunk.pygame_util.DrawOptions(screen)

#clock
clock = pygame.time.Clock()
FPS = 120 #taux de raffraichissement et frame per sec

#variables de jeu
d = 36 #diametre de boule
holeD = 66 #diametre du trou
pocketedBallsImages = []
pocketedBalls = []
takingShot = True
#force = 200
powerIncrease = False
maxForce = 10000
forceDir = 1
isCueBallPocketed = False
points = 0

#couleurs
background = (50, 50, 50)
red = (255, 0, 0)
white = (255, 255, 255)

#police 
police = pygame.font.SysFont("Lato", 30) #police et taille
largePolice = pygame.font.SysFont("Lato",60)

#images****************
tableImage = pygame.image.load("pool_tutorial/assets/images/table-modified.png").convert_alpha()
ballImages = []
blackBallImage = pygame.image.load("pool_tutorial/assets/images/boule8.png").convert_alpha()
ballImages.append(blackBallImage)
for i in range(1, 16):
    if i != 8:
        ballImage = pygame.image.load(f"pool_tutorial/assets/images/boule{i}.png").convert_alpha()
        ballImages.append(ballImage)
ballImage = pygame.image.load(f"pool_tutorial/assets/images/boule16.png").convert_alpha()
ballImages.append(ballImage)
#***********************

#ecrit texte sur l'ecran 
def drawText(text, font, textColor, x, y):
    img = font.render(text, True, textColor) #transforme texte en image
    screen.blit(img, (x, y))

#cree boule
def createBall(radius, position):
    body = pymunk.Body() #par defaut : corps dynamique
    body.position = position
    shape = pymunk.Circle(body, radius)
    shape.mass = 5 #sans unité donc empirique
    shape.elasticity = 0.8 #ajoute rebonds

    #utilise pivot joint pour ajoute de la friction
    pivot = pymunk.PivotJoint(staticBody, body, (0,0), (0,0)) #crée lien entre corps static et boule () coord où le lien est appliqué
    pivot.max_bias = 0 #désactive le correction de jointure
    pivot.max_force = 1000 #simule friction linéaire

    space.add(body, shape, pivot)
    return shape

#definit les boules de jeu
balls = []
rows = 5
#met les boules en pyramides 
for col in range(5):
    for row in range(rows):
        pos = (250 + (col * (d + 1)), 267 + (row * (d + 1)) + (col * d / 2))
        newBall = createBall(d/2, pos)
        balls.append(newBall)
    rows -= 1
#***************************

#coord initiales des boules 
ballsInit = []
for ball in balls: 
    ballsInit.append((ball.body.position[0], ball.body.position[1]))
    
#print(ballsInit)
#*************************

#crée boule blanche (cue ball)
pos = (888, height / 2)
cueBall = createBall(d / 2, pos)
balls.append(cueBall)
#****************************

def setBall(ball):
    space.add(ball.body)
    balls.append(ball)

#reinitialise positions boules 
def reInitBalls():
    points = 0    
    for i, ball in enumerate(balls):
        ball.body.position = ballsInit[i-1]
#*****************************

#cree les trous
#coord obtenues en zoomant sur image 
holes = [
  (55, 63),
  (592, 48),
  (1134, 64),
  (55, 616),
  (592, 629),
  (1134, 616)
]

#coord des cotés
sides = [
  [(88, 56), (109, 77), (555, 77), (564, 56)],
  [(621, 56), (630, 77), (1081, 77), (1102, 56)],
  [(89, 621), (110, 600),(556, 600), (564, 621)],
  [(622, 621), (630, 600), (1081, 600), (1102, 621)],
  [(56, 96), (77, 117), (77, 560), (56, 581)],
  [(1143, 96), (1122, 117), (1122, 560), (1143, 581)]
] #obtenus en zoomant sur l'image et selectionnant pixel correspondant


#cree les cotes de la table
def createSide(polyDims):
    body = pymunk.Body(body_type = pymunk.Body.STATIC)#corps statique
    body.position = ((0,0))
    shape = pymunk.Poly(body, polyDims) #polygone associé au corps 
    shape.elasticity = 0.8 #ajoute rebonds

    space.add(body, shape)

for c in sides:
    createSide(c) #rend les cotés de la table solide

#cree queue

#fonctions pour "l'IA"***************************************************************************


def generateForce():
    return random.uniform(9000, 15000) #génère une force aléatoire entre 100 et 1000

def generateOrientation():
    orientationX = random.uniform(50, 1100)
    orientationY = random.uniform(70, 620)
    return (orientationX, orientationY)

def getBestAttributes(Attributes):
    scoreArray = []
    forceArray = []
    posArray = [] 

    bestAttributes = []

    for i in range(len(Attributes)):
        scoreArray.append(Attributes[i][0])
        forceArray.append(Attributes[i][1])
        posArray.append(Attributes[i][2])

        maxScore = max(scoreArray)
        indexMax = scoreArray.index(maxScore)

        bestAttributes.append((forceArray[indexMax], posArray[indexMax]))
    return bestAttributes     

    
def chooseBestAttributes(Attributes, nbGene, nbCoups):
    bestAttributes = []
    listOfAttributes = []
    for j in range(nbCoups-1):
        for i in range(nbGene):
            listOfAttributes.append(Attributes[i][j])
        bestAttributes.append(getBestAttributes(listOfAttributes))

    return bestAttributes
#*************************************************************************************************

#print(generateOrientation())


#boucle de jeu
run = True
nbCoupsFinal = 2 #nombre de coups que va faire l'IA
compteurCoups = 0 #compteur de coups
nbGene = 5 #nombre de generation de l'IA
compteurGene = 0
isNewGene = False

#tableaux pour stocker les attributs de l'IA
Pos = [] #on y stockera les orientations du tir
Force = [] #on y stockera l'intensité du tir
Score = [] #on y stockera les scores à la fin du nombre de tirs définis 
AttributsCoups = [] #va contenir Pos force et score
AttributsGene = [] #va contenir les AttributsCoups de toutes les géné
#on gardera uniquement celui avec le meilleur score
#*******************************************

while run: 
    clock.tick(FPS) #definit combien de fois par seconde le jeu s'actualise
    space.step(1 / FPS) 
    
    #remplis le fond
    screen.fill(background)
    isCueBallPocketed = False

    pocketedBallImages = []

    #verifie si une boule est rentrée
    for i, ball in enumerate(balls):
        for hole in holes:
            ballDistX = abs(ball.body.position[0] - hole[0]) #dist suivant x d'une boule et d'un trou
            ballDistY = abs(ball.body.position[1] - hole[1]) #dist suivant y d'une boule et d'un trou
            ballDist = math.sqrt((ballDistX ** 2) + (ballDistY ** 2))
            if ballDist <= holeD / 2: #si la dist entre boule et trou est + petite que le rayon de la boule alors boule rentrée dans trou
                #vérifie si la boule rentrée est la blanche ou pas
                if i == len(balls) - 1: #la boule blanche est tjrs en dernière position de la liste
                    points -= 5
                    isCueBallPocketed = True 
                    ball.body.position = ((888, height / 2)) #on replace la boule à l'endroit initial (si ya deja une boule à cette position jsp ce qu'il se passe mais tres rare)
                    ball.body.velocity = (0, 0) #arrete le mouvement
                    #reInitBalls()       
                else:  
                    points += 5                   
                    ball.body.position = (-1000, -1000) #sort la boule de la table
                    ball.body.velocity = (0, 0) #arrete le mouvement             
                    
                    
                    

    #dessine la table
    screen.blit(tableImage, (0,0))

    #dessine les boules
    for i, ball in enumerate(balls):#i va de 0 à #balls et ball prend les val de balls
        screen.blit(ballImages[i], (ball.body.position[0] - ball.radius, ball.body.position[1] - ball.radius)) #coté haut gauche definit comme debut de dessin pour blit

    #verifie si toutes les boules sont à l'arret
    takingShot = True
    for ball in balls:
        if int(ball.body.velocity[0]) != 0 or int(ball.body.velocity[1]) != 0: #vitesse suivant x et y. "int" convertit la vitesse à l'entier: si v =0.0001 -> v=0 et immobile
            takingShot = False

    

    #IA joue
    if takingShot == True and compteurCoups < nbCoupsFinal and compteurGene <= nbGene:
        if isCueBallPocketed == True:
            #replace la boule blanche
            balls[-1].body.position = (888, height / 2) #coord d'origine
            isCueBallPocketed == False
        #calcule l'angle de la queue
        pos = generateOrientation()
        force = generateForce()
        #print(mousePos)
        xDist = balls[-1].body.position[0] - pos[0]
        yDist = -(balls[-1].body.position[1] - pos[1]) #-1 car pygame y decroissant vers le haut
        cueAngle = math.degrees(math.atan2(yDist, xDist))
        #****************************

    #puissance queue  
    if takingShot == True and compteurCoups < nbCoupsFinal and compteurGene <= nbGene:
        xImpulse = math.cos(math.radians(cueAngle)) #composant suivant x de la force
        yImpulse = math.sin(math.radians(cueAngle))
        
        balls[-1].body.apply_impulse_at_local_point((force * (-xImpulse), force * yImpulse), (0,0))#(dx,dy) valeur de l'implusion (x,y) coord application de l'impulsion
        #balls[-1]: dernier element de la liste = cueBall = bouleBlance
        
        #print(compteur)

        #stockage des attributs
        Force.append(force)
        Pos.append((xImpulse, yImpulse))
        Score.append(points)
        if compteurCoups != 0:
            AttributsCoups.append( [ Score[compteurCoups], Force[compteurCoups], Pos[compteurCoups] ] ) 
              
        else: 
            AttributsCoups.append( [Score[0], Force[0], Score[0]])

        
        forceDir = 1
        compteurCoups+=1
        print("Attributs de génération: " +str(AttributsGene))
        print("- Coup numéro " +str(compteurCoups) +": ")
        print("Attributs de coups: " + str(AttributsCoups))

    if compteurCoups >= nbCoupsFinal and compteurGene <= nbGene :
        reInitBalls()
        AttributsGene.append( AttributsCoups )
        AttributsCoups = []
        
        if compteurGene >= nbGene:
            print("*Génération numéro " + str(compteurGene + 1) +"*: ")
            BestAttributes = chooseBestAttributes(AttributsGene, nbGene, nbCoupsFinal)
            print("Meilleurs attributs: " + str(BestAttributes))
        compteurGene += 1 #on passe à une autre génération
        isNewGene = True
        compteurCoups = 0 
    
    #affiche le score
    pygame.draw.rect(screen, background, (0, height, width, outerHeight))
    drawText( "Points: " + str(points), police, white, width - 200, height + 10)

    #affiche boules rentrées dans le recapitulatif
    for i, ball in enumerate(pocketedBallsImages):
        screen.blit(ball, (10 + (i * 50), height+ 10))

    #crée et gère évenements********************
    for event in pygame.event.get():    
        #Ferme la fenetre si on appuie sur close
        if event.type == pygame.QUIT:
            run = False
    #********************************************
    #space.debug_draw(draw_options)
    pygame.display.update()       
    #****************************************        
pygame.quit()            