import pygame
import sys
import random
import sqlite3
from pygame.locals import *
from pygame import mixer
from levels import *
from sqlite3 import Error

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
nameFont = pygame.font.Font('assets/VT323.ttf', 40)

# Game variables
tileSize = 40
gameState = "Playing"
mainMenu = True
levelIndex = 0
maxLevel = len(levelList) - 1
cansScore = 0
playerName = ""
elapsedTime = 0
dbWriteState = True

# Colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
BROWN = (125, 25, 3)
RED = (255, 0, 0)

# User Input Rect
uiRect = pygame.Rect(400, 250, 320, 40)

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

# Reset Level
def resetLevel(levelIndex):
    enemyGroup.empty()
    garbageGroup.empty()
    recycleBinGroup.empty()
    cansGroup.empty()
    platformGroup.empty()
    world = World(levelList[levelIndex])
    return world

# Draw text to screen
def drawText(text, font, color, x, y):
    textImage = font.render(text, True, color)
    screen.blit(textImage, (x, y))

# Player name input box
def inputName(playerName):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()  
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                playerName = playerName[:-1]
            else:
                if len(playerName) < 12:  # maximum 12 characters
                    playerName += event.unicode
    drawText('Enter your Name: ', nameFont, BROWN, 130, 250)
    pygame.draw.rect(screen, WHITE, uiRect)
    inputSurface = nameFont.render(playerName, True, BROWN)
    screen.blit(inputSurface, (uiRect.x+5, uiRect.y))
    uiRect.w = max(150, inputSurface.get_width()+10)
    return playerName

# DB Create connection
def createConnection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print("Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occured")
    return connection

