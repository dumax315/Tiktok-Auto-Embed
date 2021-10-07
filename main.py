import os
import re
import aiohttp
import asyncio
import pyppeteer
import discord
import logging
import math

from discord.ext import tasks
from replit import db


# from keep_alive import keep_alive

# workingDir = os.getcwd()

downloadCount = 0

async def run_command(video_full_path, output_file_name, target_size):
	pro1 = await asyncio.create_subprocess_exec(*["ffprobe", "-v", "error", "-show_entries","format=duration", "-of","default=noprint_wrappers=1:nokey=1", video_full_path], stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
	print("Started: %s, pid=%s" % (pro1, pro1.pid), flush=True)
	stdout, stderr = await pro1.communicate()
	print(float(stdout))
	bitrate = str(math.floor(8*8100/float(stdout))-32)+"k"
	print(bitrate)

	# consider making very fast not ultrafast
	cmd = f"ffmpeg -y -i {video_full_path} -c:v libx264 -passlogfile {video_full_path}passlog -preset ultrafast -b:v {bitrate} -pass 1 -an -f mp4 {output_file_name}"
	print(cmd)

	cmd2 =f"ffmpeg -y -i {video_full_path} -c:v libx264 -passlogfile {video_full_path}passlog -preset ultrafast -b:v {bitrate} -pass 2 -c:a aac -b:a 32k {output_file_name}"
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
		# print(url)
		print("starting process")
		browser = await pyppeteer.launch({
			'headless': True,
			"args": ['--no-sandbox', '--disable-setuid-sandbox'],
		});
		
		page = await browser.newPage()
		await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36')
		# await page.setDefaultNavigationTimeout(1000000)
		await page.goto(url, {"waitUntil": 'load', "timeout": 1000000})
		try:
			element = await page.querySelector('video')
			videoUrl = await page.evaluate('(element) => element.src', element)
		except:
			await page.goto(url, {"waitUntil": 'load', "timeout": 1000000})
			# await page.waitForSelector('video')
			# await page.waitFor(2000);
			
			# await page.screenshot({'path': 'example.png'})
			element = await page.querySelector('video')
			videoUrl = await page.evaluate('(element) => element.src', element)
		#gets the video captions
		try:
			cap = await page.querySelector('.tt-video-meta-caption')
			capt = await page.evaluate('(element) => element.innerText', cap)
			# print(capt)
		except Exception as e: 
			print(e)
			capt = "No Caption"
		#get the likes comments and shares
		try:
			LiCoShData = await page.querySelectorAll('.bar-item-text.jsx-18968439')
			# print(LiCoShData)
			LiCoSh = []
			for i in LiCoShData:
				LiCoSh.append(await page.evaluate('(element) => element.innerText', i))
			# print(LiCoSh)
		except Exception as e: 
			print(e)
			LiCoSh = ["error","error","error"]
		if(LiCoSh == []):
			LiCoSh = ["error","error","error"]
		# print(LiCoSh)
		#get poster image
		try:
			imgobj = await page.querySelector('span.tiktok-avatar.tiktok-avatar-circle.avatar>img')
			imgsrc = await page.evaluate('(element) => element.src', imgobj)
		except Exception as e: 
			print(e)
			imgsrc = ""

		#get poster name
		try:
			posternameObj = await page.querySelector('h3.author-uniqueId')
			postername = await page.evaluate('(element) => element.innerText', posternameObj)
		except Exception as e: 
			print(e)
			postername = ""
		# print(postername)

		#get costum file names (might brake?)
		localDow = "".join(x for x in capt[0:15] if x.isalnum()) + str(localDow)

		# print(videoUrl)
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
		
		db["dataSent"] += os.path.getsize(pathToLastFile)
		#returns the path to the file
		return(pathToLastFile,capt,LiCoSh,imgsrc,postername)
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
# keep_alive()
# sets the activity to listing to &help one start
client = discord.Client(activity=discord.Activity(type=discord.ActivityType.listening, name='&Help'))

def getGuildName(n):
  return [n.name, n.member_count]

def getNum(obj):
	return obj[1]

@client.event
async def on_ready():
	print('Logged in as')
	print(client.user.name)
	print(client.user.id)
	guildsSm =list(map(getGuildName, client.guilds))
	
	guildsSm.sort(key=getNum)
	print(guildsSm)
	totalusers = 0
	for i in guildsSm:
		totalusers += i[1]
	print("Total Users: " + str(totalusers))
	print("Total Servers: " + str(len(client.guilds)))
	print("Tiktoks Converted: " + str(db["tiktoksConverted"]))
	print("Data Sent: " + str(db["dataSent"]/8388608*8))
	print("Total users using bot " + str(len(db["uniqueUsersUsed"])))
	sendUpdate.start()
	# print("discords using bot: " + str(db["discordsUsingBot"]))
	# print("Total discords using bot " + str(len(db["discordsUsingBot"])))
	# # db["listOfDiscordsMess"] = []
	# # toMake = []
	# # for i in range(0, len(db["discordsUsingBot"])):
	# # 	toMake.append(0)
	# # print(toMake)
	# db["listOfDiscordsMess"] = toMake
	# print(db["listOfDiscordsMess"])

	print('------')

@client.event
async def on_message(message):
	#is server dead?
	#is this code breaking everything
	
	# if(str(message.guild) in db["discordsUsingBot"]):
	# 	# print(db["discordsUsingBot"].index(str(message.guild)))
	# 	db["listOfDiscordsMess"][db["discordsUsingBot"].index(str(message.guild))] += 1
		# print(db["listOfDiscordsMess"][db["discordsUsingBot"].index(str(message.guild))])
		
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
	
	elif message.content.lower().startswith('&getchannelid'):
		sendUpdate.start()
		await message.channel.send(message.channel.id)

	elif message.content.lower().startswith('&getdata'):
		if(str(message.author.id) == "322193320199716865"):
			print('Logged in as')
			print(client.user.name)
			print(client.user.id)
			guildsSm =list(map(getGuildName, client.guilds))
			
			guildsSm.sort(key=getNum)
			totalusers = 0
			for i in guildsSm:
				totalusers += i[1]
			print("Data Sent: " + str(db["dataSent"]/8388608*8))
			strTosend = 'Logged in as ' + client.user.name + str(client.user.id) + "\nTotal Users: " + str(totalusers) + "\nTotal Servers: " + str(len(client.guilds)) + "\nTiktoks Converted: " + str(db["tiktoksConverted"])+"\nData Sent: " + str(db["dataSent"]/8388608*8) + "\nTotal discords using bot " + str(len(db["discordsUsingBot"]))+"\nTotal users using bot " + str(len(db["uniqueUsersUsed"]))

			await message.channel.send(strTosend)
			await message.channel.send(guildsSm)
			await message.channel.send("discords using bot: "+ str(db["discordsUsingBot"]))


	# tries to download if it sees .tiktok. in a message
	elif (re.search("\.tiktok\.", message.content) != None):
		toEdit = await message.channel.send('working on it', mention_author=True)
		if(re.search(" ", message.content) != None):
			print("bad string")
			splitonSpace = message.content.split()
			print(splitonSpace)
			for i in range(len(splitonSpace)):
				if(re.search("\.tiktok\.", splitonSpace[i]) != None):
					message.content = splitonSpace[i]

			delOrinoal = False
		else:
			delOrinoal = True
		try:
			print(message.guild)
			fileLoc, capt, LiCoShare, avaSrc, postername = await downloadTiktok(message.content)
			print(message.guild)
			if(str(message.author.id) not in db["uniqueUsersUsed"]):
				db["uniqueUsersUsed"].append(str(message.author.id))
			if(str(message.guild) not in db["discordsUsingBot"]):
				db["discordsUsingBot"].append(str(message.guild))
				db["listOfDiscordsMess"].append(0)
			else:
				db["listOfDiscordsMess"][db["discordsUsingBot"].index(str(message.guild))] += 1
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
			embed.set_footer(text=postername, icon_url=avaSrc)
			toReact = await message.channel.send(embed=embed,file=file)
			await toReact.add_reaction("❌")
			db["tiktoksConverted"] += 1
			print(fileLoc)
			os.remove(fileLoc)
			await toEdit.delete()
			#tries to delete the user sent message 
			if(delOrinoal):
				try:
					await message.delete()
				except:
					print("no perms")
		except Exception as e: 
			print(e)
			try:
				os.remove(fileLoc)
				print("failed after download")
			except:
				print("faild never downloaded")
			try:
				await toEdit.delete()
			except:
				print("not able to delete working on it")

@client.event
async def on_raw_reaction_add(payload):
	
	# Make sure that the message the user is reacting to is the one we care about.
	message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
	# print(payload.channel_id)
	user = payload.member
	# print(payload)
	if message.author.id != client.user.id:
			return
	# print(message.embeds[0].author.url.split("/")[-1])
	# check if the clicker is the orinional sender
	if(user.id == int(message.embeds[0].author.url.split("/")[-1]) and payload.emoji.name =='❌'): 
		await message.delete()

#minutes
@tasks.loop(minutes=60)
async def sendUpdate():
	channel = client.get_channel(871930436891332628)
	
	guildsSm =list(map(getGuildName, client.guilds))
	
	guildsSm.sort(key=getNum)
	# print(guildsSm)
	totalusers = 0
	for i in guildsSm:
		totalusers += i[1]
	print('Logged in as ' + client.user.name+ "\nTotal Users: " + str(totalusers)+ "\nTotal Servers: " + str(len(client.guilds))+"\nTiktoks Converted: " + str(db["tiktoksConverted"])+"\nData Sent: " + str(db["dataSent"]/8388608*8) + "\nTotal users using bot " + str(len(db["uniqueUsersUsed"])))
	await channel.send('Logged in as ' + client.user.name+ "\nTotal Users: " + str(totalusers)+ "\nTotal Servers: " + str(len(client.guilds))+"\nTiktoks Converted: " + str(db["tiktoksConverted"])+"\nData Sent: " + str(db["dataSent"]/8388608*8) + "mb\nTotal users using bot " + str(len(db["uniqueUsersUsed"])))

client.run(my_secret)
