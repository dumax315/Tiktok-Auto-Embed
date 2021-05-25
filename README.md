# download-tiktok
Discord Bot that downloads and embeds tiktok links sent by users

The TikTok Auto Embed bot will automatically embed the tiktoks links you send. This is helpful because your friends can now watch the tiktoks you send without leaving the app. When you post a TikTok link, the TikTok Auto Embed bot will delete your original message and send a new message containing: the original link, the sender's discord tag, and an embedded copy of the video.

The bot is completely async so it can handle many requests at once.

There are 3 parts to the video pipline:
First pyppeteer goes to the tiktok link and finds the file link. It also saves the cookies.
Next I send a aiohttp request with custom headers and cookies to download the video.
Finaly if the tiktok is over 8 mb the code uses asyncio.create_subprocess_exec to run ffmpeg on the file and compress it.
