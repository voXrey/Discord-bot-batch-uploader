import json
import os
import shutil
from os import listdir, makedirs, scandir
from os.path import exists, isfile, join

import aiohttp
import discord
from discord import SyncWebhook
from discord.ext import commands


def verifyDir(dirpath:str):
    if not exists(dirpath):
        makedirs(dirpath)

def getFromJson(filepath:str):
    with open(filepath, "r", encoding="utf-8") as read_file:
        data = json.load(read_file)
    return data

def dumpToJson(filepath:str, data:dict):
    with open(filepath, "w", encoding="utf-8") as write_file:
        json.dump(data, write_file)

def sort(filespath:list[str], option:str, reverse:bool):
    if option == "size":
        filespath = sorted(
            filespath,
            key = lambda x: os.stat(x).st_size
        )

    if reverse: filespath.reverse()
    return filespath

async def createWebhook(channel:discord.TextChannel, bot:commands.Bot):
    return await channel.create_webhook(
        name=bot.user.name,
        avatar=bot.user.avatar,
        reason="webhook to send pictures"
    )

async def getOrCreateWebhook(channel:discord.TextChannel, bot:commands.Bot):
    webhooks = await channel.webhooks()
    webhook = None
    if len(webhooks) == 0:
        webhook = await createWebhook(channel, bot)
    else:
        for webhook_ in webhooks:
            if webhook_.user.id == bot.user.id:
                webhook = webhook_
                break
    
    if webhook is None: webhook = await createWebhook(channel, bot)
    return webhook  


config = getFromJson("./config.json")

bot = commands.Bot(command_prefix=config["PREFIX"])


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name =f"{bot.command_prefix}post"))
    print(discord.__version__)


@bot.command(name="post")
async def post(ctx, categorie:discord.CategoryChannel):
    settings = getFromJson("./settings.json")
    PICTURES_DIR = settings["pictures-dir"]

    # get all subdirs
    verifyDir(PICTURES_DIR)
    subdirs = [f for f in scandir(PICTURES_DIR) if f.is_dir()]

    errors = []
    max_pictures = 0
    for subdir in subdirs: max_pictures += len([f for f in scandir(subdir) if f.is_file()])
    pictures_count = 0

    # create channel 
    for subdir in subdirs:
        subdir_channel = discord.utils.get(categorie.text_channels, name=subdir.name)
        if subdir_channel is None:
            subdir_channel = await categorie.create_text_channel(subdir.name)
        
        # get or create webhook
        webhook = await getOrCreateWebhook(subdir_channel, bot)

        # get all subdir's pictures
        pictures = [join(subdir.path, f) for f in listdir(subdir.path) if isfile(join(subdir.path, f))]
        if settings["sort"]: pictures = sort(pictures, settings["sort-by"], settings["sort-reverse"])
        
        # post pictures
        for picture in pictures:
            pictures_count+=1
            try:
                await webhook.send(file=discord.File(picture))

                # move picture if move setting is true
                if settings["move"]:
                    MOVE_DIR = settings["move-dir"]
                    verifyDir(MOVE_DIR)
                    dst = join(MOVE_DIR, subdir.name)
                    verifyDir(dst)
                    shutil.move(picture, dst)
                
                #  delete picture if delete setting is true and picture setting is false
                elif settings["delete"]:
                    os.remove(picture)

            except Exception as e:
                errors.append((picture, e))
    
    # send result
    await ctx.send(f"{pictures_count-len(errors)}/{pictures_count} images posted")
    for error in errors: print(error)


if __name__ == '__main__':
    bot.run(config["TOKEN"])
