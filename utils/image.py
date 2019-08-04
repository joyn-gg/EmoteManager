#!/usr/bin/env python3
# encoding: utf-8

import asyncio
import base64
import contextlib
import io
import logging
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
	while image_size > 256 * 2**10 and max_resolution >= 32:  # don't resize past 32x32 or 256KiB
		logger.debug('image size too big (%s bytes)', image_size)
		logger.debug('attempting resize to at most%s*%s pixels', max_resolution, max_resolution)

		try:
			thumbnail(image_data, (max_resolution, max_resolution))
		except wand.exceptions.CoderError:
			raise errors.InvalidImageError

		image_size = size(image_data)
		max_resolution //= 2

def thumbnail(image_data: io.BytesIO, max_size=(128, 128)) -> None:
	"""Resize an image in place to no more than max_size pixels, preserving aspect ratio."""
	with wand.image.Image(blob=image_data) as image:
		new_resolution = scale_resolution((image.width, image.height), max_size)
		image.resize(*new_resolution)
		image_data.truncate(0)
		image_data.seek(0)
		image.save(file=image_data)

	# allow resizing the original image more than once for memory profiling
	image_data.seek(0)

def scale_resolution(old_res, new_res):
	"""Resize a resolution, preserving aspect ratio. Returned w,h will be <= new_res"""
	# https://stackoverflow.com/a/6565988

	old_width, old_height = old_res
	new_width, new_height = new_res

	old_ratio = old_width / old_height
	new_ratio = new_width / new_height
	if new_ratio > old_ratio:
		return (old_width * new_height//old_height, new_height)
	return new_width, old_height * new_width//old_width

def mime_type_for_image(data):
	if data.startswith(b'\x89PNG\r\n\x1a\n'):
		return 'image/png'
	if data.startswith(b'\xFF\xD8') and data.rstrip(b'\0').endswith(b'\xFF\xD9'):
		return 'image/jpeg'
	if data.startswith((b'GIF87a', b'GIF89a')):
		return 'image/gif'
	raise errors.InvalidImageError

def image_to_base64_url(data):
	fmt = 'data:{mime};base64,{data}'
	mime = mime_type_for_image(data)
	b64 = base64.b64encode(data).decode('ascii')
	return fmt.format(mime=mime, data=b64)

def main() -> typing.NoReturn:
	"""resize an image from stdin and write the resized version to stdout."""
	import sys

	data = io.BytesIO(sys.stdin.buffer.read())
	try:
		resize_until_small(data)
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

async def resize_in_subprocess(image_data: bytes):
	proc = await asyncio.create_subprocess_exec(
		sys.executable, '-m', __name__,

		stdin=asyncio.subprocess.PIPE,
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.PIPE)

	try:
		image_data, err = await asyncio.wait_for(proc.communicate(image_data), timeout=30)
	except asyncio.TimeoutError:
		proc.kill()
		raise errors.ImageResizeTimeoutError
	else:
		if proc.returncode == 2:
			raise errors.InvalidImageError
		if proc.returncode != 0:
			raise RuntimeError(err.decode('utf-8') + f'Return code: {proc.returncode}')

	return image_data

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
