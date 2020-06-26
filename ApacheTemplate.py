#!/usr/bin/python3
#	leclient - Let's encrypt frontend tooling and configuration
#	Copyright (C) 2020-2020 Johannes Bauer
#
#	This file is part of leclient.
#
#	leclient is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	leclient is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with leclient. If not, see <http://www.gnu.org/licenses/>.
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import os
import datetime

class ApacheTemplate():
	def __init__(self, config):
		self._config = config

	def _render(self, source_name, variables):
		with open(source_name) as f:
			template = f.read()
		replacements = {
			"now":				datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
		}
		replacements.update(variables)
		for (src, dst) in replacements.items():
			src_pattern = "${" + src + "}"
			template = template.replace(src_pattern, dst)
		return template


	def render_http(self):
		return self._render("apache_config_template_http.conf", {
			"hostname":			self._config.hostnames[0],
			"challenge_dir":	os.path.realpath(self._config.challenge_dir),
		})

	def render_https(self, hostname):
		return self._render("apache_config_template_https.conf", {
			"hostname":			hostname,
			"cert_filename":	self._config.certificate_file,
			"chain_filename":	self._config.certificate_chain_file,
			"key_filename":		self._config.server_key,
		})
