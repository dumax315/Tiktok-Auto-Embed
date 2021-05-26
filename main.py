
import os
import re
import aiohttp
import asyncio
import pyppeteer
import discord

workingDir = os.getcwd()

downloadCount = 0

async def run_command(video_full_path, output_file_name, target_size):
	cmd = f'ffmpeg -i {video_full_path} -preset veryfast -vcodec libx264 -crf 28 -c:a: aac {output_file_name}'

	# Create subprocess
	process = await asyncio.create_subprocess_exec(
		*cmd.split(), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
	)

	# Status
	print("Started: %s, pid=%s" % (process, process.pid), flush=True)

	# Wait for the subprocess to finish
	stdout, stderr = await process.communicate()
	
	# Progress
	if process.returncode == 0:
		print("Done compression")
	else:
		print("Failed compression")
		print(stderr)

	print(os.path.getsize(output_file_name))
	os.remove(video_full_path)



async def downloadTiktok(url):
	# gets the downloadCount (for the file name) and increments it one
	global downloadCount
	localDow = downloadCount
	downloadCount += 1
	try:
		print(url)
		browser = await pyppeteer.launch({
			'headless': True,
			"args": ['--no-sandbox', '--disable-setuid-sandbox'],
		});
		page = await browser.newPage()
		await page.goto(url)
		
		try:
			element = await page.querySelector('video')
			videoUrl = await page.evaluate('(element) => element.src', element)
		except:
			await page.goto(url)
			# await page.waitForSelector('video')
			# await page.screenshot({'path': 'example.png'})
			element = await page.querySelector('video')
			videoUrl = await page.evaluate('(element) => element.src', element)
		
		print(videoUrl)
		cookies = await page.cookies()
		await browser.close()
	
		chunk_size = 4096

		# custom headers these seem to work almost always
		headers = {
			"Connection": "keep-alive",
			"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36",
			"Referer": "https://www.tiktok.com/"
		}

		jar = {}
		for selenium_cookie in cookies:
			jar[selenium_cookie['name']] = selenium_cookie['value']

		# downloads the file using the cookies and headers gotten from a browser
		async with aiohttp.ClientSession() as session:
			async with session.get(videoUrl,headers=headers,cookies=jar) as resp:
				if resp.status == 200:
					with open(str(localDow) + ".mp4", 'wb') as fd:
						async for data in resp.content.iter_chunked(chunk_size):
							fd.write(data)

		pathToLastFile = str(localDow) + ".mp4"
		print(os.path.getsize(pathToLastFile));

		#sends the file off to compression if it is over 8 mb
		if(os.path.getsize(pathToLastFile) >= 8000000):
			print("compressing ...")
			await run_command(pathToLastFile, pathToLastFile + "comp.mp4", 8000000)
			pathToLastFile = pathToLastFile + "comp.mp4"
		
		#returns the path to the file
		return(pathToLastFile)
	except Exception as e: 
		print(e)
		# closes the browser if it is open 
		try:
			await browser.close()
		except:
			pass

import logging
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
my_secret = os.environ['token']

# sets the activity to listing to &help one start
client = discord.Client(activity=discord.Activity(type=discord.ActivityType.listening, name='&Help'))

@client.event
async def on_ready():
		print('Logged in as')
		print(client.user.name)
		print(client.user.id)
		print(len(client.guilds))
		print('------')

@client.event
async def on_message(message):
		# we do not want the bot to reply to itself
		if message.author.id == client.user.id:
			return
		
		# sends a description of the bot on &help
		elif message.content.lower().startswith('&help'):
			embed=discord.Embed(title="About TikTok Auto Embed", description="When you post a tiktok link Tiktok Auto Embed will delete your original message and send a message containing the original link, the senders @, and a dowloaded copy of the video.", color=0xFF5733)
			embed.add_field(name="Why do long videos look bad?", value="Discord has a file limit of 8 mb, this isn't a problem for most tiktoks but for some the bot needs to compress them before sending. Because of this it can also take the bot longer to send long vides espeically if a lot of people are using the bot at once.", inline=False)
			embed.add_field(name="Say Hi to the Creator", value="Message me <@!322193320199716865> and join my discord server dedicated to my projects [https://discord.gg/fKcTKxW6Jv](https://discord.gg/fKcTKxW6Jv).", inline=False)
			await message.channel.send(embed=embed)
		
		# tries to download if it sees .tiktok. in a message
		elif (re.search("\.tiktok\.", message.content) != None):
			toEdit = await message.channel.send('working on it', mention_author=True)
			try:
				fileLoc = await downloadTiktok(message.content)
				print(message.guild)
				file = discord.File(fileLoc)
				embed=discord.Embed(url=message.content, description=message.content, color=discord.Color.blue())
				# uses the authors nick name if they have one
				if(message.author.nick != None):
					embed.set_author(name=message.author.nick, url="https://discordapp.com/users/"+str(message.author.id), icon_url=message.author.avatar_url)
				else:
					embed.set_author(name=message.author, url="https://discordapp.com/users/"+str(message.author.id), icon_url=message.author.avatar_url)	
				await message.channel.send(embed=embed,file=file)
				print(fileLoc)
				os.remove(fileLoc)
				await toEdit.delete()
				#tries to delete the user sent message 
				try:
					await message.delete()
				except:
					print("no perms")
			except Exception as e: 
				print(e)
				await toEdit.delete()

client.run(my_secret)
