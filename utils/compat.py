import hashlib

try:
	hashlib.md5(usedforsecurity=False)
except TypeError:
	md5 = hashlib.md5
else:
	def md5(*args):
		return hashlib.md5(*args, usedforsecurity=False)
