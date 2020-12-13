#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  smoke_zephyr/utilities.py
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following disclaimer
#    in the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of the project nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import collections
import functools
import inspect
import ipaddress
import itertools
import logging
import os
import random
import re
import shutil
import string
import subprocess
import sys
import time
import unittest
import urllib.parse
import urllib.request
import weakref

EMAIL_REGEX = re.compile(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,6}$', flags=re.IGNORECASE)

class AttributeDict(dict):
	"""
	This class allows dictionary keys to be accessed as attributes. For
	example: ``ad = AttributeDict(test=1); ad['test'] == ad.test``
	"""
	__getattr__ = dict.__getitem__
	__setattr__ = dict.__setitem__

class BruteforceGenerator(object):
	"""
	This class allows itarating sequences for bruteforcing.
	"""
	# requirments = itertools
	def __init__(self, startlen, endlen=None, charset=None):
		"""
		:param int startlen: The minimum sequence size to generate.
		:param int endlen: The maximum sequence size to generate.
		:param charset: The characters to include in the resulting sequences.
		"""
		self.startlen = startlen
		if endlen is None:
			self.endlen = startlen
		else:
			self.endlen = endlen
		if charset is None:
			charset = list(map(chr, range(0, 256)))
		elif isinstance(charset, str):
			charset = list(charset)
		elif isinstance(charset, bytes):
			charset = list(map(chr, charset))
		charset.sort()
		self.charset = tuple(charset)
		self.length = self.startlen
		self._product = itertools.product(self.charset, repeat=self.length)
		self._next = self.__next__

	def __iter__(self):
		return self

	def __next__(self):
		return self.next()

	def next(self):
		try:
			value = next(self._product)
		except StopIteration:
			if self.length == self.endlen:
				raise StopIteration
			self.length += 1
			self._product = itertools.product(self.charset, repeat=self.length)
			value = next(self._product)
		return ''.join(value)

_ArgSpec = collections.namedtuple('_ArgSpec', ('args', 'varargs', 'keywords', 'defaults'))
class Cache(object):
	"""
	This class provides a simple to use cache object which can be applied
	as a decorator.
	"""
	def __init__(self, timeout):
		"""
		:param timeout: The amount of time in seconds that a cached
			result will be considered valid for.
		:type timeout: int, str
		"""
		if isinstance(timeout, str):
			timeout = parse_timespan(timeout)
		self.cache_timeout = timeout
		self._target_function = None
		self._target_function_arg_spec = None
		self.__cache = {}
		self.__obj = None

	def __get__(self, instance, _):
		self.__obj = instance
		return self

	def __call__(self, *args, **kwargs):
		if not getattr(self, '_target_function', False):
			target_function = args[0]
			if not inspect.isfunction(target_function) and not inspect.ismethod(target_function):
				raise RuntimeError('the cached object must be a function or method')
			arg_spec = inspect.getfullargspec(target_function)  # pylint: disable=W1505
			arg_spec = _ArgSpec(args=arg_spec.args, varargs=arg_spec.varargs, keywords=arg_spec.kwonlyargs, defaults=arg_spec.defaults)
			if arg_spec.varargs or arg_spec.keywords:
				raise RuntimeError('the cached function can not use dynamic args or kwargs')
			self._target_function = target_function
			self._target_function_arg_spec = arg_spec
			return functools.wraps(target_function)(self)

		self.cache_clean()
		if self.__obj is not None:
			args = (self.__obj,) + args
			self.__obj = None
			is_method = True
		else:
			is_method = False
		args = self._flatten_args(args, kwargs)
		if is_method:
			inst = args.popleft()
			args = tuple(args)
			ref = weakref.ref(inst, functools.partial(self._ref_callback, args))
			cache_args = (ref,) + args
			args = (inst,) + args
		else:
			cache_args = tuple(args)
			args = tuple(args)
		result, expiration = self.__cache.get(cache_args, (None, 0))
		if expiration > time.time():
			return result
		result = self._target_function(*args)
		self.__cache[cache_args] = (result, time.time() + self.cache_timeout)
		return result

	def __repr__(self):
		return "<cached function {0} at 0x{1:x}>".format(self._target_function.__name__, id(self._target_function))

	def _flatten_args(self, args, kwargs):
		flattened_args = collections.deque(args)
		arg_spec = self._target_function_arg_spec

		arg_spec_defaults = (arg_spec.defaults or [])
		default_args = tuple(arg_spec.args[:-len(arg_spec_defaults)])
		default_kwargs = dict(zip(arg_spec.args[-len(arg_spec_defaults):], arg_spec_defaults))

		for arg_id in range(len(args), len(arg_spec.args)):
			arg_name = arg_spec.args[arg_id]
			if arg_name in default_args:
				if not arg_name in kwargs:
					raise TypeError("{0}() missing required argument '{1}'".format(self._target_function.__name__, arg_name))
				flattened_args.append(kwargs.pop(arg_name))
			else:
				flattened_args.append(kwargs.pop(arg_name, default_kwargs[arg_name]))

		if kwargs:
			unexpected_kwargs = tuple("'{0}'".format(a) for a in kwargs.keys())
			raise TypeError("{0}() got an unexpected keyword argument{1} {2}".format(self._target_function.__name__, ('' if len(unexpected_kwargs) == 1 else 's'), ', '.join(unexpected_kwargs)))
		return flattened_args

	def _ref_callback(self, args, ref):
		args = (ref,) + args
		self.__cache.pop(args, None)

	def cache_clean(self):
		"""
		Remove expired items from the cache.
		"""
		now = time.time()
		keys_for_removal = collections.deque()
		for key, (_, expiration) in self.__cache.items():
			if expiration < now:
				keys_for_removal.append(key)
		for key in keys_for_removal:
			del self.__cache[key]

	def cache_clear(self):
		"""
		Remove all items from the cache.
		"""
		self.__cache = {}

