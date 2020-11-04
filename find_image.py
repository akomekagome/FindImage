#!/usr/bin/env python
# -*- coding: utf-8 -*-
from urllib import request as req
from urllib import parse
from discord.ext import commands
import json
import aiofiles
import asyncio
import discord
import bs4
import re
import os
import psycopg2
import psycopg2.extras

protocols = [
	'https://',
	'http://'
]

image_extensions = [
	'.jpg',
	'.JPG',
	'.png',
	'.gif',
	'.jpeg'
]

unique_urls = [
	'lohas.nicoseiga.jp/thumb',
	'cdn-image.alphapolis.co.jp',
	'cdn.yamap.co.jp/public/image2.yamap.co.jp',
	'img.cdn.nimg.jp',
	'chie-pctr.c.yimg.jp',
	'nicovideo.cdn.nimg.jp',
	'www.instagram.com',
]

exception_urls = [
	'.cdninstagram.com'
]

prefix_json_path = 'prefix.json'
defalut_prefix = '!'
table_name = 'guilds'

def is_url(str):
	return any([x in str for x in protocols])

def is_image_extension(str):
	return any([x in str for x in image_extensions])

def is_unique_url(str):
	return any([x in str for x in unique_urls])

def is_exception_url(str):
	return any([x in str for x in exception_urls])

def is_image_url(str):
	return is_url(str) & (not is_exception_url(str)) & (is_image_extension(str) | is_unique_url(str))

def check_url(url):
	try:
		f = req.urlopen(url)
		f.close()
		return True
	except req.HTTPError:
		return False

def find_image(keyword, start = 0, stop = 1):
	urlKeyword = parse.quote(keyword)
	url = 'https://www.google.com/search?hl=jp&q=' + urlKeyword + '&btnG=Google+Search&tbs=0&safe=off&tbm=isch'
	headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0",}
	request = req.Request(url=url, headers=headers)
	page = req.urlopen(request)
	html = page.read()
	page.close()
	soup = bs4.BeautifulSoup(html, "html.parser", from_encoding="utf8")
	soup = soup.find_all('script')
	text = ''.join([str(x) for x in soup])
	list = text.split('\"')
	image_url_list = [x for x in list if is_image_url(x)][start:stop]
	image_url_list = [re.sub(r'[\'\[\]]', '', x) for x in image_url_list]
	image_url_list = [x.encode().decode('unicode-escape') for x in image_url_list]

	return image_url_list

async def open_json(path):
	try:
		async with aiofiles.open(path) as f:
			contents = await f.read()
			return json.loads(contents)
	except:
		return {}

async def get_prefix(bot, message):
	return get_prefix_list(str(message.guild.id))

def get_prefix_dict(key):
	return data.get(key, defalut_prefix)

def get_prefix_list(key):
	for x in data:
		if x[0] == key:
			return x[1]
	return defalut_prefix

def get_help_embed(prefix):
	help_embed = discord.Embed()
	help_embed.add_field(name = "fi", value = "> Search for images based on keywords", inline = False)
	help_embed.add_field(name = f"{prefix}fi <keyword>", value = f"ex) {prefix}fi apple\n:apple:1st apple image", inline = False)
	help_embed.add_field(name = f"{prefix}fi <start> <keyword>", value = f"ex) {prefix}fi 2 dog\n:dog:2nd dog image\nex) {prefix}fi 4 cat\n:cat:4th cat image", inline = False)
	help_embed.add_field(name = f"{prefix}fi <start> <stop> <keyword>", value = f"ex) {prefix}fi 1 5 rabbit\n:rabbit:1st-5th rabbit image\nex) {prefix}fi 4 10 fox\n:fox:4th-10th fox image", inline = False)
	help_embed.add_field(name = "set_prefix", value = "> Change the prefix", inline = False)
	help_embed.add_field(name = f"{prefix}set_prefix <prefix>", value = f"ex) {prefix}set_prefix $\n:dollar:The prefix has been changed from {prefix} to $", inline = False)
	help_embed.add_field(name = "If you have a request, ", value = "[Twitter](https://twitter.com/akomekagome) or [GitHub](https://github.com/akomekagome/FindImage)", inline = False)

	return help_embed

async def set_prefix_json(key, prefix):
	data[key] = prefix
	async with aiofiles.open("prefix.json", "w") as f:
		await f.write(json.dumps(data))

def set_prefix_sql(key, prefix):
	for x in data:
		if x[0] == key:
			x[1] = prefix
	with conn.cursor() as cur:
		cur.execute(f'INSERT INTO {table_name} VALUES (%s,%s) ON CONFLICT ON CONSTRAINT guilds_pkey DO UPDATE SET prefix=%s', (key, prefix, prefix))
	conn.commit()

# loop = asyncio.get_event_loop()
# data = loop.run_until_complete(open_json(prefix_json_path))
db_url = os.environ['DATABASE_URL']
conn = psycopg2.connect(db_url)
with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
	cur.execute(f'SELECT * FROM {table_name}')
	data = cur.fetchall()
bot = commands.Bot(command_prefix=get_prefix, help_command=None)

@bot.event
async def on_ready():
    print("導入サーバー数: " + str(len(bot.guilds)))

@bot.command()
async def fi(ctx, *args):
	urls = []
	if (len(args) > 2 and args[0].isdecimal() and args[1].isdecimal()):
		urls = find_image(' '.join(args[2:]), int(args[0]) - 1, int(args[1]))
	elif (len(args) > 1 and args[0].isdecimal()):
		urls = find_image(' '.join(args[1:]), int(args[0]) - 1, int(args[0]))
	else:
		urls = find_image(' '.join(args))
	for url in urls:
		await ctx.send(url)

@bot.command()
async def help(ctx):
	prefix = get_prefix_list(str(ctx.guild.id))
	await ctx.send(embed=get_help_embed(prefix))

@bot.command()
async def set_prefix(ctx, prefix):
	key = str(ctx.guild.id)
	before = get_prefix_list(key)
	set_prefix_sql(key, prefix)

	await ctx.send(f"The prefix has been changed from {before} to {prefix}")

token = os.environ['FINDIMAGE_DISCORD_TOKEN']
bot.run(token)