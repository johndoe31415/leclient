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
import mako.lookup

class TemplateGenerator():
	def __init__(self, config):
		self._config = config
		self._lookup = mako.lookup.TemplateLookup([ "." ], strict_undefined = True)

	def _render(self, source_name, variables):
		template = self._lookup.get_template(source_name)
		variables.update({
			"now":				datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
		})
		return template.render(**variables)

	def render_http(self):
		hostnames = set()
		for request in self._config.requests:
			hostnames |= set(request["hostnames"])
		hostnames = sorted(hostnames)
		return self._render("apache_config_template_http.conf", {
			"hostnames":		hostnames,
			"challenge_dir":	os.path.realpath(self._config.challenge_dir),
		})

	def render_https(self, request):
		return self._render("apache_config_template_https.conf", {
			"hostnames":		request["hostnames"],
			"cert_filename":	request["server_crt"],
			"chain_filename":	request["server_crt_chain"],
			"key_filename":		request["server_key"],
		})

	def render_systemd_service(self, executable):
		return self._render("systemd.service", {
			"renew_executable":	executable,
		})

	def render_systemd_timer(self):
		return self._render("systemd.timer", { })