class FileWalker(object):
	"""
	This class is used to easily iterate over files and subdirectories of a
	specified parent directory.
	"""
	def __init__(self, filespath, absolute_path=False, skip_files=False, skip_dirs=False, filter_func=None, follow_links=False, max_depth=None):
		"""
		.. versionchanged:: 1.4.0
			Added the *follow_links* and *max_depth* parameters.

		:param str filespath: A path to either a file or a directory. If
			a file is passed then that will be the only file returned
			during the iteration. If a directory is passed, all files and
			subdirectories will be recursively returned during the iteration.
		:param bool absolute_path: Whether or not the absolute path or a
			relative path should be returned.
		:param bool skip_files: Whether or not to skip files.
		:param bool skip_dirs: Whether or not to skip directories.
		:param function filter_func: If defined, the filter_func function will
			be called for each path (with the path as the one and only argument)
			and if the function returns false the path will be skipped.
		:param bool follow_links: Whether or not to follow directories pointed
			to by symlinks.
		:param max_depth: A maximum depth to recurse into.
		"""
		if not (os.path.isfile(filespath) or os.path.isdir(filespath)):
			raise Exception(filespath + ' is neither a file or directory')
		if absolute_path:
			self.filespath = os.path.abspath(filespath)
		else:
			self.filespath = os.path.relpath(filespath)
		self.skip_files = skip_files
		self.skip_dirs = skip_dirs
		self.filter_func = filter_func
		self.follow_links = follow_links
		self.max_depth = float('inf') if max_depth is None else max_depth
		if os.path.isdir(self.filespath):
			self._walk = None
			self._next = self._next_dir
		elif os.path.isfile(self.filespath):
			self._next = self._next_file

	def __iter__(self):
		return self._next()

	def _skip(self, cur_file):
		if self.skip_files and os.path.isfile(cur_file):
			return True
		if self.skip_dirs and os.path.isdir(cur_file):
			return True
		if self.filter_func is not None:
			if not self.filter_func(cur_file):
				return True
		return False

	def _next_dir(self):
		for root, dirs, files in os.walk(self.filespath, followlinks=self.follow_links):
			if root == self.filespath:
				depth = 0
			else:
				depth = os.path.relpath(root, start=self.filespath).count(os.path.sep) + 1
			if depth >= self.max_depth:
				continue
			for entry in itertools.chain(dirs, files):
				current_path = os.path.join(root, entry)
				if not self._skip(current_path):
					yield current_path
		if self.max_depth >= 0 and not self._skip(self.filespath):
			yield self.filespath

	def _next_file(self):
		if self.max_depth >= 0 and not self._skip(self.filespath):
			yield self.filespath

