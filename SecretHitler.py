#TODO VETO
#TODO DM FASCISTS INFO?

import discord
import random
import asyncio
import gamedata

TOKEN = 'TOKEN-HERE'
RATIOS = {2 : 0, 3 : 1, 5 : 3, 6 : 4, 7 : 4, 8 : 5, 9 : 5, 10 : 6}
TRACK = {}

START = "It's sunset in Germany. Whichever flowers bloom during the night in Germany have begun to bloom... and two groups of government are conspiring to overthrow one another."

client = discord.Client()

game = gamedata.gamedata()

@client.event
async def on_message(message):
    global game
    channel = message.channel
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return 

    #------------GENERAL-----------------------------------------#
    if message.content.lower().startswith('!state'):
        await message.channel.send(str(game))

    if message.content.lower().startswith('!owner'):
        await message.channel.send(game.owner.mention)

    if message.content.lower().startswith('!voters'):
        hasntvoted = []
        for user in game.activePlayers:
            if user not in game.votes.keys() and user not in [game.curPresident, game.curChancellor]: hasntvoted.append(user.mention)
        await message.channel.send("Oi, "+str(hasntvoted)[1:-1]+", vote.")

    #------------PHASE 0-1: CONSTRUCTION---------------------------#
    if game.phase == 0:
        if message.content.lower().startswith('begin'):
            await message.channel.send("A new game is beginning! Say 'join' to enter.")
            game.phase = 1
            game.add_player(message.author)
            await reset_permissions()
            
    elif game.phase == 1:
        if message.content.lower().startswith('join'):
            if game.players == 10:
                await message.channel.send("There are too many players, you cannot join now")
            elif message.author in game.activePlayers:
                await message.channel.send(message.author.mention + ", you are already a member of the game!")
            else:
                await message.channel.send("Welcome to the game, "+message.author.mention)
                game.add_player(message.author)

        #elif message.content.lower().startswith('add'): #!
        #    await message.channel.send(message.mentions[0].mention+" added to the game!")
        #    game.add_player(message.mentions[0])
                
        if message.content.lower().startswith('ready') and message.author == game.owner: 
            if game.players < min(RATIOS.keys()):
                await message.channel.send("Not enough players")
            else:
                await message.channel.send(START)
                game.build()
                await assign_players()
                await inform_roles()
                await update_fascists()
                await inform_president(game.advance_president())
                
    #------------PHASE 2: NOMINATION---------------------------#
    elif game.phase == 2:
        if message.content.lower().startswith('nominate') and (message.author == game.curPresident):
            if len(message.mentions) != 1:
                await message.channel.send("You must nominate one person.")
            elif message.mentions[0] == game.curPresident:
                await message.channel.send("You cannot nominate yourself.")
            elif not message.mentions[0] in game.activePlayers:
                await message.channel.send("That player is not a member of the game.")
            elif message.mentions[0] in [game.lastPresident, game.lastChancellor]:
                await message.channel.send("That player is ineligible to be Chancellor.")
            else:
                await message.channel.send(message.mentions[0].mention+" has been nominated as Chancellor! Your votes will be collected now.")
                game.lastChancellor = game.curChancellor
                game.curChancellor = message.mentions[0]
                game.phase = 3
                await inform_voter()

    #-------------PHASE 3: ELECTION----------------------------#
    elif game.phase == 3 and message.author not in game.votes.keys() and message.author not in [game.curPresident, game.curChancellor]:
        if message.content.lower() == 'yay':
            game.yayVotes += 1
            game.votes[message.author] = 'yay'
        elif message.content.lower() == 'nay':
            game.nayVotes += 1
            game.votes[message.author] = 'nay'
        else:
            return

        if game.yayVotes + game.nayVotes == len(game.activePlayers) - 2:
            voter = {}
            for vote in game.votes.keys():
                voter[vote.display_name] = game.votes[vote]
            await client.get_channel(697814656831717429).send(str(voter)[1:-1].replace("'", "").replace(","," |"))
            game.votes = {}
            if game.yayVotes > game.nayVotes:
                await client.get_channel(697814656831717429).send("The election was a success! " +game.curChancellor.mention+" is now the chancellor!")
                if game.fasCards >= 3 and game.roles["hitler"][0] == game.curChancellor:
                    await client.get_channel(697814656831717429).send("Hitler was elected as chancellor! The fascists have won!")
                    await refresh_game()
                else:
                    game.phase = 4
                    game.president_selection()
                    await inform_president_selection()
            else:
                game.curChancellor = None
                await client.get_channel(697814656831717429).send("The election was a failure! We shall now select a new president.")

                dealt_card = game.handle_chaos()
                if dealt_card != None:
                    await client.get_channel(697814656831717429).send("The government is in chaos, a policy will be put into play!")
                    await deal_card(dealt_card)
                else:
                    await inform_president(game.advance_president())
                    game.phase = 2
                        
                
    #-------------PHASE 4: PRESIDENT'S SELECTION---------------------#
    elif game.phase == 4 and message.author == game.curPresident:
        if message.content.lower().startswith("discard"):
            val = message.content.split(" ")
            if len(val) != 2:
                await message.channel.send("Invalid number of arguments given. Please enter one number")
            elif not val[1].isnumeric():
                await message.channel.send("Invalid input. Please give a number")
            elif int(val[1]) < 1 or int(val[1]) > 3:
                await message.channel.send("Invalid input. Please enter a number between 1 and 3")
            else:
                game.remove_card(int(val[1]) - 1)
                await inform_chancellor_selection()
                game.phase = 5

    #-------------PHASE 5: CHANCELLORS'S SELECTION---------------------#
    elif game.phase == 5 and message.author == game.curChancellor:
        if message.content.startswith("discard"):
            val = message.content.split(" ")
            if len(val) != 2:
                await message.channel.send("Invalid number of arguments given. Please enter one number")
            elif not val[1].isnumeric():
                await message.channel.send("Invalid input. Please give a number")
            elif int(val[1]) < 1 or int(val[1]) > 2:
                await message.channel.send("Invalid input. Please enter either 1 or 2")
            else: 
                game.remove_card(int(val[1]) - 1)
                await deal_card(game.deal_hand())
                await client.get_channel(697814656831717429).send(str(game))
        if message.content.startswith("veto") and message.channel == client.get_channel(697814656831717429):
            await do_veto()

    elif game.phase == 9:
        if message.content.startswith("veto") and message.author == game.curPresident and message.channel == client.get_channel(697814656831717429):
            game.handle_veto()
            game.phase = 2
            await message.channel.send("The veto has been approved! We shall now move on to the next term")
            await inform_president(game.advance_president())
            
        elif message.content.startswith("cancel") and message.author == game.curChancellor and message.channel == client.get_channel(697814656831717429):
            await message.channel.send("The chancellor has cancelled the veto!")
            game.phase = 5

    #-------------PHASE 5-7: ADDITIONAL ACTIONS-----------------#
    elif game.phase == 6:
        if message.content.startswith("execute") and message.author == game.curPresident:
            if len(message.mentions) != 1:
                await message.channel.send("You must select one person.")
            elif message.mentions[0] == game.curPresident:
                await message.channel.send("You cannot select yourself.")
            elif not message.mentions[0] in game.activePlayers:
                await message.channel.send("That player is not a member of the game.")
            else:
                await message.channel.send(message.mentions[0].mention+" has been executed by the president!")
                if game.roles["hitler"][0] == message.mentions[0]:
                    await message.channel.send("Hitler has been slain! The liberals have won!")
                    await refresh_game()
                else:
                    game.execute_player(message.mentions[0])
                    await message.mentions[0].add_roles(client.get_guild(697814656831717426).get_role(698323720044937237))
                    await message.mentions[0].remove_roles(client.get_guild(697814656831717426).get_role(698323685253054534))
                    game.phase = 2
                    await inform_president(game.advance_president())

    elif game.phase == 7:
        if message.content.startswith("investigate") and message.author == game.curPresident:
            if len(message.mentions) != 1:
                await message.channel.send("You must select one person.")
            elif message.mentions[0] == game.curPresident:
                await message.channel.send("You cannot select yourself.")
            elif not message.mentions[0] in game.activePlayers:
                await message.channel.send("That player is not a member of the game.")
            else:
                if message.mentions[0] in game.roles["fascist"] or message.mentions[0] in game.roles["hitler"]:
                    await message.author.send(message.mentions[0].mention+" is a fascist!")
                else:
                    await message.author.send(message.mentions[0].mention+" is a liberal!")
                game.phase = 2
                await inform_president(game.advance_president())

    elif game.phase == 8:
        if message.content.startswith("select") and message.author == game.curPresident:
            if len(message.mentions) != 1:
                await message.channel.send("You must select one person.")
            elif not message.mentions[0] in game.activePlayers:
                await message.channel.send("That player is not a member of the game.")
            else:
                game.naturalPresident = False
                game.nextInLine = game.curPresident
                game.lastPresident = game.curPresident
                game.lastChancellor = game.curChancellor
                game.curChancellor = None
                game.curPresident = message.mentions[0]
                game.yayVotes = game.nayVotes = 0
                game.turn += 1

                ineligible = ""
                if game.lastPresident == None: ineligible = ""
                else:
                    if game.lastChancellor == None: ineligible = game.lastPresident.mention
                    else:
                        ineligible = game.lastPresident.mention+" or "+game.lastChancellor.mention
                        
                await inform_president(ineligible)
                game.phase = 2

