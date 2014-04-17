#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  utilities/__init__.py
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
#  * Neither the name of the  nor the names of its
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
import os
import re
import time

__version__ = '0.1'

class Cache(object):
	"""
	This class provides a simple to use cache object which can be applied
	as a decorator.
	"""
	def __init__(self, timeout):
		"""
		@type timeout: string, integer
		@param timeout: The amount of time in seconds that a cached
		result will be considered valid for.
		"""
		if isinstance(timeout, (str, unicode)):
			timeout = timedef_to_seconds(timeout)
		self.cache_timeout = timeout
		self.__cache = {}

	def __call__(self, *args):
		if not hasattr(self, '_target_function'):
			self._target_function = args[0]
			return self
		self.cache_clean()
		if not isinstance(args, collections.Hashable):
			return self._target_function(*args)
		result, expiration = self.__cache.get(args, (None, 0))
		if expiration > time.time():
			return result
		result = self._target_function(*args)
		self.__cache[args] = (result, time.time() + self.cache_timeout)
		return result

	def __repr__(self):
		return "<cached function {0}>".format(self._target_function.__name__)

	def cache_clean(self):
		"""
		Remove expired items from the cache.
		"""
		now = time.time()
		keys_for_removal = []
		for key, (value, expiration) in self.__cache.items():
			if expiration < now:
				keys_for_removal.append(key)
		for key in keys_for_removal:
			del self.__cache[key]

	def cache_clear(self):
		"""
		Remove all items from the cache.
		"""
		self.__cache = {}

class FileWalker:
	"""
	This class is used to easily iterate over files in a directory.
	"""
	def __init__(self, filespath, absolute_path = False, skip_files = False, skip_dirs = False, filter_func = None):
		"""
		@type filespath: string
		@param filespath: A path to either a file or a directory.  If a
		file is passed then that will be the only file returned during the
		iteration.  If a directory is passed, all files will be recursively
		returned during the iteration.

		@type absolute_path: boolean
		@param absolute_path: Whether or not the absolute path or a relative
		path should be returned.

		@type skip_files: boolean
		@param skip_files: Whether or not to skip files.

		@type skip_dirs: boolean
		@param skip_dirs: Whether or not to skip directories.

		@type filter_func: function
		@param filter_func: If defined, the filter_func function will be called
		for each file and if the function returns false the file will be
		skipped.
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
		if os.path.isdir(self.filespath):
			self.__iter__= self._next_dir
		elif os.path.isfile(self.filespath):
			self.__iter__ = self._next_file

	def _skip(self, cur_file):
		if self.skip_files and os.path.isfile(cur_file):
			return True
		if self.skip_dirs and os.path.isdir(cur_file):
			return True
		if self.filter_func != None:
			if not self.filter_func(cur_file):
				return True
		return False

	def _next_dir(self):
		for root, dirs, files in os.walk(self.filespath):
			for cur_file in files:
				cur_file = os.path.join(root, cur_file)
				if not self._skip(cur_file):
					yield cur_file
			for cur_dir in dirs:
				cur_dir = os.path.join(root, cur_dir)
				if not self._skip(cur_dir):
					yield cur_dir
		raise StopIteration

	def _next_file(self):
		if not self._skip(self.filespath):
			yield self.filespath
		raise StopIteration

class SectionConfigParser(object):
	"""
	Proxy access to a section of a ConfigParser object.
	"""
	__version__ = '0.1'
	def __init__(self, section_name, config_parser):
		"""
		@type section_name: string
		@param section_name: Name of the section to proxy access for.

		@type config_parser: ConfigParser.ConfigParser instance
		@param config_parser: ConfigParser object to proxy access for.
		"""
		self.section_name = section_name
		self.config_parser = config_parser

	def get_raw(self, option, opt_type, default = None):
		get_func = getattr(self.config_parser, 'get' + opt_type)
		if default == None:
			return get_func(self.section_name, option)
		elif self.config_parser.has_option(self.section_name, option):
			return get_func(self.section_name, option)
		else:
			return default

	def get(self, option, default = None):
		return self.get_raw(option, '', default)

	def getint(self, option, default = None):
		return self.get_raw(option, 'int', default)

	def getfloat(self, option, default = None):
		return self.get_raw(option, 'float', default)

	def getboolean(self, option, default = None):
		return self.get_raw(option, 'boolean', default)

	def has_option(self, option):
		return self.config_parser.has_option(self.section_name, option)

	def options(self):
		return self.config_parser.options(self.section_name)

	def items(self):
		return self.config_parser.items(self.section_name)

def parse_case_camel_to_snake(string):
	return re.sub('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))', r'_\1', string).lower()

def parse_case_snake_to_camel(string, upper_first = True):
	string = string.split('_')
	first_part = string[0]
	if upper_first:
		first_part = first_part.title()
	second_part = ''.join(map(lambda word: word.title(), string[1:]))
	return first_part + second_part

def parse_server(server, default_port):
	"""
	Convert a server string to a tuple suitable for passing to connect, for
	example converting 'www.google.com:443' to ('www.google.com', 443).

	@type server: string
	@param server: The server string to convert.

	@type default_port: integer
	@param default_port: The port to use in case one is not specified in
	the server string.
	"""
	server = server.split(':')
	host = server[0]
	if len(server) == 1:
		return (host, default_port)
	else:
		port = server[1]
		if not port:
			port = default_port
		else:
			port = int(port)
		return (host, port)

def parse_timespan(timedef):
	"""
	Convert a string timespan definition to seconds, for example converting
	'1m30s' to 90.

	@type timedef: string
	@param timedef: The timespan definition to convert to seconds.
	"""
	converter_order = ['w', 'd', 'h', 'm', 's']
	converters = {
		'w': 604800,
		'd': 86400,
		'h': 3600,
		'm': 60,
		's': 1
	}
	timedef = timedef.lower()
	seconds = 0
	for spec in converter_order:
		timedef = timedef.split(spec)
		if len(timedef) == 1:
			timedef = timedef[0]
			continue
		elif len(timedef) > 2 or not timedef[0].isdigit():
			raise ValueError('invalid time format')
		adjustment = converters[spec]
		seconds += (int(timedef[0]) * adjustment)
		timedef = timedef[1]
		if not len(timedef):
			break
	if timedef.isdigit():
		seconds += int(timedef)
	return seconds

def unique(seq, key = None):
	"""
	Unique a list or tuple and preserve the order

	@type seq: list, tuple
	@param seq: The list or tuple to preserve unique items from.

	@type key: Function or None
	@param key: If key is provided it will be called during the
	comparison process.
	"""
	if key is None:
		key = lambda x: x
	preserved_type = type(seq)
	seen = {}
	result = []
	for item in seq:
		marker = key(item)
		if marker in seen:
			continue
		seen[marker] = 1
		result.append(item)
	return preserved_type(result)

def which(program):
	"""
	Locate an executable binary's full path by its name.

	@type program: string
	@param program: The executables name.
	"""
	is_exe = lambda fpath: (os.path.isfile(fpath) and os.access(fpath, os.X_OK))
	if is_exe(program):
		return program
	for path in os.environ["PATH"].split(os.pathsep):
		path = path.strip('"')
		exe_file = os.path.join(path, program)
		if is_exe(exe_file):
			return exe_file
	return None

def xfrange(start, stop, step):
	"""
	Iterate through an arithmetic progression.

	@type start: int, long, float
	@param start: Starting number.

	@type stop: int, long, float
	@param stop: Stopping number.

	@type step: int, long, float
	@param step: Stepping size.
	"""
	while start < stop:
		yield start
		start += step
