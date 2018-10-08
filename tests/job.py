#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  tests/job.py
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

import contextlib
import time
import unittest
import uuid

from smoke_zephyr import job
from smoke_zephyr import utilities

ROUTINE_SLEEP_TIME = 1.5
def test_routine():
	time.sleep(ROUTINE_SLEEP_TIME)

def test_routine_delete():
	return job.JobRequestDelete()

class JobManagerTests(utilities.TestCase):
	def setUp(self):
		self.assertGreater(ROUTINE_SLEEP_TIME, 1)
		self.jm = job.JobManager()
		self.jm.start()

	def tearDown(self):
		self.jm.stop()

	@contextlib.contextmanager
	def _job_add(self, callback, parameters=None, expiration=1, wait=True):
		jid = self.jm.job_add(callback, parameters, seconds=1, expiration=expiration)
		self.assertIsInstance(jid, uuid.UUID)
		self.assertTrue(self.jm.job_exists(jid))
		self.assertEqual(self.jm.job_count(), 1)
		self.assertEqual(self.jm.job_count_enabled(), 1)
		yield jid
		if wait:
			time.sleep(ROUTINE_SLEEP_TIME * 2)

	def test_job_init(self):
		self.assertEqual(self.jm.job_count(), 0)
		self.assertEqual(self.jm.job_count_enabled(), 0)

	def test_job_add(self):
		test_list = []
		data = utilities.random_string_alphanumeric(10)
		with self._job_add(test_list.append, data) as jid:
			self.assertEqual(len(test_list), 0)
		self.assertEqual(len(test_list), 1)
		self.assertIn(data, test_list)
		self.assertFalse(self.jm.job_exists(jid))

	def test_job_delete(self):
		with self._job_add(test_routine, wait=False) as jid:
			self.jm.job_delete(jid)
			self.assertEqual(self.jm.job_count(), 0)
			self.assertEqual(self.jm.job_count_enabled(), 0)

	def test_job_disable(self):
		with self._job_add(test_routine, wait=False) as jid:
			self.jm.job_disable(jid)
			self.assertEqual(self.jm.job_count(), 1)
			self.assertEqual(self.jm.job_count_enabled(), 0)

	def test_job_request_delete(self):
		with self._job_add(test_routine_delete) as jid:
			self.assertTrue(self.jm.job_exists(jid))
		result = self.jm.job_exists(jid)
		self.assertFalse(result)
		self.assertEqual(self.jm.job_count(), 0)
		self.assertEqual(self.jm.job_count_enabled(), 0)

	def test_job_run(self):
		jid = self.jm.job_run(test_routine)
		self.assertIsInstance(jid, uuid.UUID)
		self.assertTrue(self.jm.job_is_running(jid))
		self.assertEqual(self.jm.job_count(), 1)
		self.assertEqual(self.jm.job_count_enabled(), 1)
		time.sleep(ROUTINE_SLEEP_TIME * 2)

		self.assertFalse(self.jm.job_is_running(jid))

if __name__ == '__main__':
	unittest.main()
