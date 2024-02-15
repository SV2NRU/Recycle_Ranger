import pygame
import random
from pygame.locals import *
from pygame import mixer
from levels import *

# Initialize pygame and mixer
pygame.init()
pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()


########## VARIABLES ##########

# Set game window size
screenWidth = 800
screenHeight = 800
SCREENSIZE = (screenWidth, screenHeight)

# Clock and FPS
clock = pygame.time.Clock()
FPS = 40

# Fonts
scoreFont = pygame.font.Font('assets/VT323.ttf', 32)
msgFont = pygame.font.Font('assets/VT323.ttf', 100)
scoreMsgFont = pygame.font.Font('assets/VT323.ttf', 80)

# Game variables
tileSize = 40
gameState = "Playing"
mainMenu = True
levelIndex = 0
maxLevel = len(levelList) - 1
score = 0

# Colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
BROWN = (125, 25, 3)
RED = (255, 0, 0)

# Create game window
screen = pygame.display.set_mode(SCREENSIZE)
pygame.display.set_caption('Recycle Ranger')

# Load background images
bgImage = pygame.image.load('assets/main_menu.jpg')
bgImage2 = pygame.image.load('assets/sky.jpg')

# Load buttons images
restartImage = pygame.image.load('assets/restart_btn.png')
startImage = pygame.image.load('assets/start_btn.png')
exitImage = pygame.image.load('assets/exit_btn.png')

# Load sounds
pygame.mixer.music.load('assets/game_music_loop.mp3')
pygame.mixer.music.play(-1,0.0, 2000)
pygame.mixer.music.set_volume(0.2)
jumpSound = pygame.mixer.Sound('assets/jump.mp3')
jumpSound.set_volume(0.6)
pickupSound = pygame.mixer.Sound('assets/pickup.mp3')
pickupSound.set_volume(0.1)


########## FUNCTIONS ##########

def resetLevel(levelIndex):
    enemyGroup.empty()
    garbageGroup.empty()
    recycleBinGroup.empty()
    cansGroup.empty()
    world = World(levelList[levelIndex])
    return world

def drawText(text, font, color, x, y):
    textImage = font.render(text, True, color)
    screen.blit(textImage, (x, y))


########## BUTTON ##########

class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def draw(self):
        buttonAction = False
        mousePos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mousePos):
            if pygame.mouse.get_pressed()[0]:
               buttonAction = True
        screen.blit(self.image, self.rect)
        return buttonAction


########## PLAYER ##########