class SectionConfigParser(object):
	"""
	Proxy access to a section of a ConfigParser object.
	"""
	__version__ = '0.2'
	def __init__(self, section_name, config_parser):
		"""
		:param str section_name: Name of the section to proxy access for.
		:param config_parser: ConfigParser object to proxy access for.
		:type config_parse: :py:class:`ConfigParser.ConfigParser`
		"""
		self.section_name = section_name
		self.config_parser = config_parser

	def _get_raw(self, option, opt_type, default=None):
		get_func = getattr(self.config_parser, 'get' + opt_type)
		if default is None:
			return get_func(self.section_name, option)
		elif self.config_parser.has_option(self.section_name, option):
			return get_func(self.section_name, option)
		else:
			return default

	def get(self, option, default=None):
		"""
		Retrieve *option* from the config, returning *default* if it
		is not present.

		:param str option: The name of the value to return.
		:param default: Default value to return if the option does not exist.
		"""
		return self._get_raw(option, '', default)

	def getint(self, option, default=None):
		"""
		Retrieve *option* from the config, returning *default* if it
		is not present.

		:param str option: The name of the value to return.
		:param default: Default value to return if the option does not exist.
		:rtype: int
		"""
		return self._get_raw(option, 'int', default)

	def getfloat(self, option, default=None):
		"""
		Retrieve *option* from the config, returning *default* if it
		is not present.

		:param str option: The name of the value to return.
		:param default: Default value to return if the option does not exist.
		:rtype: float
		"""
		return self._get_raw(option, 'float', default)

	def getboolean(self, option, default=None):
		"""
		Retrieve *option* from the config, returning *default* if it
		is not present.

		:param str option: The name of the value to return.
		:param default: Default value to return if the option does not exist.
		:rtype: bool
		"""
		return self._get_raw(option, 'boolean', default)

	def has_option(self, option):
		"""
		Check that *option* exists in the configuration file.

		:param str option: The name of the option to check.
		:rtype: bool
		"""
		return self.config_parser.has_option(self.section_name, option)

	def options(self):
		"""
		Get a list of all options that are present in the section of the
		configuration.

		:return: A list of all set options.
		:rtype: list
		"""
		return self.config_parser.options(self.section_name)

	def items(self):
		"""
		Return all options and their values in the form of a list of tuples.

		:return: A list of all values and options.
		:rtype: list
		"""
		return self.config_parser.items(self.section_name)

	def set(self, option, value):
		"""
		Set an option to an arbitrary value.

		:param str option: The name of the option to set.
		:param value: The value to set the option to.
		"""
		self.config_parser.set(self.section_name, option, value)

class TestCase(unittest.TestCase):
	"""
	This class provides additional functionality over the built in
	:py:class:`unittest.TestCase` object, including better compatibility for
	methods across Python 2.x and Python 3.x.
	"""
	def __init__(self, *args, **kwargs):
		super(TestCase, self).__init__(*args, **kwargs)
		if not hasattr(self, 'assertRegex') and hasattr(self, 'assertRegexpMatches'):
			self.assertRegex = self.assertRegexpMatches
		if not hasattr(self, 'assertNotRegex') and hasattr(self, 'assertNotRegexpMatches'):
			self.assertNotRegex = self.assertNotRegexpMatches
		if not hasattr(self, 'assertRaisesRegex') and hasattr(self, 'assertRaisesRegexp'):
			self.assertRaisesRegex = self.assertRaisesRegexp

def configure_stream_logger(logger='', level=None, formatter='%(levelname)-8s %(message)s'):
	"""
	Configure the default stream handler for logging messages to the console,
	remove other logging handlers, and enable capturing warnings.

	.. versionadded:: 1.3.0

	:param str logger: The logger to add the stream handler for.
	:param level: The level to set the logger to, will default to WARNING if no level is specified.
	:type level: None, int, str
	:param formatter: The format to use for logging messages to the console.
	:type formatter: str, :py:class:`logging.Formatter`
	:return: The new configured stream handler.
	:rtype: :py:class:`logging.StreamHandler`
	"""
	level = level or logging.WARNING
	if isinstance(level, str):
		level = getattr(logging, level, None)
		if level is None:
			raise ValueError('invalid log level: ' + level)
	root_logger = logging.getLogger('')
	for handler in root_logger.handlers:
		root_logger.removeHandler(handler)

	logging.getLogger(logger).setLevel(logging.DEBUG)
	console_log_handler = logging.StreamHandler()
	console_log_handler.setLevel(level)
	if isinstance(formatter, str):
		formatter = logging.Formatter(formatter)
	elif not isinstance(formatter, logging.Formatter):
		raise TypeError('formatter must be an instance of logging.Formatter')
	console_log_handler.setFormatter(formatter)
	logging.getLogger(logger).addHandler(console_log_handler)
	logging.captureWarnings(True)
	return console_log_handler

