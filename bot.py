import discord
from discord.ext import commands
from os import listdir, scandir, makedirs
from os.path import isfile, join, exists
import shutil
import json

### SET OPTIONS ###
TOKEN = "TOKEN" # set your token here
PREFIX = "!"

CATEGORIE = 000000000 # set your categorie id here
PICTURES_REP = "pictures"
DONE_REP = "done"

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

bot = commands.Bot(command_prefix=PREFIX)


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name =f"{bot.command_prefix}post"))
    print(discord.__version__)


@bot.command(name="post")
async def post(ctx):
    errors = []
    pictures_count = 0

    # get the categorie
    categorie = discord.utils.get(ctx.guild.categories, id=CATEGORIE)

    # get all subdirs
    verifyDir(PICTURES_REP)
    subdirs = [f for f in scandir(PICTURES_REP) if f.is_dir()]

    # create channel 
    for subdir in subdirs:

        data = getFromJson("data.json")
        channels = [channel for channel in categorie.text_channels]

        subdir_channel = None

        exists = False
        if subdir.name in data:
            for channel in channels:
                if channel.id == data[subdir.name]:
                    subdir_channel = channel
                    exists = True
                    break

        if not exists:
            subdir_channel = await categorie.create_text_channel(subdir.name)
            data[subdir.name] = subdir_channel.id
            dumpToJson("data.json", data)
        

        # get all subdir's pictures
        pictures = [join(subdir.path, f) for f in listdir(subdir.path) if isfile(join(subdir.path, f))]
        
        # post pictures
        for picture in pictures:
            pictures_count+=1
            try:
                await subdir_channel.send(file=discord.File(picture))
                verifyDir(DONE_REP)
                dst = join(DONE_REP, subdir.name)
                verifyDir(dst)
                shutil.move(picture, dst)
            except:
                errors.append(picture)
    
    # send result
    await ctx.send(f"{pictures_count-len(errors)}/{pictures_count} images posted")
    for error in errors: print(error)

if __name__ == '__main__':
    bot.run(TOKEN)