# DB Execute write SQL query
def executeQuery(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query (write) executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

# DB Execute read SQL query
def executeReadQuery(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
        print("Query (read) executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

# Show high scores board
def scoreBoard():
    rect = pygame.Surface((520,200), pygame.SRCALPHA, 32)
    rect.fill((255, 255, 255, 200))
    screen.blit(rect, (screenWidth / 2 - 270, 30))
    
    header = scoreFont.render("High Scores", True, BROWN)
    screen.blit(header, (screenWidth / 2 - header.get_width() / 2, 40))
    header1 = scoreFont.render("Player", True, BLUE)
    screen.blit(header1, (screenWidth / 2 - 260, 80))
    header2 = scoreFont.render("Score", True, BLUE)
    screen.blit(header2, (screenWidth / 2 - header2.get_width(), 80))
    header3 = scoreFont.render("Time", True, BLUE)
    screen.blit(header3, (screenWidth / 2 + 160, 80))

    y_pos = 120
    for playername, score, time in dbexport:
        playerText = scoreFont.render(playername, True, BLUE)
        scoreText = scoreFont.render(str(score), True, BLUE)
        timeText = scoreFont.render(str(time), True, BLUE)
        screen.blit(playerText, (screenWidth / 2 - 260, y_pos))
        screen.blit(scoreText, (screenWidth / 2 - header2.get_width(), y_pos))
        screen.blit(timeText, (screenWidth / 2 + 160, y_pos))
        y_pos += 40


########## SQL QUERIES ##########

createUserTable = """
CREATE TABLE IF NOT EXISTS highscores (
id INTEGER PRIMARY KEY AUTOINCREMENT,
playername TEXT NOT NULL,
score INTEGER,
time float
);
"""

selectHighScores = "SELECT playername, score, time FROM highscores ORDER BY score DESC, time ASC LIMIT 3"


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
        collisionThreshold = 20

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

            # Check for collision with moving platforms
            for platform in platformGroup:
                # Check for collision in x axis
                if platform.rect.colliderect(self.rect.x + dif_x, self.rect.y, self.width, self.height):
                    dif_x = 0
                # Check for collision in x axis
                if platform.rect.colliderect(self.rect.x, self.rect.y + dif_y, self.width, self.height):
                    # Check if player is below the platform
                    if abs((self.rect.top + dif_y) - platform.rect.bottom) <= collisionThreshold:
                        self.jump = 0
                        dif_y = platform.rect.bottom - self.rect.top # Stop because player hit platform
                    # Check if player is above platform
                    elif abs((self.rect.bottom + dif_y) - platform.rect.top) <= collisionThreshold:
                        self.rect.bottom = platform.rect.top - 1 # Stop because player standing on the platform
                        self.jump = 0
                        if key[pygame.K_SPACE] == False:
                            self.isJump = False  # Disable double jump
                    # Move player together with platform
                    if platform.moveX != 0:
                        self.rect.x += platform.direction

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
                if tile == 7:
                    platform = Platform(columnCount * tileSize, rowCount * tileSize, 1, 0) # Horizontal moving platforms
                    platformGroup.add(platform)
                if tile == 8:
                    platform = Platform(columnCount * tileSize, rowCount * tileSize, 0, 1) # Vertical moving platforms
                    platformGroup.add(platform)
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


########## PLATFORMS ##########

class Platform(pygame.sprite.Sprite):
        def __init__(self, x, y, moveX, moveY):
            pygame.sprite.Sprite.__init__(self)
            platformImage= pygame.image.load('assets/platform.png')
            self.image = pygame.transform.scale(platformImage, (tileSize, tileSize // 2))
            self.rect = self.image.get_rect()
            self.rect.x = x
            self.rect.y = y
            self.direction = 1
            self.counter = 0
            self.moveX = moveX
            self.moveY = moveY

# Override update method to make platforms moves
        def update(self):
            self.rect.x += self.direction * self.moveX
            self.rect.y += self.direction * self.moveY
            self.counter += 1
            if abs(self.counter) > 40:
                self.direction *= -1
                self.counter *=-1


########## MAIN GAME ##########

# Connect to database
connection = createConnection("scoredb.sqlite")

# Create DB table if not exists
executeQuery(connection, createUserTable)

# Create Player instance
player = Player(tileSize, screenHeight-100)

# Create Sprite Group
enemyGroup = pygame.sprite.Group()
garbageGroup = pygame.sprite.Group()
cansGroup = pygame.sprite.Group()
recycleBinGroup = pygame.sprite.Group()
platformGroup = pygame.sprite.Group()

# Creare Buttons instances
restartButton = Button(screenWidth // 2 - 50, screenHeight // 2 + 100, restartImage)
startButton = Button(screenWidth // 2 - 340, screenHeight // 2, startImage)
exitButton = Button(screenWidth // 2 + 70, screenHeight // 2, exitImage)

# Check if levelIndex is inside the levelList and start the game
if levelIndex < len(levelList):
    world = World(levelList[levelIndex])
    runGame = True
else:
    print("Level index is outside the levelList")
    runGame = False

# Game Loop
while runGame:
    clock.tick(FPS)

    screen.blit(bgImage, (0, 0))
    drawText('Recycle Ranger', msgFont, BROWN, 130, 150)

    if mainMenu == True:
        playerName = inputName(playerName)
        if startButton.draw():
            mainMenu = False
            if playerName == "":
                playerName =  "No Name"
            startTime = pygame.time.get_ticks() # Start counter time
        if exitButton.draw():
            runGame = False
    else:
        world.drawWorld(screen)          
        if gameState == "Playing":
            elapsedTime = (pygame.time.get_ticks() - startTime) / 1000  # Timer - Convert to seconds
            enemyGroup.update()
            platformGroup.update()
            if pygame.sprite.spritecollide(player, cansGroup, True):
                pickupSound.play()
                cansScore += 1
            drawText('Player: ' + playerName, scoreFont, WHITE, 40, 10)
            drawText('Score: ' + str(cansScore), scoreFont, WHITE, 350, 10)
            drawText(f"Time: {elapsedTime:.1f}", scoreFont, WHITE, 550, 10)
            
        
        enemyGroup.draw(screen)
        garbageGroup.draw(screen)
        cansGroup.draw(screen)
        recycleBinGroup.draw(screen)
        platformGroup.draw(screen)
        gameState = player.update(gameState)

        if gameState == "GameOver":
            drawText('GAME OVER', msgFont, RED, screenWidth // 2 -180, screenHeight // 2)
            if restartButton.draw():
                world = resetLevel(levelIndex)
                player = Player(tileSize, screenHeight-100)
                gameState = "Playing"
                cansScore = 0

        if gameState == "NextLevel":
            levelIndex += 1
            if levelIndex <= maxLevel:
                world = resetLevel(levelIndex)
                player = Player(tileSize, screenHeight-100)
                gameState = "Playing"
            else:
                drawText('YOU WIN', msgFont, BLUE, screenWidth // 2 - 140, screenHeight // 2)
                drawText('Score: ' + str(cansScore), scoreMsgFont, BROWN, screenWidth // 2 - 120, screenHeight // 2 - 80)
                drawText(f"Time: {elapsedTime:.2f}", scoreMsgFont, BROWN, screenWidth // 2 - 150, screenHeight // 2 - 150)
                addPlayerScore = f"INSERT INTO highscores(playername, score, time) VALUES ('{playerName}', '{cansScore}', '{elapsedTime:.2f}')"
                if dbWriteState:
                    executeQuery(connection, addPlayerScore)
                    dbexport = executeReadQuery(connection, selectHighScores) # Return the 3 best scores
                    print(dbexport)
                    dbWriteState = False # Flag to write only once to the database
                scoreBoard() # Show high scores board
                if restartButton.draw():
                    levelIndex = 0
                    world = resetLevel(levelIndex)
                    player = Player(tileSize, screenHeight-100)
                    cansScore = 0
                    elapsedTime = 0 # Reset Timer
                    startTime = pygame.time.get_ticks() # Reset timer
                    gameState = "Playing"
                    dbWriteState = True
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            runGame = False
    
    pygame.display.update()
    
pygame.quit()
sys.exit()