#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  tests/utilities.py
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
import unittest

from smoke_zephyr import utilities

SINGLE_QUOTE_STRING_ESCAPED = """C:\\\\Users\\\\Alice\\\\Desktop\\\\Alice\\'s Secret File.txt"""
SINGLE_QUOTE_STRING_UNESCAPED = """C:\\Users\\Alice\\Desktop\\Alice's Secret File.txt"""

def cache_test(first_name, last_name, email=None, dob=None):
	return utilities.random_string_alphanumeric(24)

class UtilitiesCacheTests(utilities.TestCase):
	def test_cache(self):
		target_function = utilities.Cache('6h')(cache_test)

		result_alice = target_function('alice', 'liddle')
		self.assertEqual(target_function('alice', 'liddle'), result_alice)

		result_calie = target_function('calie', 'liddle')
		self.assertEqual(target_function('calie', 'liddle'), result_calie)
		self.assertNotEqual(result_alice, result_calie)

		result_alice = target_function('alice', 'liddle', email='aliddle@wonderland.com')
		self.assertEqual(target_function('alice', 'liddle', email='aliddle@wonderland.com'), result_alice)
		self.assertNotEqual(result_alice, result_calie)

	def test_cache_cache_clear(self):
		target_function = utilities.Cache('6h')(cache_test)
		result_alice = target_function('alice', 'liddle')
		target_function.cache_clear()
		self.assertNotEqual(target_function('alice', 'liddle'), result_alice)

	def test_cache_flatten_args(self):
		target_function = utilities.Cache('6h')(cache_test)
		flatten_args = target_function._flatten_args  # pylint: disable=W0212
		self.assertEqual(
			flatten_args(('alice',), {'last_name': 'liddle'}),
			collections.deque(('alice', 'liddle', None, None))
		)
		self.assertEqual(
			flatten_args(('alice',), {'last_name': 'liddle', 'email': 'aliddle@wonderland.com'}),
			collections.deque(('alice', 'liddle', 'aliddle@wonderland.com', None))
		)
		self.assertEqual(
			flatten_args(('alice', 'liddle'), {}),
			collections.deque(('alice', 'liddle', None, None))
		)
		self.assertEqual(
			flatten_args(('alice', 'liddle'), {}),
			collections.deque(('alice', 'liddle', None, None))
		)
		self.assertEqual(
			flatten_args(('alice', 'liddle', 'aliddle@wonderland.com'), {}),
			collections.deque(('alice', 'liddle', 'aliddle@wonderland.com', None))
		)
		self.assertEqual(
			flatten_args(('alice', 'liddle'), {'dob': '1990'}),
			collections.deque(('alice', 'liddle', None, '1990'))
		)

		with self.assertRaisesRegex(TypeError, r'^cache_test\(\) missing required argument \'last_name\'$'):
			flatten_args(('alice',), {})
		with self.assertRaisesRegex(TypeError, r'^cache_test\(\) got an unexpected keyword argument \'foobar\'$'):
			flatten_args(('alice', 'liddle'), {'foobar': True})

