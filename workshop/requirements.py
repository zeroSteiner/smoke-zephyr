#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  workshop/requirements.py
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

import distutils.version
import re

import pkg_resources

def check_requirements(requirements_file, ignore=None):
	"""
	Parse a requirements file for package information to determine if
	all requirements are met.

	:param str requirements_file: The file to parse.
	:param ignore: A sequence of packages to ignore.
	:type ignore: list, tuple
	:return: A list of missing or incompatible packages.
	:rtype: list
	"""
	ignore = (ignore or [])
	not_satisfied = []

	installed_packages = dict(map(lambda p: (p.project_name, p), pkg_resources.working_set))
	file_h = open(requirements_file, 'r')
	for req_line in file_h:
		parts = re.match('^([\w\-]+)(([<>=]=)(\d+(\.\d+)*))?$', req_line)
		if not parts:
			continue
		req_pkg = parts.group(1)
		if req_pkg in ignore:
			continue
		if req_pkg not in installed_packages:
			not_satisfied.append(req_pkg)
			continue
		if not parts.group(2):
			continue
		req_version = distutils.version.StrictVersion(parts.group(4))
		installed_pkg = installed_packages[req_pkg]
		installed_version = distutils.version.StrictVersion(installed_pkg.version)
		if parts.group(3) == '==' and not (installed_version == req_version):
			not_satisfied.append(req_pkg)
		elif parts.group(3) == '>=' and not (installed_version >= req_version):
			not_satisfied.append(req_pkg)
		elif parts.group(3) == '<=' and not (installed_version <= req_version):
			not_satisfied.append(req_pkg)
	file_h.close()
	return not_satisfied