class Player(): 
    def __init__(self, x ,y):
        self.playerImagesR = []
        self.playerImagesL = []
        self.imgIndex = 0
        self.imgCounter = 0
        self.jump = 0
        self.isJump = False
        self.direction = "R"
        for num in range(1, 5):
            playerImageR = pygame.image.load(f"assets/ranger{num}.png")
            playerImageR = pygame.transform.scale(playerImageR, (30, 60))
            playerImageL = pygame.transform.flip(playerImageR, True, False)
            self.playerImagesR.append(playerImageR)
            self.playerImagesL.append(playerImageL)
        self.image = self.playerImagesR[self.imgIndex]
        self.deadImage = pygame.image.load(f"assets/dead.png")
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self, gameState):       
        dif_x = 0
        dif_y = 0
        walkAnimation = 5

        if gameState == "Playing":
            # Player movement
            key = pygame.key.get_pressed()
            if key[pygame.K_LEFT]:
                dif_x -= 5
                self.imgCounter += 1
                self.direction = "L"
            if key[pygame.K_RIGHT]:
                dif_x += 5
                self.imgCounter += 1
                self.direction = "R"
            if key[pygame.K_SPACE] and self.isJump == False:
                jumpSound.play()
                self.jump = -15
                self.isJump = True
            if key[pygame.K_RIGHT] == False and key[pygame.K_LEFT] == False:
                self.imgCounter = 0
                self.imgIndex = 0
                if self.direction == "R":
                    self.image = self.playerImagesR[self.imgIndex]
                if self.direction == "L":
                    self.image = self.playerImagesL[self.imgIndex]
                               
            # Player image animation
            if self.imgCounter > walkAnimation:
                self.imgIndex += 1
                if self.imgIndex >= len(self.playerImagesR):
                    self.imgIndex = 0
                if self.direction == "R":
                    self.image = self.playerImagesR[self.imgIndex]
                if self.direction == "L":
                    self.image = self.playerImagesL[self.imgIndex]
                self.imgCounter = 0
        
            # Add some gravity
            self.jump += 1
            if self.jump > 10:
                self.jump = 10
            dif_y += self.jump
          
            # Check for collision with tiles
            for tile in world.tileList:
            # Check for collision in x axis
                if tile[1].colliderect(self.rect.x + dif_x, self.rect.y, self.width, self.height):
                    dif_x = 0
                # Check for collision in y axis
                if tile[1].colliderect(self.rect.x, self.rect.y + dif_y, self.width, self.height):
                    # Disable double jumps
                    if key[pygame.K_SPACE] == False:
                        self.isJump = False
                    # Check if below the ground - jumping
                    if self.jump < 0:
                        dif_y = tile[1].bottom - self.rect.top
                        self.jump = 0
                    # Check if above the ground - falling
                    elif self.jump >= 0:
                        dif_y = tile[1].top - self.rect.bottom
                        self.jump = 0

            # Check for collision with enemies
            if pygame.sprite.spritecollide(self, enemyGroup, False):
                gameState = "GameOver"

            # Check for collision with garbage
            if pygame.sprite.spritecollide(self, garbageGroup, False):
                gameState = "GameOver"

            # Check for collision with recycle bin
            if pygame.sprite.spritecollide(self, recycleBinGroup, False):
                gameState = "NextLevel"
                    
            # Update player position
            self.rect.x += dif_x
            self.rect.y += dif_y
        
        # Else If player is dead GaveOver change image of player
        elif gameState == "GameOver":
            self.image = self.deadImage
            if self.rect.y > tileSize + 100:
                 self.rect.y -= 5

        # Draw player on screen
        screen.blit(self.image, self.rect)

        return gameState


########## WORLD ##########

class World():
    def __init__(self, levelData):
        # Create an empty tileList in order to append the tiles based on levelData
        self.tileList = []
        
        # Load tile images
        wallImage = pygame.image.load('assets/wall.png')
        groundImage = pygame.image.load('assets/ground.png')

        rowCount = 0
        for row in levelData:
            columnCount = 0
            for tile in row:
                if tile == 1:
                    image = pygame.transform.scale(wallImage, (tileSize, tileSize))
                    rect = image.get_rect()
                    rect.x = columnCount * tileSize
                    rect.y = rowCount * tileSize
                    tile = (image, rect)
                    self.tileList.append(tile)
                if tile == 2:
                    image = pygame.transform.scale(groundImage, (tileSize, tileSize))
                    rect = image.get_rect()
                    rect.x = columnCount * tileSize
                    rect.y = rowCount * tileSize
                    tile = (image, rect)
                    self.tileList.append(tile)
                if tile == 3:
                    poopEnemy = Enemies(columnCount * tileSize, rowCount * tileSize)
                    enemyGroup.add(poopEnemy)
                if tile == 4:
                    garbage = Garbage(columnCount * tileSize, rowCount * tileSize)
                    garbageGroup.add(garbage)
                if tile == 5:
                    recycleBin = Recyclebin(columnCount * tileSize, rowCount * tileSize)
                    recycleBinGroup.add(recycleBin)
                if tile == 6:
                    can = Cans(columnCount * tileSize, rowCount * tileSize + 30)
                    cansGroup.add(can)
                columnCount += 1
            rowCount +=1
    
    # Draw background image and the tiles of the level
    def drawWorld(self, screen):
        screen.blit(bgImage2, (0, 0))
        for tile in self.tileList:
            screen.blit(tile[0], tile[1])


########## ENEMIES ##########

class Enemies(pygame.sprite.Sprite):
        def __init__(self, x, y):
            pygame.sprite.Sprite.__init__(self)
            self.image = pygame.image.load('assets/poop.png')
            self.rect = self.image.get_rect()
            self.rect.x = x
            self.rect.y = y
            self.direction = 1
            self.counter = 0

        # Override update method to make enemy moves
        def update(self):
            self.rect.x += self.direction
            self.counter += 1
            if abs(self.counter) > 40:
                self.direction *= -1
                self.counter *=-1


