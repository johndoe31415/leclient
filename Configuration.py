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
import json
import contextlib
import collections

class Configuration():
	def __init__(self, dirname):
		self._dirname = os.path.realpath(os.path.expanduser(dirname))
		self._filename = self._dirname + "/config.json"
		try:
			with open(self._filename) as f:
				self._config = json.load(f)
		except FileNotFoundError:
			self._config = None
		self._create_dirs()

	@property
	def base_dir(self):
		return self._dirname

	@property
	def requests(self):
		return iter(self._config["requests"])

	@property
	def challenge_dir(self):
		return self._config["challenge_dir"]

	@property
	def account_key(self):
		return self._config["account_key"]

	@property
	def renew_days_before_expiration(self):
		return self._config["renew_days_before_expiration"]

	@property
	def renew_trigger_file(self):
		return self._config["renew_trigger_file"]

	@property
	def apache2_config_template_dir(self):
		return self._config["apache2_config_template_dir"]

	@property
	def configured(self):
		return self._config is not None

	def _create_dir(self, dirname):
		with contextlib.suppress(FileExistsError):
			os.makedirs(dirname)
			os.chmod(dirname, 0o700)

	def _create_filedir(self, filename):
		return self._create_dir(os.path.dirname(filename))

	def _create_dirs(self):
		self._create_dir(self._dirname)
		if self.configured:
			self._create_dir(self.challenge_dir)
			self._create_filedir(self.account_key)
			self._create_filedir(self.renew_trigger_file)
			self._create_dir(self.apache2_config_template_dir)
			for request in self.requests:
				self._create_filedir(request["server_crt"])
				self._create_filedir(request["server_crt_chain"])
				self._create_filedir(request["server_csr"])
				self._create_filedir(request["server_key"])

	def write(self):
		with open(self._filename, "w") as f:
			json.dump(self._config, f, indent = 4, sort_keys = True)

	def set_initial_config(self, hostname_dict):
		requests = [ ]
		for (name, hostnames) in hostname_dict.items():
			request = collections.OrderedDict((
				("name", name),
				("hostnames", hostnames),
				("server_crt", "%s/crt/%s.crt" % (self._dirname, name)),
				("server_crt_chain", "%s/crt_chain/%s.crt" % (self._dirname, name)),
				("server_key", "%s/key/%s.key" % (self._dirname, name)),
				("server_csr", "%s/csr/%s.csr" % (self._dirname, name)),
			))
			requests.append(request)

		self._config = collections.OrderedDict((
			("challenge_dir",					self._dirname + "/challenges"),
			("account_key",						self._dirname + "/account.key"),
			("requests",						requests),
			("renew_trigger_file",				self._dirname + "/crt_renewed.trigger"),
			("renew_days_before_expiration",	30),
			("apache2_config_template_dir",		self._dirname + "/conf"),
		))
		self._create_dirs()
