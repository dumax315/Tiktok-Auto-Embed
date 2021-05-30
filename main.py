from keep_alive import keep_alive

import os
import re
import aiohttp
import asyncio
import pyppeteer
import discord
import logging
import math

workingDir = os.getcwd()

downloadCount = 0

async def run_command(video_full_path, output_file_name, target_size):
	pro1 = await asyncio.create_subprocess_exec(*["ffprobe", "-v", "error", "-show_entries","format=duration", "-of","default=noprint_wrappers=1:nokey=1", video_full_path], stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
	print("Started: %s, pid=%s" % (pro1, pro1.pid), flush=True)
	stdout, stderr = await pro1.communicate()
	print(float(stdout))
	bitrate = str(math.floor(8*8100/float(stdout))-32)+"k"
	print(bitrate)

	# consider making very fast not ultrafast
	cmd =f"ffmpeg -y -i {video_full_path} -c:v libx264 -passlogfile {video_full_path}passlog -preset ultrafast -b:v {bitrate} -pass 1 -an -f mp4 {output_file_name}"
	print(cmd)

	cmd2 =f"ffmpeg -y -i {video_full_path} -c:v libx264 -passlogfile {video_full_path}passlog -preset ultrafast -b:v {bitrate} -pass 2 -acodec copy {output_file_name}"
	print(cmd2)

	pro1 = await asyncio.create_subprocess_exec(*cmd.split(), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
	)
	print("Started: %s, pid=%s" % (pro1, pro1.pid), flush=True)
	stdout, stderr = await pro1.communicate()
	
	pro1 = await asyncio.create_subprocess_exec(*cmd2.split(), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
	)
	print("Started: %s, pid=%s" % (pro1, pro1.pid), flush=True)
	stdout, stderr = await pro1.communicate()

	os.remove(video_full_path +"passlog-0.log")
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
		try:
			cap = await page.querySelector('.tt-video-meta-caption')
			capt = await page.evaluate('(element) => element.innerText', cap)
			print(capt)
		except Exception as e: 
			print(e)
			capt = "No Caption"
		try:
			LiCoShData = await page.querySelectorAll('.jsx-1045706868.bar-item-wrapper')
			LiCoSh = []
			for i in LiCoShData:
				LiCoSh.append(await page.evaluate('(element) => element.innerText', i))
			print(LiCoSh)
		except Exception as e: 
			print(e)
			LiCoSh = ["error","error","error"]
		
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
		if(os.path.getsize(pathToLastFile) >= 8388000):
			print("compressing ...")
			await run_command(pathToLastFile, pathToLastFile + "comp.mp4", 8388000)
			pathToLastFile = pathToLastFile + "comp.mp4"
		
		#returns the path to the file
		return(pathToLastFile,capt,LiCoSh)
	except Exception as e: 
		print(e)
		# closes the browser if it is open 
		try:
			await browser.close()
		except:
			pass

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
my_secret = os.environ['token']

# hosts a website that can be pinged for uptime
keep_alive()
# sets the activity to listing to &help one start
client = discord.Client(activity=discord.Activity(type=discord.ActivityType.listening, name='&Help'))

def getGuildName(n):
  return [n.name, n.member_count]

@client.event
async def on_ready():
	print('Logged in as')
	print(client.user.name)
	print(client.user.id)
	print(list(map(getGuildName, client.guilds)))
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
		embed.add_field(name="Can I add this bot to my server?", value="Yep, just go to this link.\nhttps://tinyurl.com/TiktokAutoEmbed", inline=False)
		embed.add_field(name="Why do long videos look bad?", value="Discord has a file limit of 8 mb, this isn't a problem for most tiktoks but for some the bot needs to compress them before sending. Because of this it can also take the bot longer to send long vides espeically if a lot of people are using the bot at once.", inline=False)
		embed.add_field(name="Say Hi to the Creator", value="Message me <@!322193320199716865> and join my discord server dedicated to my projects [https://discord.gg/fKcTKxW6Jv](https://discord.gg/fKcTKxW6Jv).", inline=False)
		await message.channel.send(embed=embed)
	
	# tries to download if it sees .tiktok. in a message
	elif (re.search("\.tiktok\.", message.content) != None):
		toEdit = await message.channel.send('working on it', mention_author=True)
		try:
			fileLoc, capt, LiCoShare = await downloadTiktok(message.content)
			print(message.guild)
			file = discord.File(fileLoc)
			embed=discord.Embed(url=message.content, description=message.content, color=discord.Color.blue())
			# uses the authors nick name if they have one
			try:
				if(message.author.nick != None):
					embed.set_author(name=message.author.nick, url="https://discordapp.com/users/"+str(message.author.id), icon_url=message.author.avatar_url)
				else:
					embed.set_author(name=message.author, url="https://discordapp.com/users/"+str(message.author.id), icon_url=message.author.avatar_url)
			except:
				print("pm")
				embed.set_author(name=message.author, url="https://discordapp.com/users/"+str(message.author.id), icon_url=message.author.avatar_url)
			
			LikesComString = ":heart: " + LiCoShare[0] +" :speech_left: " +LiCoShare[1]+ " :arrow_right: " + LiCoShare[2]
			embed.add_field(name=capt, value=LikesComString, inline=True)
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