def download(url, filename=None):
	"""
	Download a file from a url and save it to disk.

	:param str url: The URL to fetch the file from.
	:param str filename: The destination file to write the data to.
	"""
	# requirements os, shutil, urllib.parse, urllib.request
	if not filename:
		url_parts = urllib.parse.urlparse(url)
		filename = os.path.basename(url_parts.path)
	url_h = urllib.request.urlopen(url)
	with open(filename, 'wb') as file_h:
		shutil.copyfileobj(url_h, file_h)
	url_h.close()
	return

def escape_single_quote(unescaped):
	"""
	Escape a string containing single quotes and backslashes with backslashes.
	This is useful when a string is evaluated in some way.

	:param str unescaped: The string to escape.
	:return: The escaped string.
	:rtype: str
	"""
	# requirements = re
	return re.sub(r'(\'|\\)', r'\\\1', unescaped)

def format_bytes_size(val):
	"""
	Take a number of bytes and convert it to a human readable number.

	:param int val: The number of bytes to format.
	:return: The size in a human readable format.
	:rtype: str
	"""
	if not val:
		return '0 bytes'
	for sz_name in ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB']:
		if val < 1024.0:
			return "{0:.2f} {1}".format(val, sz_name)
		val /= 1024.0
	raise OverflowError()

def grep(expression, file, flags=0, invert=False):
	"""
	Search a file and return a list of all lines that match a regular expression.

	:param str expression: The regex to search for.
	:param file: The file to search in.
	:type file: str, file
	:param int flags: The regex flags to use when searching.
	:param bool invert: Select non matching lines instead.
	:return: All the matching lines.
	:rtype: list
	"""
	# requirements = re
	if isinstance(file, str):
		file = open(file)
	lines = []
	for line in file:
		if bool(re.search(expression, line, flags=flags)) ^ invert:
			lines.append(line)
	return lines

def is_valid_email_address(email_address):
	"""
	Check that the string specified appears to be a valid email address.

	:param str email_address: The email address to validate.
	:return: Whether the email address appears to be valid or not.
	:rtype: bool
	"""
	# requirements = re
	return EMAIL_REGEX.match(email_address) != None

def get_ip_list(ip_network, mask=None):
	"""
	Quickly convert an IPv4 or IPv6 network (CIDR or Subnet) to a list
	of individual IPs in their string representation.

	:param str ip_network:
	:param int mask:
	:return: list
	"""
	if mask and '/' not in ip_network:
		net = ipaddress.ip_network("{0}/{1}".format(ip_network, mask))
	elif '/' not in ip_network:
		return [str(ipaddress.ip_address(ip_network))]
	else:
		net = ipaddress.ip_network(ip_network)
	hosts = net.hosts()
	if net.netmask == ipaddress.IPv4Address('255.255.255.255') and sys.version_info > (3, 9):
		# see: https://github.com/zeroSteiner/smoke-zephyr/issues/8
		hosts = []
	return [host.__str__() for host in hosts]

def sort_ipv4_list(ip_list, unique=True):
	"""
	Sorts a provided list of IPv4 addresses. Optionally can remove duplicate values
	Supports IPv4 addresses with ports included (ex: [10.11.12.13:80, 10.11.12.13:8080])

	:param ip_list: (list) iterable of IPv4 Addresses
	:param unique: (bool) removes duplicate values if true
	:return: sorted list of IP addresses
	"""
	if unique:
		ip_list = list(set(ip_list))
	ipv4_list = sorted([i.rstrip(':') for i in ip_list], key=lambda ip: (
		int(ip.split(".")[0]),
		int(ip.split(".")[1]),
		int(ip.split(".")[2]),
		int(ip.split(".")[3].split(':')[0]),
		int(ip.split(":")[1]) if ":" in ip else 0
	))
	return ipv4_list

