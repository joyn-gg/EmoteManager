# © 2018–2020 io mintz <io@mintz.cc>
#
# Emote Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Emote Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Emote Manager. If not, see <https://www.gnu.org/licenses/>.

import asyncio
import base64
import contextlib
import functools
import io
import logging
import signal
import sys
import typing

logger = logging.getLogger(__name__)

try:
	import wand.image
except (ImportError, OSError):
	logger.warn('Failed to import wand.image. Image manipulation functions will be unavailable.')
else:
	import wand.exceptions

from utils import errors

def resize_until_small(image_data: io.BytesIO) -> None:
	"""If the image_data is bigger than 256KB, resize it until it's not."""
	# It's important that we only attempt to resize the image when we have to,
	# ie when it exceeds the Discord limit of 256KiB.
	# Apparently some <256KiB images become larger when we attempt to resize them,
	# so resizing sometimes does more harm than good.
	max_resolution = 128  # pixels
	image_size = size(image_data)
	if image_size <= 256 * 2**10:
		return

	try:
		with wand.image.Image(blob=image_data) as original_image:
			while True:
				logger.debug('image size too big (%s bytes)', image_size)
				logger.debug('attempting resize to at most%s*%s pixels', max_resolution, max_resolution)

				with original_image.clone() as resized:
					resized.transform(resize=f'{max_resolution}x{max_resolution}')
					image_size = len(resized.make_blob())
					if image_size <= 256 * 2**10 or max_resolution < 32:  # don't resize past 256KiB or 32×32
						image_data.truncate(0)
						image_data.seek(0)
						resized.save(file=image_data)
						image_data.seek(0)
						break

				max_resolution //= 2
	except wand.exceptions.CoderError:
		raise errors.InvalidImageError

def convert_to_gif(image_data: io.BytesIO) -> None:
	try:
		with wand.image.Image(blob=image_data) as orig, orig.convert('gif') as converted:
			# discord tries to stop us from abusing animated gif slots by detecting single frame gifs
			# so make it two frames
			converted.sequence[0].delay = 0  # show the first frame forever
			converted.sequence.append(wand.image.Image(width=1, height=1))

			image_data.truncate(0)
			image_data.seek(0)
			converted.save(file=image_data)
			image_data.seek(0)
	except wand.exceptions.CoderError:
		raise errors.InvalidImageError

def mime_type_for_image(data):
	if data.startswith(b'\x89PNG\r\n\x1a\n'):
		return 'image/png'
	if data.startswith(b'\xFF\xD8') and data.rstrip(b'\0').endswith(b'\xFF\xD9'):
		return 'image/jpeg'
	if data.startswith((b'GIF87a', b'GIF89a')):
		return 'image/gif'
	if data.startswith(b'RIFF') and data[8:12] == b'WEBP':
		return 'image/webp'
	raise errors.InvalidImageError

def image_to_base64_url(data):
	fmt = 'data:{mime};base64,{data}'
	mime = mime_type_for_image(data)
	b64 = base64.b64encode(data).decode('ascii')
	return fmt.format(mime=mime, data=b64)

def main() -> typing.NoReturn:
	"""resize or convert an image from stdin and write the resized or converted version to stdout."""
	import sys

	if sys.argv[1] == 'resize':
		f = resize_until_small
	elif sys.argv[1] == 'convert':
		f = convert_to_gif
	else:
		sys.exit(1)

	data = io.BytesIO(sys.stdin.buffer.read())
	try:
		f(data)
	except errors.InvalidImageError:
		# 2 is used because 1 is already used by python's default error handler
		sys.exit(2)

	stdout_write = sys.stdout.buffer.write  # getattr optimization

	while True:
		buf = data.read(16 * 1024)
		if not buf:
			break

		stdout_write(buf)

	sys.exit(0)

async def process_image_in_subprocess(command_name, image_data: bytes):
	proc = await asyncio.create_subprocess_exec(
		sys.executable, '-m', __name__, command_name,

		stdin=asyncio.subprocess.PIPE,
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.PIPE)

	try:
		image_data, err = await asyncio.wait_for(proc.communicate(image_data), timeout=float('inf'))
	except asyncio.TimeoutError:
		proc.send_signal(signal.SIGINT)
		raise errors.ImageResizeTimeoutError if command_name == 'resize' else errors.ImageConversionTimeoutError
	else:
		if proc.returncode == 2:
			raise errors.InvalidImageError
		if proc.returncode != 0:
			raise RuntimeError(err.decode('utf-8') + f'Return code: {proc.returncode}')

	return image_data

resize_in_subprocess = functools.partial(process_image_in_subprocess, 'resize')
convert_to_gif_in_subprocess = functools.partial(process_image_in_subprocess, 'convert')

def size(fp):
	"""return the size, in bytes, of the data a file-like object represents"""
	with preserve_position(fp):
		fp.seek(0, io.SEEK_END)
		return fp.tell()

class preserve_position(contextlib.AbstractContextManager):
	def __init__(self, fp):
		self.fp = fp
		self.old_pos = fp.tell()

	def __exit__(self, *excinfo):
		self.fp.seek(self.old_pos)

if __name__ == '__main__':
	main()
