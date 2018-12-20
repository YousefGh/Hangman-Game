import socket
import sys

def Main():
    if len(sys.argv) < 3:
        print("Please enter the IP and PORT number ")
        sys.exit()

    ip = str(sys.argv[1])
    port = int(sys.argv[2])
    print('Client running on Host ' + ip + '| Port ' + str(port))

    s = socket.socket()
    s.connect((ip, port))

    print("Two Players? (y/n)")
    print(">>", end='')
    msg = input().lower()

    while 1:
        if msg == 'y' or msg == 'n':
            break
        msg = input('Please enter either y (Yes) or n (No)')

    if msg == 'y':
        # Signal game start (2P)
        twoPlayerSignal = '2'.encode('utf-8')
        s.send(twoPlayerSignal)
        playGame(s)

    else:
        # Signal game (1P)
        twoPlayerSignal = '0'.encode('utf-8')
        s.send(twoPlayerSignal)

        print("One Player Game Started")
        playGame(s)

def recv_helper(socket):
    first_byte_value = int(socket.recv(1)[0])
    if first_byte_value == 0:
        x, y = socket.recv(2)
        return 0, socket.recv(int(x)), socket.recv(int(y))
    else:
        return 1, socket.recv(first_byte_value)

def playGame(s):
    while True:
        pkt = recv_helper(s)
        msgFlag = pkt[0]
        if msgFlag != 0:
            msg = pkt[1].decode('utf8')
            print(msg)
            if msg == 'server-overloaded' or 'Game Over!' in msg:
                break
        else:
            gameString = pkt[1].decode('utf8')
            incorrectGuesses = pkt[2].decode('utf8')
            print(" ".join(list(gameString)))
            print("Incorrect Guesses: " + " ".join(incorrectGuesses) + "\n")
            if "_" not in gameString or len(incorrectGuesses) >= 6:
                continue
            else:
                letterGuessed = ''
                valid = False
                while not valid:
                    letterGuessed = input('Letter to guess: ').lower()
                    if letterGuessed in incorrectGuesses or letterGuessed in gameString:
                        print("Error! Letter " + letterGuessed.upper() + " has been guessed before, please guess another letter.")
                    elif len(letterGuessed) > 1 or not letterGuessed.isalpha():
                        print("Error! Please guess one letter")
                    else:
                        valid = True
                msg = bytes([len(letterGuessed)]) + bytes(letterGuessed, 'utf8')
                s.send(msg)

    s.shutdown(socket.SHUT_RDWR)
    s.close()


if __name__ == '__main__':
    Main()
