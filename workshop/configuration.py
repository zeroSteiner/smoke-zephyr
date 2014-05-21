#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  workshop/configuration.py
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

import copy
import json
import os
import sys

try:
	import yaml
except ImportError:
	has_yaml = False
else:
	has_yaml = True
	try:
		from yaml import CLoader as Loader, CDumper as Dumper
	except ImportError:
		from yaml import Loader, Dumper

SERIALIZER_DRIVERS = {}
SERIALIZER_DRIVERS['json'] = {'load': json.load, 'dumps': lambda obj: json.dumps(obj, sort_keys=True, indent=4)}
SERIALIZER_DRIVERS['jsn'] = {'load': json.load, 'dumps': lambda obj: json.dumps(obj, sort_keys=True, indent=4)}
SERIALIZER_DRIVERS['yaml'] = {'load': lambda file_obj: yaml.load(file_obj, Loader=Loader), 'dumps': lambda obj: yaml.dumps(obj, default_flow_style=False, Dumper=Dumper)}
SERIALIZER_DRIVERS['yml'] = {'load': lambda file_obj: yaml.load(file_obj, Loader=Loader), 'dumps': lambda obj: yaml.dumps(obj, default_flow_style=False, Dumper=Dumper)}

class Configuration(object):
	"""
	This class provides a generic object for parsing configuration files
	in multiple formats.
	"""
	def __init__(self, configuration_file, prefix=''):
		"""
		@type configuration_file: string
		@param configuration_file: The configuration file to parse.

		@type prefix: string
		@param prefix: String to be prefixed to all option names.
		"""
		self.prefix = prefix
		self.seperator = '.'
		self.configuration_file = configuration_file
		file_h = open(self.configuration_file, 'r')
		self._storage = dict(self._serializer('load', file_h))
		file_h.close()

	@property
	def configuration_file_ext(self):
		"""
		The extension of the current configuration file.
		"""
		return os.path.splitext(self.configuration_file)[1][1:]

	def _serializer(self, operation, *args):
		if not self.configuration_file_ext in SERIALIZER_DRIVERS:
			raise ValueError('unknown file type \'' + self.configuration_file_ext + '\'')
		function = SERIALIZER_DRIVERS[self.configuration_file_ext][operation]
		return function(*args)

	def get_storage(self):
		"""
		Get a copy of the internal configuration.
		"""
		return copy.deepcopy(self._storage)

	def get(self, item_name):
		"""
		Retrieve the value of an option.

		@type item_name: string
		@param item_name: The name of the option to retreive.
		"""
		if self.prefix:
			item_name = self.prefix + self.seperator + item_name
		item_names = item_name.split(self.seperator)
		node = self._storage
		for item_name in item_names:
			node = node[item_name]
		return node

	def has_option(self, option_name):
		"""
		Check that an option exists.

		@type option_name: string
		@param option_name: The name of the option to check.
		"""
		if self.prefix:
			item_name = self.prefix + self.seperator + item_name
		item_names = option_name.split(self.seperator)
		node = self._storage
		for item_name in item_names:
			if not item_name in node:
				return False
			node = node[item_name]
		return True

	def has_section(self, section_name):
		"""
		Checks that an option exists and that it contains sub options.

		@type section_name: string
		@param section_name: The name of the section to check.
		"""
		if not self.has_option(section_name):
			return False
		return isinstance(self.get(section_name), dict)

	def set(self, item_name, item_value):
		"""
		Sets the value of an option in the configuration.

		@type item_name: string
		@param item_name: The name of the option to set.

		@type item_value: *
		@param item_value: The value of the option to set.
		"""
		if self.prefix:
			item_name = self.prefix + self.seperator + item_name
		item_names = item_name.split(self.seperator)
		item_last = item_names.pop()
		node = self._storage
		for item_name in item_names:
			if not item_name in node:
				node[item_name] = {}
			node = node[item_name]
		node[item_last] = item_value
		return

	def save(self):
		"""
		Save the current configuration to disk.
		"""
		file_h = open(self.configuration_file, 'wb')
		file_h.write(self._serializer('dumps', self._storage))
		file_h.close()

def main():
	import argparse

	parser = argparse.ArgumentParser(description='Parse a configuration file', conflict_handler='resolve')
	parser.add_argument('config_file', action='store', help='configuration file to parse')
	parser.add_argument('option', action='store', help='option to retreive the value from')
	arguments = parser.parse_args()

	config = Configuration(arguments.config_file)
	if not config.has_option(arguments.option):
		return 1
	print(config.get(arguments.option))
	return 0

if __name__ == '__main__':
	sys.exit(main())
