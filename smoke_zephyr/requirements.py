#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  smoke_zephyr/requirements.py
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

import distutils.version # pylint: disable=E0611
import re

import pkg_resources

def check_requirements(requirements, ignore=None):
	"""
	Parse requirements for package information to determine if all requirements
	are met. The *requirements* argument can be a string to a requirements file,
	a file like object to be read, or a list of strings representing the package
	requirements.

	:param requirements: The file to parse.
	:type requirements: file obj, list, str, tuple
	:param ignore: A sequence of packages to ignore.
	:type ignore: list, tuple
	:return: A list of missing or incompatible packages.
	:rtype: list
	"""
	ignore = (ignore or [])
	not_satisfied = []
	working_set = pkg_resources.working_set
	installed_packages = dict((p.project_name, p) for p in working_set)  # pylint: disable=E1133

	if isinstance(requirements, str):
		with open(requirements, 'r') as file_h:
			requirements = file_h.readlines()
	elif hasattr(requirements, 'readlines'):
		requirements = requirements.readlines()
	elif not isinstance(requirements, (list, tuple)):
		raise TypeError('invalid type for argument requirements')

	for req_line in requirements:
		req_line = req_line.strip()
		parts = re.match(r'^([\w\-]+)(([<>=]=)(\d+(\.\d+)*))?$', req_line)
		if not parts:
			raise ValueError("requirement '{0}' is in an invalid format".format(req_line))
		req_pkg = parts.group(1)
		if req_pkg in ignore:
			continue
		if req_pkg not in installed_packages:
			try:
				find_result = working_set.find(pkg_resources.Requirement.parse(req_line))
			except pkg_resources.ResolutionError:
				find_result = False
			if not find_result:
				not_satisfied.append(req_pkg)
			continue
		if not parts.group(2):
			continue
		req_version = distutils.version.StrictVersion(parts.group(4))
		installed_pkg = installed_packages[req_pkg]
		installed_version = re.match(r'^((\d+\.)*\d+)', installed_pkg.version)
		if not installed_version:
			not_satisfied.append(req_pkg)
			continue
		installed_version = distutils.version.StrictVersion(installed_version.group(0))
		if parts.group(3) == '==' and installed_version != req_version:
			not_satisfied.append(req_pkg)
		elif parts.group(3) == '>=' and installed_version < req_version:
			not_satisfied.append(req_pkg)
		elif parts.group(3) == '<=' and installed_version > req_version:
			not_satisfied.append(req_pkg)
	return not_satisfied
