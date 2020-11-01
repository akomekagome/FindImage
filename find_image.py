#!/usr/bin/env python
# -*- coding: utf-8 -*-
from urllib import request as req
from urllib import parse
from discord.ext import commands
import discord
import bs4
import re
import os

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

bot = commands.Bot(command_prefix='!', help_command=None)
help_embed = discord.Embed(title="!fi",description="> Search by keyword using Google Image Search")
help_embed.add_field(name="!fi keyword",value="ex) !fi apple\n:apple:1st apple image",inline=False)
help_embed.add_field(name="!fi start keyword",value="ex) !fi 2 dog\n:dog:2nd dog image\nex) !fi 4 cat\n:cat:4th cat image",inline=False)
help_embed.add_field(name="!fi start stop keyword",value="ex) !fi 1 5 rabbit\n:rabbit:1st-5th rabbit image\nex) !fi 4 10 fox\n:fox:4th-10th fox image",inline=False)
help_embed.add_field(name="If you have a request, ", value="[Twitter](https://twitter.com/akomekagome) or [GitHub](https://github.com/akomekagome/FindImage)",inline=False)

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
	await ctx.send(embed=help_embed)

token = os.environ['FINDIMAGE_DISCORD_TOKEN']
bot.run(token)