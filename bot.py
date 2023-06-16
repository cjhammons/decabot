import discord
from discord.ext import commands
import random
import configparser


# setup discord client  

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
config = configparser.ConfigParser()
config.read('config')

def roll_dice(dice):
    rolls = []
    extra_rolls = []
    
    for _ in range(dice):
        roll = random.randint(1, 10)
        rolls.append(roll)
        
        if roll == 10:
            extra_roll = random.randint(1, 10)
            extra_rolls.append(extra_roll)

    # Return both lists sorted in descending order
    return sorted(rolls, reverse=True), sorted(extra_rolls, reverse=True)

@bot.command(name='roll', help='Rolls a White Wolf dice pool. Syntax: !roll [number of dice] [difficulty]')
async def roll(ctx, dice: int, difficulty: int = 7):
    original_rolls, extra_rolls = roll_dice(dice)  # Roll the dice
    all_rolls = original_rolls + extra_rolls
    successes = len([d for d in all_rolls if d >= difficulty])  # Count successes

    # Handle botches (all dice showing 1)
    if all(d == 1 for d in all_rolls):
        await ctx.send(f'{ctx.message.author.mention} rolled: {all_rolls}.\nOh no, a botch!')
    else:
        if extra_rolls:
            await ctx.send(f'{ctx.message.author.mention} rolled: {original_rolls} with extra rolls: {extra_rolls}.\nYou have {successes} successes.')
        else:
            await ctx.send(f'{ctx.message.author.mention} rolled: {original_rolls}.\nYou have {successes} successes.')



# Run the bot with your token
bot.run(config['discord']['token'])
