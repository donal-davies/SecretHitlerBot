import random
import asyncio

class gamedata:

    def __init__(self):

        self.RATIOS = {2 : 0, 3 : 1, 5 : 3, 6 : 4, 7 : 4, 8 : 5, 9 : 5, 10 : 6}
        
        self.activePlayers = []
        self.players = 0
        self.owner = None

        self.curPresident = None
        self.lastPresident = None
        self.curChancellor  = None
        self.lastChancellor = None

        self.votes = {}

        self.roles = {"hitler" : [], "fascist" : [], "liberal" : []}

        self.phase = 0

        self.libCards = 0
        self.fasCards = 0
        self.electionTracker = 0

        self.yayVotes = 0
        self.nayVotes = 0

        self.deck = ["liberal"]*6 + ["fascist"]*11
        self.discard = []
        self.curHand = []

        self.naturalPresident = True
        self.nextInLine = -1

        self.turn = 0

    def reshuffle(self):
        self.deck += self.discard
        self.discard = []
        random.shuffle(self.deck)

    def remove_card(self,index):
        self.discard.append(self.curHand[index])
        self.curHand.remove(self.curHand[index])

    def __str__(self):
        return "Election Tracker: "+str(self.electionTracker)+"\n"+"Liberal Policies: "+str(self.libCards)+"\n"+"Fascist Policies: "+str(self.fasCards)+"\n"+"Cards in deck: "+str(len(self.deck))

    def add_player(self,player):
        if len(self.activePlayers) == 0:
            self.owner = player
        self.activePlayers.append(player)
        self.players += 1

    def handle_veto(self):
        self.discard += self.curHand
        self.curHand = []

    def build(self):
        random.shuffle(self.deck)

        possibleRoles = ['liberal' for i in range(self.RATIOS[self.players])] + ['fascist' for i in range(self.players - self.RATIOS[self.players] - 1)] + ['hitler']
        random.shuffle(possibleRoles)

        for i in range(self.players):
            user = self.activePlayers[i]
            role = possibleRoles[i]

            self.roles[role].append(user)
        self.phase = 2

    def advance_president(self):
        self.yayVotes = self.nayVotes = 0
        self.turn += 1

        if not self.naturalPresident:
            self.curPresident = self.nextInLine

        self.lastChancellor = self.curChancellor
        self.curChancellor = None

        if self.curPresident == None:
            self.curPresident = self.activePlayers[random.randint(0,self.players-1)]
        
        else:
            self.lastPresident = self.curPresident
            if self.activePlayers.index(self.curPresident) == len(self.activePlayers)-1:
                self.curPresident = self.activePlayers[0]
            else:
                self.curPresident = self.activePlayers[ self.activePlayers.index(self.curPresident)+1 ]

        if self.turn == 1: return ""
        else:
            if self.lastChancellor == None: return self.lastPresident.mention
            else:
                return self.lastPresident.mention+" or "+self.lastChancellor.mention

    def handle_chaos(self):
        self.electionTracker += 1
        if self.electionTracker == 3:
            self.electionTracker = 0
            if len(self.deck) <= 3: self.reshuffle()
            dealt_card = self.deck.pop()
            if dealt_card == 'fascist': self.fasCards += 1
            else: self.libCards += 1

            return dealt_card
        else: return None

    def president_selection(self):
        if len(self.deck) <= 3: self.reshuffle()
        self.curHand = [self.deck.pop() for i in range(3)]

    def deal_hand(self):
        card = self.curHand[0]
        self.curHand = []
        if card == 'liberal':
            self.libCards += 1
        else: self.fasCards += 1
        return card

    def execute_player(self,player):
        self.activePlayers.remove(player)
        if player in self.roles["fascist"]: self.roles["fascist"].remove(player)
        else: self.roles["liberal"].remove(player)
