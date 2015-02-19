#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  tests/configuration.py
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

import os
import unittest

from smoke_zephyr.utilities import Cache
from smoke_zephyr.utilities import TestCase
from smoke_zephyr.utilities import random_string_alphanumeric

def cache_test(first_name, last_name, email=None, dob=None):
	return random_string_alphanumeric(24)

class UtilitiesCacheTests(TestCase):
	def test_cache(self):
		target_function = Cache('6h')(cache_test)

		result_alice = target_function('alice', 'liddle')
		self.assertEqual(target_function('alice', 'liddle'), result_alice)

		result_calie = target_function('calie', 'liddle')
		self.assertEqual(target_function('calie', 'liddle'), result_calie)
		self.assertNotEqual(result_alice, result_calie)

		result_alice = target_function('alice', 'liddle', email='aliddle@wonderland.com')
		self.assertEqual(target_function('alice', 'liddle', email='aliddle@wonderland.com'), result_alice)
		self.assertNotEqual(result_alice, result_calie)

	def test_cache_cache_clear(self):
		target_function = Cache('6h')(cache_test)
		result_alice = target_function('alice', 'liddle')
		target_function.cache_clear()
		self.assertNotEqual(target_function('alice', 'liddle'), result_alice)

	def test_cache_flatten_args(self):
		target_function = Cache('6h')(cache_test)
		flatten_args = target_function._flatten_args
		self.assertEqual(flatten_args(('alice',), {'last_name': 'liddle'}), ('alice', 'liddle', None, None))
		self.assertEqual(flatten_args(('alice',), {'last_name': 'liddle', 'email': 'aliddle@wonderland.com'}), ('alice', 'liddle', 'aliddle@wonderland.com', None))
		self.assertEqual(flatten_args(('alice', 'liddle'), {}), ('alice', 'liddle', None, None))
		self.assertEqual(flatten_args(('alice', 'liddle'), {}), ('alice', 'liddle', None, None))
		self.assertEqual(flatten_args(('alice', 'liddle', 'aliddle@wonderland.com'), {}), ('alice', 'liddle', 'aliddle@wonderland.com', None))
		self.assertEqual(flatten_args(('alice', 'liddle'), {'dob': '1990'}), ('alice', 'liddle', None, '1990'))

		with self.assertRaisesRegex(TypeError, r'^cache_test\(\) missing required argument \'last_name\'$'):
			flatten_args(('alice',), {})
		with self.assertRaisesRegex(TypeError, r'^cache_test\(\) got an unexpected keyword argument \'foobar\'$'):
			flatten_args(('alice', 'liddle'), {'foobar': True})

if __name__ == '__main__':
	unittest.main()
