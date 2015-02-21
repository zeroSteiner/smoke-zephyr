#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  tests/argparse_types.py
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

import argparse
import logging
import os
import unittest

from smoke_zephyr import argparse_types
from smoke_zephyr import utilities

class ArgparseTypeTests(utilities.TestCase):
	def _invalid_argparse_type(self, function, invalid):
		with self.assertRaises(argparse.ArgumentTypeError):
			function(invalid)

	def _valid_argparse_type(self, function, valid, valid_result=None, valid_result_type=None):
		valid_result = valid if valid_result == None else valid_result
		valid_result_type = valid_result_type or str
		result = function(valid)
		self.assertEqual(result, valid_result)
		self.assertIsInstance(result, valid_result_type)

	def test_bin_b64_type(self):
		self._invalid_argparse_type(argparse_types.bin_b64_type, '0')
		self._valid_argparse_type(argparse_types.bin_b64_type, 'SGVsbG8gV29ybGQh', b'Hello World!', bytes)

	def test_bin_hex_type(self):
		self._invalid_argparse_type(argparse_types.bin_hex_type, 'FAKE')
		self._valid_argparse_type(argparse_types.bin_hex_type, '48656c6c6f20576f726c6421', b'Hello World!', bytes)

	def test_dir_type(self):
		self._invalid_argparse_type(argparse_types.dir_type, 'FAKE')
		self._valid_argparse_type(argparse_types.dir_type, os.getcwd(), os.getcwd())
		self._valid_argparse_type(argparse_types.dir_type, '.', '.')

	def test_log_level_type(self):
		self._invalid_argparse_type(argparse_types.log_level_type, 'FAKE')
		for level_name in ('NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
			self._valid_argparse_type(argparse_types.log_level_type, level_name, getattr(logging, level_name), int)

	def test_port_type(self):
		self._invalid_argparse_type(argparse_types.port_type, 'FAKE')
		self._invalid_argparse_type(argparse_types.port_type, '65536')
		self._valid_argparse_type(argparse_types.port_type, '80', 80, int)

	def test_timespan_type(self):
		self._invalid_argparse_type(argparse_types.timespan_type, 'FAKE')
		self._invalid_argparse_type(argparse_types.timespan_type, '30x')
		self._valid_argparse_type(argparse_types.timespan_type, '80', 80, int)
		self._valid_argparse_type(argparse_types.timespan_type, '1m', 60, int)
		self._valid_argparse_type(argparse_types.timespan_type, '1h', 3600, int)
		self._valid_argparse_type(argparse_types.timespan_type, '1h1m', 3660, int)

if __name__ == '__main__':
	unittest.main()
