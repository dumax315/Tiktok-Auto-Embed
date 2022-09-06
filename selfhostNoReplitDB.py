import os
import re
import aiohttp
import asyncio
# import pyppeteer
import discord
import logging
import math
import sys


from discord.ext import tasks
# from replit import db
my_secret = os.environ['token']
# db["listOfDiscordsMess"] = []
# db["discordsUsingBot"] = []
# get rid of extral files
# find . -name "*.mp4" -type f -delete
#find . -name "*.log" -type f -delete
#find . -name "*.temp" -type f -delete

os.system('find . -name "*.temp" -type f -delete')
os.system('find . -name "*.log" -type f -delete')
os.system('find . -name "*.temp" -type f -delete')
# import matplotlib.pyplot as plt
# import numpy as np

# xpoints = np.array([0, 6])
# ypoints = np.array([0, 250])

# plt.plot(xpoints, ypoints)
# plt.show()

print(discord.__version__)
# need to uncomment before may
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
# db["errors"] = 0

# db["alive"] += 1

# if(db["alive"] > 1):
#   db["alive"] = 1
#   quit()

  
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

def get_url(message):
    a = re.search("(?P<url>https?://[^\s]+)", message)
    if a:
        a = a.group("url")
        return a

async def get(text):
  global downloadCount
  localDow = downloadCount
  downloadCount += 1
  try:
    # print(url)
    print("starting process")
    a = get_url(text)
    if ".tiktok." in a:
      async with aiohttp.ClientSession() as session:
        session.headers.update({
          'User-Agent': 'Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)'
        })
        async with session.get(a) as resp:
          a = resp.url


      async with aiohttp.ClientSession() as session:
        session.headers.update({
                                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'})
        async with session.get(f"https://www.tiktok.com/oembed?url={a}") as resp:
          if resp.status == 200:
            rjson = await resp.json()
            data = rjson.get("html")
          else:
            data = None

        if data:
          tiktokid = re.findall('https://www.tiktok.com/@(.*)/video/(.{19})', data)
          if tiktokid:
            tiktokid = tiktokid[0]
            async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
              session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'})
              async with session.get(
                  f"https://www.tiktok.com/node/share/video/@{tiktokid[0]}/{tiktokid[1]}") as resptk:
                if resptk.status == 200:
                  rjson = await resptk.json()
                  cookies = session.cookie_jar.filter_cookies('https://www.tiktok.com')

                  jar = {}
                  for key, cookie in cookies.items():
                    # print('Key: "%s", Value: "%s"' % (cookie.key, cookie.value))
                    jar[cookie.key] = cookie.value
                  # print(jar)
                  # for selenium_cookie in cookies:
                  #   print(selenium_cookie)
                  #   # jar[selenium_cookie['Domain']] = selenium_cookie['tt_csrf_token']
                    
                  video_url = rjson["itemInfo"]["itemStruct"]["video"]["playAddr"]
                  LiCoSh = ["error","error","error"]
                  
                  # print(rjson["itemInfo"]["itemStruct"]["desc"])
                  capt = rjson["itemInfo"]["itemStruct"]["desc"]
                  
                  # print(rjson["itemInfo"]["itemStruct"]["stats"])
                  LiCoSh[0] = rjson["itemInfo"]["itemStruct"]["stats"]["diggCount"]
                  LiCoSh[1] = rjson["itemInfo"]["itemStruct"]["stats"]["commentCount"]
                  LiCoSh[2] = rjson["itemInfo"]["itemStruct"]["stats"]["shareCount"]

                  # print(rjson["itemInfo"]["itemStruct"]["author"]["avatarMedium"])
                  imgsrc = rjson["itemInfo"]["itemStruct"]["author"]["avatarMedium"]

                  # print(rjson["itemInfo"]["itemStruct"]["author"]["uniqueId"])
                  postername = rjson["itemInfo"]["itemStruct"]["author"]["uniqueId"]

                  video_format = rjson["itemInfo"]["itemStruct"]["video"]["format"]
                else:
                  video_url = None
                  video_format = None
                # print(video_format)
                # print(video_url)
                # return (video_url)
                # print(cookies)
                chunk_size = 4096
            
                # custom headers these seem to work almost always
                headers = {
                  "Connection": "keep-alive",
                  "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36",
                  "Referer": "https://www.tiktok.com/"
                }
            
            
                # downloads the file using the cookies and headers gotten from a browser
                async with aiohttp.ClientSession() as session:
                  async with session.get(video_url,headers=headers,cookies=jar) as resp:
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
                
                # db["dataSent"] += os.path.getsize(pathToLastFile)
                #returns the path to the file
                return(pathToLastFile,capt,LiCoSh,imgsrc,postername)
  except Exception as e: 
    # db["errors"] += 1
    print(e)
    # return (video_url, capt,LiCoSh,imgsrc,postername)

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


# hosts a website that can be pinged for uptime
# keep_alive()
# sets the activity to listing to &help one start
client = discord.AutoShardedClient(activity=discord.Activity(type=discord.ActivityType.listening, name='&Help'), intents=intents)
# need to add , intents=intents
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
 # print("Total Users: " + str(totalusers))
 # print("Total Servers: " + str(len(client.guilds)))
 # print("Tiktoks Converted: " + str(db["tiktoksConverted"]))
  #print("Data Sent: " + str(# db["dataSent"]/8388608*8))
 # print("Total users using bot " + str(len(db["uniqueUsersUsed"])))
 # sendUpdate.start()
  # print("discords using bot: " + str(db["discordsUsingBot"]))
  # print("Total discords using bot " + str(len(db["discordsUsingBot"])))
  # db["listOfDiscordsMess"] = []
  # db["discordsUsingBot"] = []
  # # toMake = []
  # # for i in range(0, len(db["discordsUsingBot"])):
  # #   toMake.append(0)
  # # print(toMake)
  # db["listOfDiscordsMess"] = toMake
  # print(db["listOfDiscordsMess"])

  print('------')

@client.event
async def on_message(message):
  #is server dead?
  #is this code breaking everything
  # if(str(message.guild) in db["discordsUsingBot"]):
  #   # print(db["discordsUsingBot"].index(str(message.guild)))
  #   db["listOfDiscordsMess"][db["discordsUsingBot"].index(str(message.guild))] += 1
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
      sendUpdate.start()
      
      guildsSm.sort(key=getNum)
      totalusers = 0
      for i in guildsSm:
        totalusers += i[1]
      # print("Data Sent: " + str(db["dataSent"]/8388608*8))
      # strTosend = 'Logged in as ' + client.user.name + str(client.user.id) + "\nTotal Users: " + str(totalusers) + "\nTotal Servers: " + str(len(client.guilds)) + "\nTiktoks Converted: " + str(db["tiktoksConverted"])+"\nData Sent: " + str(db["dataSent"]/8388608*8) + "\nTotal discords using bot " + str(len(db["discordsUsingBot"]))+"\nTotal users using bot " + str(len(db["uniqueUsersUsed"]))

      # await message.channel.send(strTosend)
      await message.channel.send(guildsSm)
      # await message.channel.send("discords using bot: "+ str(db["discordsUsingBot"]))


  # tries to download if it sees .tiktok. in a message
  elif (re.search("\.tiktok\.", message.content) != None):
    if(str(message.guild) in ["nachwile","nachwile2"] or str(message.author.id) in ["937842804875460658","954047452699324488"]):
      print("spammer")
      # try:
      #   link = await message.channel.create_invite(max_age = 300)
      #   print(link)
      # except:
      #   print("blocked linked")
      # await message.channel.send('stop spamming please, join server and talk to me https://discord.gg/ApdPE6adRc', mention_author=True)
      raise Exception("spammer")
    toEdit = await message.channel.send('working on it')
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
      fileLoc, capt, LiCoShare, avaSrc, postername = await get(message.content)
      # print(message.guild)
      # if(str(message.author.id) not in db["uniqueUsersUsed"]):
      #   db["uniqueUsersUsed"].append(str(message.author.id))
      # if(str(message.guild) not in db["discordsUsingBot"]):
      #   db["discordsUsingBot"].append(str(message.guild))
      #   db["listOfDiscordsMess"].append(0)
      # else:
      #   db["listOfDiscordsMess"][db["discordsUsingBot"].index(str(message.guild))] += 1
      file = discord.File(fileLoc)
      # getting rid of the querry string (not sure if I should try)
      linkToSend = re.findall("([^\?]+)(\?.*)?", message.content)[0][0]
      # print(linkToSend)
      embed=discord.Embed(url=linkToSend, description=linkToSend, color=discord.Color.blue())


      # uses the authors nick name if they have one
      try:
        # if(message.author.nick != None):
        #   embed.set_footer(text="requested by: "+str(message.author.nick), icon_url=message.author.avatar_url)
        # else:
        embed.set_footer(text="requested by: "+str(message.author), icon_url=message.author.avatar.url)
      except:
        print("pm")
        embed.set_footer(text="requested by: "+str(message.author), icon_url=message.author.avatar.url)
      LikesComString = ":heart: " + str(LiCoShare[0]) +" :speech_left: " + str(LiCoShare[1])+ " :arrow_right: " + str(LiCoShare[2])

      try:
        # print("caption= "+ capt)
        if(capt == ""):
          capt = "no caption"
        # added limit after seeing error
          # 400 Bad Request (error code: 50035): Invalid Form Body
          # In embed.fields.0.name: Must be 256 or fewer in length.
          # failed after download
        embed.add_field(name=capt[0:250], value=LikesComString, inline=True)

        # embed.set_footer(text=postername, icon_url=avaSrc)
        embed.set_author(name=postername, icon_url=avaSrc, url="https://www.tiktok.com/@"+str(postername))
      except Exception as e: 
        # db["errors"] += 1
        print(e)
      toReact = await message.channel.send(embed=embed,file=file)
      await toReact.add_reaction("❌")
      # db["tiktoksConverted"] += 1
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
      # db["errors"] += 1
      print(e)
      try:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        os.remove(fileLoc)
        print("failed after download")
      except:
        print(message.content)
        print("faild never downloaded")
      try:
        await toEdit.delete()
      except:
        print("not able to delete working on it")

@client.event
async def on_raw_reaction_add(payload):
  try:
    # Make sure that the message the user is reacting to is the one we care about.
    message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
    # print(payload.channel_id)
    user = payload.member
    # print(payload)
    if message.author.id != client.user.id:
        return
    # print(message.embeds[0].author.url.split("/")[-1])
    # check if the clicker is the orinional sender
    if(str(user).split(" ")[-1] == message.embeds[0].footer.text.split(" ")[-1] and payload.emoji.name =='❌'): 
      await message.delete()
  except Exception as e: 
    print(e)

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
  # print('Logged in as ' + client.user.name+ "\nTotal Users: " + str(totalusers)+ "\nTotal Servers: " + str(len(client.guilds))+"\nTiktoks Converted: " + str(db["tiktoksConverted"])+"\nData Sent: " + str(db["dataSent"]/8388608*8) + "\nTotal users using bot " + str(len(db["uniqueUsersUsed"])))
  # await channel.send('Logged in as ' + client.user.name+ "\nTotal Users: " + str(totalusers)+ "\nTotal Servers: " + str(len(client.guilds))+"\nTiktoks Converted: " + str(db["tiktoksConverted"])+"\nData Sent: " + str(db["dataSent"]/8388608*8) + "mb\nTotal users using bot " + str(len(db["uniqueUsersUsed"]))+"\nerrors= " + str(db["errors"]))

client.run(my_secret)
# try:
#   client.run(my_secret)
# except:
#   os.system("kill 1")

# sendUpdate.start()
  #client.run(my_secret)