#----------------
#Removes all permissions in non-general channels
async def reset_permissions():
    for user in client.get_guild(697814656831717426).members:
        await user.remove_roles(client.get_guild(697814656831717426).get_role(698323685253054534),client.get_guild(697814656831717426).get_role(698323720044937237))

#Provides fascists with the necessary permissions
async def update_fascists():
    global game
    fascists = []
    for user in game.roles["fascist"]:
        fascists.append(user.display_name)
        
    if game.players < 7:
        for user in game.roles["fascist"] + game.roles["hitler"]:
            await user.send("Your fellow fascists are: "+str(fascists)[1:-1])
            if user not in game.roles["hitler"]:
                await user.send(game.roles["hitler"][0].mention+" is Hitler!")

    else:
        for user in game.roles["fascist"]:
            await user.send("Your fellow fascists are: "+str(fascists)[1:-1])
            await user.send(game.roles["hitler"][0].mention+" is Hitler!")

#Messages all players to inform them of their roles
async def inform_roles():
    global game
    for user in game.roles["hitler"]:
        await user.send("You are Hitler! It's up to you to bring Germany into a golden era!")
    for user in game.roles["fascist"]:
        await user.send("You are a Fascist! You must support Hitler until your dying breath!")
    for user in game.roles["liberal"]:
        await user.send("You are a Liberal! Defend the sanctity of our beautiful country!")