class UtilitiesTests(utilities.TestCase):
	def test_attribute_dict(self):
		ad = utilities.AttributeDict(test=1)
		self.assertIsInstance(ad, utilities.AttributeDict)
		self.assertEqual(ad['test'], ad.test)
		self.assertEqual(ad.test, 1)

	def test_escape_single_quote(self):
		escaped_string = utilities.escape_single_quote(SINGLE_QUOTE_STRING_UNESCAPED)
		self.assertEqual(escaped_string, SINGLE_QUOTE_STRING_ESCAPED)

	def test_get_ip_list(self):
		cases = {
			('192.168.1.0', None): ['192.168.1.0'],
			('192.168.2.0/32', None): [],
			('192.168.3.0/30', None): ['192.168.3.1', '192.168.3.2'],
			('192.168.4.0', 32): [],
			('192.168.5.0', 30): ['192.168.5.1', '192.168.5.2'],
		}
		for (ip_network, mask), ip_list in cases.items():
			returned_ip_list = utilities.get_ip_list(ip_network, mask=mask)
			self.assertEqual(returned_ip_list, ip_list, msg=("get_ip_list({!r}, mask={!r}) != {!r}".format(ip_network, mask, ip_list)))

	def test_is_valid_email_address(self):
		valid_emails = [
			'aliddle@wonderland.com',
			'aliddle@wonderland.co.uk',
			'alice.liddle1+spam@wonderland.com',
		]
		invalid_emails = [
			'aliddle.wonderland.com'
			'aliddle+',
			'aliddle@',
			'aliddle',
			'',
			'@wonderland.com',
			'@wonder@land.com',
			'aliddle@.com'
		]
		for address in valid_emails:
			self.assertTrue(utilities.is_valid_email_address(address))
		for address in invalid_emails:
			self.assertFalse(utilities.is_valid_email_address(address))

	def test_parse_case_camel_to_snake(self):
		parsed = utilities.parse_case_camel_to_snake('SmokeZephyr')
		self.assertEqual(parsed, 'smoke_zephyr')

	def test_parse_case_snake_to_camel(self):
		parsed = utilities.parse_case_snake_to_camel('smoke_zephyr')
		self.assertEqual(parsed, 'SmokeZephyr')
		parsed = utilities.parse_case_snake_to_camel('smoke_zephyr', False)
		self.assertEqual(parsed, 'smokeZephyr')

	def test_parse_server(self):
		parsed = utilities.parse_server('127.0.0.1', 80)
		self.assertIsInstance(parsed, tuple)
		self.assertEqual(len(parsed), 2)
		self.assertEqual(parsed[0], '127.0.0.1')
		self.assertEqual(parsed[1], 80)
		parsed = utilities.parse_server('127.0.0.1:8080', 80)
		self.assertIsInstance(parsed, tuple)
		self.assertEqual(len(parsed), 2)
		self.assertEqual(parsed[0], '127.0.0.1')
		self.assertEqual(parsed[1], 8080)
		parsed = utilities.parse_server('[::1]:8080', 80)
		self.assertIsInstance(parsed, tuple)
		self.assertEqual(len(parsed), 2)
		self.assertEqual(parsed[0], '::1')
		self.assertEqual(parsed[1], 8080)

	def test_parse_timespan(self):
		self.assertRaises(ValueError, utilities.parse_timespan, 'fake')
		self.assertEqual(utilities.parse_timespan(''), 0)
		self.assertEqual(utilities.parse_timespan('30'), 30)
		self.assertEqual(utilities.parse_timespan('1m30s'), 90)
		self.assertEqual(utilities.parse_timespan('2h1m30s'), 7290)
		self.assertEqual(utilities.parse_timespan('3d2h1m30s'), 266490)

	def test_parse_to_slug(self):
		parsed = utilities.parse_to_slug('Smoke Zephyr!')
		self.assertEqual(parsed, 'smoke-zephyr')
		parsed = utilities.parse_to_slug('_Smoke Zephyr! (Next Try)')
		self.assertEqual(parsed, 'smoke-zephyr-next-try')

	def test_selection_collision(self):
		chance = utilities.selection_collision(30, 365)
		self.assertAlmostEqual(chance, 70.6316243)

	def test_sort_ipv4_list(self):
		cases = [
			(['9.8.7.6', '1.2.3.4'], ['1.2.3.4', '9.8.7.6']),
			(['11.22.33.44', '2.3.4.5'], ['2.3.4.5', '11.22.33.44']),
		]
		for in_list, out_list in cases:
			self.assertEquals(utilities.sort_ipv4_list(in_list), out_list)
		self.assertEquals(utilities.sort_ipv4_list(['1.2.3.4', '1.2.3.4'], unique=True), ['1.2.3.4'])

	def test_unescape_single_quote(self):
		unescaped_string = utilities.unescape_single_quote(SINGLE_QUOTE_STRING_ESCAPED)
		self.assertEqual(unescaped_string, SINGLE_QUOTE_STRING_UNESCAPED)

if __name__ == '__main__':
	unittest.main()
