from code import interact
import nextcord
from nextcord.ext import commands
import random
import settings

card_list = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["bj"])
    async def blackjack(self, ctx: commands.Context):
        # Initialize variables
        player_hand = random.sample(card_list, 2)
        dealer_hand = random.sample(card_list, 2)

        # Create embed
        embed = await self.embed_generator(player_hand, dealer_hand, first_turn=True)

        # Send embed
        msg = await ctx.send(embed=embed, view=Blackjack_Button(self.bot))

        # Create data for the game
        data = {
            "player_id": ctx.author.id,
            "player_hand": player_hand,
            "dealer_hand": dealer_hand,
            "channel_id": ctx.channel.id,
            "msg_id": msg.id
        }

        # Insert data into database
        await settings.collectionblackjack.insert_one(data)

    async def embed_generator(self, player_hand, dealer_hand, first_turn=False):
        player_hand_text = ""
        for i in player_hand:
            player_hand_text += f"{i} "
        
        dealer_hand_text = ""
        for i in dealer_hand:
            dealer_hand_text += f"{i} "
        
        embed = nextcord.Embed(title="Blackjack")
        embed.add_field(
            name="Your hand",
            value=f"{player_hand_text}\n\n Value: {await get_score(player_hand)}",
        )
        if first_turn:
            embed.add_field(
                name="Dealer's hand",
                value=f"{dealer_hand[0]} #\n\n Value: {await get_score([dealer_hand[0]])}",
            )
        else:
            embed.add_field(
                name="Dealer's hand",
                value=f"{dealer_hand_text}\n\n Value: {await get_score(dealer_hand)}",
            )
        return embed


    # It will come from Blackjack_Button
    async def handle_click(self, button: nextcord.ui.Button, interaction):
        if button.custom_id == "hit":
            game = await settings.collectionblackjack.find_one(
                {"player_id": interaction.user.id}
            )
            if game is not None:
                newcard = random.sample(card_list, 1)
                game["player_hand"].append(newcard[0])
                await settings.collectionblackjack.update_one(
                    {"player_id": game["player_id"]}, {"$set": game}
                )

                # call computer dealer playing function
                await Blackjack.computer_dealer_playing(self,game)
                
                #update message
                embed = await Blackjack.embed_generator(self,game["player_hand"], game["dealer_hand"])
                await Blackjack.update_message(self, game, embed, interaction)

                player_score = await get_score(game["player_hand"])
                dealer_score = await get_score(game["dealer_hand"])

                

        elif button.custom_id == "stand":
            game = await settings.collectionblackjack.find_one(
                {"player_id": interaction.user.id}
            )
            if game is not None:
                # call computer dealer playing function
                await Blackjack.computer_dealer_playing(self,game)
                
                embed = await Blackjack.embed_generator(self,game["player_hand"], game["dealer_hand"])
                await Blackjack.update_message(self, game, embed, interaction)

    async def check_win_lose_draw(self,player_score, dealer_score):
        if player_score == dealer_score == 21:
            return False,False,True #win,lose,draw
        elif player_score >= 21:
            return False,True,False
        elif dealer_score >= 21:
            return True,False,False
        
        return False,False,False


    async def computer_dealer_playing(self, game):
        action = random.randint(0, 1)

        # If the dealer has a score of 17 or less, he will hit
        if action == 0:
            newcard = random.sample(card_list, 1)
            game["dealer_hand"].append(newcard[0])
            await settings.collectionblackjack.update_one(
                {"player_id": game["player_id"]}, {"$set": game}
            )
        
        # If action = 0 then do nothing
        else:
            pass

    async def update_message(self, data, embed, interaction, remove_view=False):
        if remove_view:
            await interaction.edit(embed=embed, view=None)
        else:
            await interaction.edit(embed=embed)


async def get_score(cards: list):
    sum = 0
    for _ in range(cards.count("A")):
        if "A" in cards:
            if "J" in cards or "Q" in cards or "K" in cards:
                sum += 11
            else:
                sum += 1

    for _ in range(cards.count("J") + cards.count("Q") + cards.count("K")):
        if "J" in cards or "Q" in cards or "K" in cards:
            sum += 10

    for card in cards:
        if card not in ["A", "J", "Q", "K"]:
            sum += int(card)
    return sum


class Blackjack_Button(nextcord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @nextcord.ui.button(
        label=" Hit ",
        style=nextcord.ButtonStyle.secondary,
        custom_id="hit",
        row=0,
    )
    async def double_down(
        self, button: nextcord.ui.Button, interaction: nextcord.Interaction
    ):
        await Blackjack.handle_click(self, button, interaction)

    @nextcord.ui.button(
        label=" Stand ", style=nextcord.ButtonStyle.secondary, custom_id="stand", row=0
    )
    async def stand(
        self, button: nextcord.ui.Button, interaction: nextcord.Interaction
    ):
        await Blackjack.handle_click(self, button, interaction)


def setup(bot):
    bot.add_cog(Blackjack(bot))
