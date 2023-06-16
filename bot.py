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

def roll_dice(dice, difficulty):
    rolls = []
    cancellations = []

    # Roll the initial dice
    for _ in range(dice):
        roll = random.randint(1, 10)
        rolls.append(roll)

    # Count the number of 1s and their impact on successes
    ones = rolls.count(1)
    while ones > 0:
        highest_remaining_success = max((roll for roll in rolls if roll >= difficulty), default=None)
        if highest_remaining_success is not None:
            rolls.remove(1)
            rolls.remove(highest_remaining_success)
            cancellations.append((1, highest_remaining_success))
            ones -= 1
        else:
            break

    # Roll extra dice for each 10, and continue to roll as long as 10s are being rolled
    extra_rolls = []
    tens = rolls.count(10)
    while tens > 0:
        for _ in range(tens):
            extra_roll = random.randint(1, 10)
            extra_rolls.append(extra_roll)
            if extra_roll == 10:
                tens += 1
            tens -= 1

    # Return all rolls (including cancelled ones) and extra rolls
    return sorted(rolls + [pair for sublist in cancellations for pair in sublist], reverse=True), sorted(extra_rolls, reverse=True)

@bot.command(name='roll', help='Rolls a White Wolf dice pool. Syntax: !roll [number of dice] [difficulty]')
async def roll(ctx, dice: int, difficulty: int = -1):
    all_rolls, extra_rolls = roll_dice(dice, difficulty)  # Roll the dice
    successes = len([d for d in all_rolls if d >= difficulty and d != 1]) - all_rolls.count(1)  # Count successes

    # if no dficulty is specified, just return the rolls
    if difficulty < 1:
        await ctx.send(f'{ctx.message.author.mention} rolled: {all_rolls}')
        return 

    # Handle botches (all dice showing 1)
    if all(d == 1 for d in all_rolls):
        await ctx.send(f'{ctx.message.author.mention} rolled: {all_rolls}.\nOh no, a botch!')
    else:
        if extra_rolls:
            await ctx.send(f'{ctx.message.author.mention} rolled: {all_rolls} with extra rolls: {extra_rolls}.\nYou have {successes} successes.')
        else:
            await ctx.send(f'{ctx.message.author.mention} rolled: {all_rolls}.\nYou have {successes} successes.')


# Run the bot with your token
bot.run(config['discord']['token'])
