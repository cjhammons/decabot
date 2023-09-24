import discord
from discord.ext import commands
import random
import configparser
import logging
import requests
import json 

# setup discord client  
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s - %(message)s')
logging.info('Starting decabot')
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
config = configparser.ConfigParser()
config.read('config-decabot.ini')

logging.info(f'Loaded config: {config}')
logging.info(f'Config Sections: {config.sections()}')
nommer_api_key = config['nommer']['api_key']


def roll_dice(dice, difficulty, initiative):
    logging.info(f'Rolling {dice} dice with {difficulty} difficulty.')
    rolls = []
    cancellations = []

    botches = 0
    # Roll the initial dice
    for _ in range(dice):
        roll = random.randint(1, 10)
        rolls.append(roll)

    if initiative is None:
    # Count the number of 1s and their impact on successes
        ones = rolls.count(1)
        while ones > 0:
            botches += 1
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
            elif extra_roll == 1:
                botches += 1
            tens -= 1

    # Return all rolls (including cancelled ones) and extra rolls
    return sorted(rolls + [pair for sublist in cancellations for pair in sublist], reverse=True), sorted(extra_rolls, reverse=True), botches

def send_to_nommer(ctx, rolls, successes, botches, extra_rolls, message):
    payload = {
        "event": {
            "author_id": ctx.author.id,
            "author_name": ctx.author.display_name,
            "author_nickname": ctx.author.nick,
            "rolls": rolls,
            "successes": successes,
            "botches": botches,
            "extra_rolls": extra_rolls,
            "message": message
        }
    }
    json_payload = json.dumps(payload)
    logging.info(f'Sending payload to nommer: {payload}')
    try:
        url = f'http://{config["nommer"]["url"]}/1/{config["nommer"]["project"]}/event'
        logging.info(f'POST {url}')
        response = requests.post(
            url,
            headers={
                'X-API-Key': nommer_api_key,
                'Content-Type': 'application/json'
                },
            data=json_payload
        )
        if response.status_code not in [200, 201]:
            logging.error(f'Error sending payload to nommer: {response.text}')
    except Exception as e:
        logging.error(f'Error sending payload to nommer: {e}')

@bot.command(name='roll', help='Rolls a White Wolf dice pool. Syntax: !roll [number of dice](required, int) [difficulty](required, int) [initiative](optional, boolean)')
async def roll(ctx, dice: int, difficulty: int = -1, initiative: str = None):
    all_rolls, extra_rolls, botches = roll_dice(dice, difficulty, initiative)  # Roll the dice
    successes = len([d for d in all_rolls if d >= difficulty]) + len([d for d in extra_rolls if d >= difficulty]) - botches # Count successes
    
    s = 'MESSAGE: '

    if initiative is not None:
        s = f'{ctx.message.author.mention} rolled: {all_rolls}.\nYou have {successes} initiative.'
    # Handle botches (all dice showing 1)
    elif all(d == 1 for d in all_rolls):
        s = f'{ctx.message.author.mention} rolled: {all_rolls}.\nOh no, a botch!'
    else:
        if extra_rolls:
            s = f'{ctx.message.author.mention} rolled: {all_rolls} with extra rolls: {extra_rolls}.'
        else:
            s = f'{ctx.message.author.mention} rolled: {all_rolls}.'
        if difficulty > 0:
            s += f'\nYou have {successes} successes.'
        
    await ctx.send(s)
    logging.info(s)

    # send_to_nommer(ctx.message.author.id, ctx.message.author.display_name, all_rolls, successes, botches, extra_rolls, s)
    send_to_nommer(ctx, all_rolls, successes, botches, extra_rolls, ctx.message.content)

# Run the bot with your token
bot.run(config['discord']['token'])