def open_uri(uri):
	"""
	Open a URI in a platform intelligent way. On Windows this will use
	'cmd.exe /c start' and on Linux this will use gvfs-open or xdg-open
	depending on which is available. If no suitable application can be
	found to open the URI, a RuntimeError will be raised.

	.. versionadded:: 1.3.0

	:param str uri: The URI to open.
	"""
	close_fds = True
	startupinfo = None
	proc_args = []
	if sys.platform.startswith('win'):
		proc_args.append(which('cmd.exe'))
		proc_args.append('/c')
		proc_args.append('start')
		uri = uri.replace('&', '^&')
		close_fds = False
		startupinfo = subprocess.STARTUPINFO()
		startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		startupinfo.wShowWindow = subprocess.SW_HIDE
	elif which('gvfs-open'):
		proc_args.append(which('gvfs-open'))
	elif which('xdg-open'):
		proc_args.append(which('xdg-open'))
	else:
		raise RuntimeError('could not find suitable application to open uri')
	proc_args.append(uri)
	proc_h = subprocess.Popen(proc_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=close_fds, startupinfo=startupinfo)
	return proc_h.wait() == 0

def parse_case_camel_to_snake(camel):
	"""
	Convert a string from CamelCase to snake_case.

	:param str camel: The CamelCase string to convert.
	:return: The snake_case version of string.
	:rtype: str
	"""
	# requirements = re
	return re.sub('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))', r'_\1', camel).lower()

def parse_case_snake_to_camel(snake, upper_first=True):
	"""
	Convert a string from snake_case to CamelCase.

	:param str snake: The snake_case string to convert.
	:param bool upper_first: Whether or not to capitalize the first
		character of the string.
	:return: The CamelCase version of string.
	:rtype: str
	"""
	snake = snake.split('_')
	first_part = snake[0]
	if upper_first:
		first_part = first_part.title()
	return first_part + ''.join(word.title() for word in snake[1:])

def parse_server(server, default_port):
	"""
	Convert a server string to a tuple suitable for passing to connect, for
	example converting 'www.google.com:443' to ('www.google.com', 443).

	:param str server: The server string to convert.
	:param int default_port: The port to use in case one is not specified
		in the server string.
	:return: The parsed server information.
	:rtype: tuple
	"""
	server = server.rsplit(':', 1)
	host = server[0]
	if host.startswith('[') and host.endswith(']'):
		host = host[1:-1]
	if len(server) == 1:
		return (host, default_port)
	port = server[1]
	if not port:
		port = default_port
	else:
		port = int(port)
	return (host, port)

def parse_timespan(timedef):
	"""
	Convert a string timespan definition to seconds, for example converting
	'1m30s' to 90. If *timedef* is already an int, the value will be returned
	unmodified.

	:param timedef: The timespan definition to convert to seconds.
	:type timedef: int, str
	:return: The converted value in seconds.
	:rtype: int
	"""
	if isinstance(timedef, int):
		return timedef
	converter_order = ('w', 'd', 'h', 'm', 's')
	converters = {
		'w': 604800,
		'd': 86400,
		'h': 3600,
		'm': 60,
		's': 1
	}
	timedef = timedef.lower()
	if timedef.isdigit():
		return int(timedef)
	elif len(timedef) == 0:
		return 0
	seconds = -1
	for spec in converter_order:
		timedef = timedef.split(spec)
		if len(timedef) == 1:
			timedef = timedef[0]
			continue
		elif len(timedef) > 2 or not timedef[0].isdigit():
			seconds = -1
			break
		adjustment = converters[spec]
		seconds = max(seconds, 0)
		seconds += (int(timedef[0]) * adjustment)
		timedef = timedef[1]
		if not len(timedef):
			break
	if seconds < 0:
		raise ValueError('invalid time format')
	return seconds

def parse_to_slug(words, maxlen=24):
	"""
	Parse a string into a slug format suitable for use in URLs and other
	character restricted applications. Only utf-8 strings are supported at this
	time.

	:param str words: The words to parse.
	:param int maxlen: The maximum length of the slug.
	:return: The parsed words as a slug.
	:rtype: str
	"""
	slug = ''
	maxlen = min(maxlen, len(words))
	for c in words:
		if len(slug) == maxlen:
			break
		c = ord(c)
		if c == 0x27:
			continue
		elif c >= 0x30 and c <= 0x39:
			slug += chr(c)
		elif c >= 0x41 and c <= 0x5a:
			slug += chr(c + 0x20)
		elif c >= 0x61 and c <= 0x7a:
			slug += chr(c)
		elif len(slug) and slug[-1] != '-':
			slug += '-'
	if len(slug) and slug[-1] == '-':
		slug = slug[:-1]
	return slug

