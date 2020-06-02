import asyncio
import os
import socket

from discord.ext import commands

from utils.socket import open_datagram_endpoint

class SystemdNotifier(commands.Cog):
	def __init__(self):
		self.os_sock = socket.socket(family=socket.AF_UNIX, type=socket.SOCK_DGRAM)
		self.connect_task = asyncio.create_task(self.connect())
		self.addr = os.environ['NOTIFY_SOCKET']

	def send(self, msg):
		self.sock.send(msg, self.addr)

	async def connect(self):
		self.sock = await open_datagram_endpoint(sock=self.os_sock)

	def cog_unload(self):
		self.connect_task.cancel()

	@commands.Cog.listener()
	async def on_shard_ready(self, shard_id):
		self.send(b'STATUS=Ready on shard %d' % shard_id)

	@commands.Cog.listener()
	async def on_ready(self):
		self.send(b'READY=1')

def setup(bot):
	bot.add_cog(SystemdNotifier())
