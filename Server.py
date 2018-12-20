import socket
from _thread import *
import sys
import random
clientNumber = 0  # Total number of clients
words = [
    'muscle', 'cat', 'board', 'body', 'love',
    'car', 'strict', 'addition', 'health', 'ball',
    'dog', 'sick', 'cold', 'coffee', 'real'
]
games = []

class Game:
    word = ""
    gameString = ""
    incorrectGuesses = 0
    incorrectLetters = 0
    turn = 1
    lock = 0
    full = False

    def __init__(self, word, num_players_requested):
        self.incorrectLetters = []
        self.lock = allocate_lock()
        self.word = word
        for i in range(len(word)):
            self.gameString += "_"
        if num_players_requested == 1:
            self.full = True

    def getStatus(self):
        if self.incorrectGuesses >= 6:
            return 'You Lose :('
        elif not '_' in self.gameString:
            return 'You Win!'
        else:
            return ''

    def guess(self, letter):
        if letter not in self.word or letter in self.gameString:
            self.incorrectGuesses += 1
            self.incorrectLetters.append(letter)
            return 'Incorrect!'
        else:
            gameString = list(self.gameString)
            for i in range(len(self.word)):
                if self.word[i] == letter:
                    gameString[i] = letter
            self.gameString = ''.join(gameString)
            return 'Correct!'

    def changeTurn(self):
        if self.turn == 1:
            self.turn = 2
        else:
            self.turn = 1


def Main():
    global clientNumber
    global words

    # Set up the server
    #########################################
    ip = '127.0.0.1'
    if len(sys.argv) < 2:
        print("Please enter the PORT number ")
        sys.exit()
    port = int(sys.argv[1])

    if len(sys.argv) > 2:
        text_file = open(sys.argv[2], "r")
        words = text_file.read().split(', ')

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create TCP Socket
    print('Server running on Host ' + ip + '| Port ' + str(port))

    # Bind and Listen
    try:
        s.bind((ip, port))  # Bind to connection
    except socket.error as e:
        print(str(e))
    s.listen(6)  # Listen to X client
    ########################################
    # End

    # Start accepting Client connections
    while True:
        c, addr = s.accept()
        clientNumber += 1
        print("Connection " + str(clientNumber) + " established from: " + str(addr))
        start_new_thread(clientThread, (c,))

def getGame(num_players_requested):
    if num_players_requested == 2:
        for game in games:
            if not game.full:
                game.full = True
                return (game, 2)
    if len(games) < 3:
        word = words[random.randint(0, 14)]
        game = Game(word, num_players_requested)
        games.append(game)
        return (game, 1)
    else:
        return -1

def clientThread(c):  # Threaded client handler
    global clientNumber
                                                           # Is it a two player game? expected 2, 0
    twoPlayerSignal = c.recv(1024).decode('utf-8')

    if twoPlayerSignal == '2':
        x = getGame(2)
        if x == -1:
            send(c, 'server-overloaded')
        else:
            game, player = x
            send(c, 'Waiting for other player!')

            while not game.full:
                continue
            send(c, 'Game starting!')
            twoPlayerGame(c, player, game)

    else:
        x = getGame(1)
        if x == -1:
            send(c, 'server-overloaded')
        else:
            game, player = x
            onePlayerGame(c, game)

def send(c, msg):
    packet = bytes([len(msg)]) + bytes(msg, 'utf8')
    c.send(packet)

def send_game_control_packet(c, game):
    msgFlag = bytes([0])
    data = bytes(game.gameString + ''.join(game.incorrectLetters), 'utf8')
    gamePacket = msgFlag + bytes([len(game.word)]) + bytes([game.incorrectGuesses]) + data
    c.send(gamePacket)

def twoPlayerGame(c, player, game):
    global clientNumber                                                  # SEND_2 >>> Player Number

    while True:
        while game.turn != player:
            continue
        game.lock.acquire()

        status = game.getStatus()
        if status != '':
            send_game_control_packet(c, game)
            send(c, status)
            send(c, "Game Over!")
            game.changeTurn()
            game.lock.release()
            break

        send(c, 'Your Turn!')

        send_game_control_packet(c, game)

        rcvd = c.recv(1024)
        letterGuessed = bytes([rcvd[1]]).decode('utf-8')

        send(c, game.guess(letterGuessed))

        status = game.getStatus()
        if len(status) > 0:
            send_game_control_packet(c, game)
            send(c, status)
            send(c, "Game Over!")
            game.changeTurn()
            game.lock.release()
            break

        send(c, "Waiting on other player...")
        game.changeTurn()
        game.lock.release()

    if game in games:
        games.remove(game)
    c.close()
    clientNumber -= 1


def onePlayerGame(c, game):
    global clientNumber

    while True:
        send_game_control_packet(c, game)

        rcvd = c.recv(1024)
        letterGuessed = bytes([rcvd[1]]).decode('utf-8')

        send(c, game.guess(letterGuessed))

        status = game.getStatus()
        if len(status) > 0:
            send_game_control_packet(c, game)
            send(c, status)
            send(c, "Game Over!")
            break
    games.remove(game)
    c.close()
    clientNumber -= 1



if __name__ == '__main__':
    Main()