def random_string_alphanumeric(size):
	"""
	Generate a random string of *size* length consisting of mixed case letters
	and numbers. This function is not meant for cryptographic purposes.

	:param int size: The length of the string to return.
	:return: A string consisting of random characters.
	:rtype: str
	"""
	# requirements = random, string
	return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(size))

def random_string_lower_numeric(size):
	"""
	Generate a random string of *size* length consisting of lowercase letters
	and numbers. This function is not meant for cryptographic purposes.

	:param int size: The length of the string to return.
	:return: A string consisting of random characters.
	:rtype: str
	"""
	# requirements = random, string
	return ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(size))

def selection_collision(selections, poolsize):
	"""
	Calculate the probability that two random values selected from an arbitrary
	sized pool of unique values will be equal. This is commonly known as the
	"Birthday Problem".

	:param int selections: The number of random selections.
	:param int poolsize: The number of unique random values in the pool to choose from.
	:rtype: float
	:return: The chance that a collision will occur as a percentage.
	"""
	# requirments = sys
	probability = 100.0
	poolsize = float(poolsize)
	for i in range(selections):
		probability = probability * (poolsize - i) / poolsize
	probability = (100.0 - probability)
	return probability

def unescape_single_quote(escaped):
	"""
	Unescape a string which uses backslashes to escape single quotes.

	:param str escaped: The string to unescape.
	:return: The unescaped string.
	:rtype: str
	"""
	escaped = escaped.replace('\\\\', '\\')
	escaped = escaped.replace('\\\'', '\'')
	return escaped

def unique(seq, key=None):
	"""
	Create a unique list or tuple from a provided list or tuple and preserve the
	order.

	:param seq: The list or tuple to preserve unique items from.
	:type seq: list, tuple
	:param key: If key is provided it will be called during the
		comparison process.
	:type key: function, None
	"""
	if key is None:
		key = lambda x: x
	preserved_type = type(seq)
	if preserved_type not in (list, tuple):
		raise TypeError("unique argument 1 must be list or tuple, not {0}".format(preserved_type.__name__))
	seen = []
	result = []
	for item in seq:
		marker = key(item)
		if marker in seen:
			continue
		seen.append(marker)
		result.append(item)
	return preserved_type(result)

def weighted_choice(choices, weight):
	"""
	Make a random selection from the specified choices. Apply the *weight*
	function to each to return a positive integer representing shares of
	selection pool the choice should received. The *weight* function is passed a
	single argument of the choice from the *choices* iterable.

	:param choices: The choices to select from.
	:type choices: list, tuple
	:param weight: The function used for gather weight information for choices.
	:type weight: function
	:return: A randomly selected choice from the provided *choices*.
	"""
	# requirements = random
	weights = []
	# get weight values for each of the choices
	for choice in choices:
		choice_weight = weight(choice)
		if not (isinstance(choice_weight, int) and choice_weight > 0):
			raise TypeError('weight results must be positive integers')
		weights.append(choice_weight)

	# make a selection within the acceptable range
	selection = random.randint(0, sum(weights) - 1)

	# find and return the corresponding choice
	for idx, choice in enumerate(choices):
		if selection < sum(weights[:idx + 1]):
			return choice
	raise RuntimeError('no selection could be made')

def which(program):
	"""
	Locate an executable binary's full path by its name.

	:param str program: The executables name.
	:return: The full path to the executable.
	:rtype: str
	"""
	# requirements = os
	is_exe = lambda fpath: (os.path.isfile(fpath) and os.access(fpath, os.X_OK))
	for path in os.environ['PATH'].split(os.pathsep):
		path = path.strip('"')
		exe_file = os.path.join(path, program)
		if is_exe(exe_file):
			return exe_file
	if is_exe(program):
		return os.path.abspath(program)
	return None

def xfrange(start, stop=None, step=1):
	"""
	Iterate through an arithmetic progression.

	:param start: Starting number.
	:type start: float, int, long
	:param stop: Stopping number.
	:type stop: float, int, long
	:param step: Stepping size.
	:type step: float, int, long
	"""
	if stop is None:
		stop = start
		start = 0.0
	start = float(start)
	while start < stop:
		yield start
		start += step