#Informs the new president of their term
async def inform_president(invalid):
    global game
    await client.get_channel(697814656831717429).send("----------------------------------------------")
    if invalid == "":
        await client.get_channel(697814656831717429).send(game.curPresident.mention + ", you are the new President! Enter 'nominate @x' to nominate a chancellor for "+
                                                                "election.")
    else:
        await client.get_channel(697814656831717429).send(game.curPresident.mention + ", you are the new President! Enter 'nominate @x' to nominate a chancellor for "+
                                                                "election. You may not nominate "+invalid+".")

#Informs the current voter of their obligation to the country
async def inform_voter():
    global game
    for user in game.activePlayers:
        if user not in [game.curPresident, game.curChancellor]:
            await user.send("You may now cast your vote for"+game.curChancellor.mention+"! Please say either yay or nay")

#Handles the implementation of a new policy
async def deal_card(newPolicy):
    global game
    if newPolicy == 'liberal':
        await client.get_channel(697814656831717429).send("A liberal policy was put into play! There are now "+str(game.libCards)+" liberal policies.")
        if game.libCards == 5:
            await client.get_channel(697814656831717429).send("The liberals have won over the government. They are victorious!")
            await refresh_game()
        else:
            game.phase = 2
            await inform_president(game.advance_president())
    else:
        await client.get_channel(697814656831717429).send("A fascist policy was put into play! There are now "+str(game.fasCards)+" fascist policies.")
        if game.fasCards == 6:
            await client.get_channel(697814656831717429).send("The fascists have won over the government. They are victorious!")
            await refresh_game()
        else:
            if TRACK[game.players][game.fasCards - 1] != None:
                await TRACK[game.players][game.fasCards - 1]()
            else:
                game.phase = 2
                await inform_president(game.advance_president())