########## GARBAGE ##########

class Garbage(pygame.sprite.Sprite):
        def __init__(self, x, y):
            pygame.sprite.Sprite.__init__(self)
            garbageImage= pygame.image.load('assets/garbage.png')
            self.image = pygame.transform.scale(garbageImage, (tileSize, tileSize))
            self.rect = self.image.get_rect()
            self.rect.x = x
            self.rect.y = y


########## CANS ##########

class Cans(pygame.sprite.Sprite):
        def __init__(self, x, y):
            pygame.sprite.Sprite.__init__(self)
            self.randomcan = random.randint(1,3)
            canImage= pygame.image.load(f"assets/can{self.randomcan}.png")
            self.image = pygame.transform.scale(canImage, (tileSize // 2, tileSize // 2))
            self.rect = self.image.get_rect()
            self.rect.center = (x, y)


########## RECYCLE BIN ##########

class Recyclebin(pygame.sprite.Sprite):
        def __init__(self, x, y):
            pygame.sprite.Sprite.__init__(self)
            garbageImage= pygame.image.load('assets/recycle_bin.png')
            self.image = pygame.transform.scale(garbageImage, (tileSize, tileSize * 2))
            self.rect = self.image.get_rect()
            self.rect.x = x
            self.rect.y = y
            
            
########## MAIN GAME ##########

# Create Player instance
player = Player(tileSize, screenHeight-100)

# Create Sprite Group
enemyGroup = pygame.sprite.Group()
garbageGroup = pygame.sprite.Group()
cansGroup = pygame.sprite.Group()
recycleBinGroup = pygame.sprite.Group()

# Creare Buttons instances
restartButton = Button(screenWidth // 2 - 50, screenHeight // 2 + 100, restartImage)
startButton = Button(screenWidth // 2 - 340, screenHeight // 2, startImage)
exitButton = Button(screenWidth // 2 + 70, screenHeight // 2, exitImage)

# Check if levelIndex is inside the levelList and start the game
if levelIndex < len(levelList):
    world = World(levelList[levelIndex])
    runGame = True
else:
    runGame = False

# Game Loop
while runGame:
    clock.tick(FPS)

    screen.blit(bgImage, (0, 0))
    drawText('Recycle Ranger', msgFont, BROWN, 130, 150)

    if mainMenu == True:
        if startButton.draw():
            mainMenu = False
        if exitButton.draw():
            runGame = False
    else:
        world.drawWorld(screen)          
        if gameState == "Playing":
            enemyGroup.update()
            if pygame.sprite.spritecollide(player, cansGroup, True):
                pickupSound.play()
                score += 1
            drawText('Score: ' + str(score), scoreFont, WHITE, 40, 10)
        
        enemyGroup.draw(screen)
        garbageGroup.draw(screen)
        cansGroup.draw(screen)
        recycleBinGroup.draw(screen)
        gameState = player.update(gameState)

        if gameState == "GameOver":
            drawText('GAME OVER', msgFont, RED, screenWidth // 2 -180, screenHeight // 2)
            if restartButton.draw():
                world = resetLevel(levelIndex)
                player = Player(tileSize, screenHeight-100)
                gameState = "Playing"
                score = 0

        if gameState == "NextLevel":
            levelIndex += 1
            if levelIndex <= maxLevel:
                world = resetLevel(levelIndex)
                player = Player(tileSize, screenHeight-100)
                gameState = "Playing"
            else:
                drawText('YOU WIN', msgFont, BLUE, screenWidth // 2 - 140, screenHeight // 2)
                drawText('Score: ' + str(score), scoreMsgFont, BROWN, screenWidth // 2 - 120, screenHeight // 2 - 80)
                if restartButton.draw():
                    levelIndex = 0
                    world = resetLevel(levelIndex)
                    player = Player(tileSize, screenHeight-100)
                    score = 0
                    gameState = "Playing"
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            runGame = False
    
    pygame.display.update()
    
pygame.quit()