#Inform the president that he can select policies
async def inform_president_selection():
    global game
    await game.curPresident.send("\n1: "+game.curHand[0]+"\n2: "+game.curHand[1]+"\n3: "+
                                                      game.curHand[2]+"\nPlease enter 'discard x' to remove the card of your choice")

#Inform the chancellor that he can select a policy
async def inform_chancellor_selection():
    global game
    await game.curChancellor.send("\n1: "+game.curHand[0]+"\n2: "+
                                                      game.curHand[1]+"\nPlease enter 'discard x' to remove the card of your choice")


#Grants the president the power to select the next president
async def select():
    global game
    await client.get_channel(697814656831717429).send(game.curPresident.mention+", you may now select the next president! Enter 'select @x' to make your selection")
    game.phase = 8

#Grants the president the power to investigate a player
async def invest():
    global game
    await client.get_channel(697814656831717429).send(game.curPresident.mention+", you may now investigate a member of government! Enter 'investigate @x' to make your selection")
    game.phase = 7

#Grants the president the power to execute a player
async def execute():
    global game
    await client.get_channel(697814656831717429).send(game.curPresident.mention+", you may now execute a member of government! Enter 'execute @x' to make your selection")
    game.phase = 6

#Grants the president a peek at the next three cards
async def peek():
    global game
    if len(game.deck) <= 3:
        game.reshuffle()
    peekDeck = game.deck[len(game.deck)-1 : len(game.deck)-4 : -1]
    await game.curPresident.send("The top three cards are "+str(peekDeck))
    game.phase = 2
    await inform_president(game.advance_president())

#Resets the game
async def refresh_game():
    global game
    fascists = []
    liberals = []
    for user in game.roles['fascist']:
        fascists.append(user.display_name)
    for user in game.roles['liberal']:
        liberals.append(user.display_name)

    await client.get_channel(697814656831717429).send("The fascists were: "+str(fascists)[1:-1].replace("'",""))
    await client.get_channel(697814656831717429).send("The liberals were: "+str(liberals)[1:-1].replace("'",""))
    await client.get_channel(697814656831717429).send("Hitler was: "+game.roles["hitler"][0].display_name)
    game = gamedata.gamedata()
    await reset_permissions()

#Assings the 'Playing' role to all players
async def assign_players():
    global game
    for user in game.activePlayers:
        await user.add_roles(client.get_guild(697814656831717426).get_role(698323685253054534))

async def do_veto():
    await client.get_channel(697814656831717429).send(game.curPresident.mention+", your chancellor has called for a veto of the current policies. Enter 'veto' to accept")
    game.phase = 9

#----------------


TRACK = {5 : [None]*2 + [peek] + [execute]*2, 6 : [None]*2 + [peek] + [execute]*2, 7 : [None] + [invest] + [select] + [execute]*2, 8 : [None] + [invest] + [select] + [execute]*2,
         9 : [invest]*2 + [select] + [execute]*2, 10 : [invest]*2 + [select] + [execute]*2}

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(TOKEN)
