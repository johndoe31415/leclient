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

class Configuration():
	def __init__(self, dirname):
		self._dirname = os.path.realpath(os.path.expanduser(dirname))
		self._filename = self._dirname + "/leclient.json"
		try:
			with open(self._filename) as f:
				self._config = json.load(f)
		except FileNotFoundError:
			self._config = None
		self._create_dir()

	@property
	def base_dir(self):
		return self._dirname

	@property
	def challenge_dir(self):
		return self._config["challenge_dir"]

	@property
	def account_key(self):
		return self._config["account_key"]

	@property
	def server_key(self):
		return self._config["server_key"]

	@property
	def server_csr(self):
		return self._config["server_csr"]

	@property
	def certificate_file(self):
		return self._config["certificate_file"]

	@property
	def certificate_chain_file(self):
		return self._config["certificate_chain_file"]

	@property
	def renew_days_before_expiry(self):
		return self._config["renew_days_before_expiry"]

	@property
	def renewed_trigger_file(self):
		return self._config["renewed_trigger_file"]

	@property
	def hostnames(self):
		return self._config["hostnames"]

	@property
	def apache2_template_dir(self):
		return self._config["apache2_template_dir"]

	@property
	def configured(self):
		return self._config is not None

	def _create_dir(self):
		with contextlib.suppress(FileExistsError):
			os.makedirs(self._dirname)
			os.chmod(self._dirname, 0o700)

		if self.configured:
			with contextlib.suppress(FileExistsError):
				os.makedirs(self.challenge_dir)
			with contextlib.suppress(FileExistsError):
				os.makedirs(self.apache2_template_dir)

	def write(self):
		with open(self._filename, "w") as f:
			json.dump(self._config, f, indent = 4, sort_keys = True)

	def set_initial_config(self, hostnames, key_file = None):
		if key_file is None:
			key_file = self._dirname + "/keys/server.key"
		else:
			key_file = os.path.realpath(key_file)
		self._config = {
			"hostnames":						hostnames,
			"challenge_dir":					self._dirname + "/challenges",
			"account_key":						self._dirname + "/keys/account.key",
			"server_key":						key_file,
			"server_csr":						self._dirname + "/server.csr",
			"certificate_file":					self._dirname + "/certificate.pem",
			"certificate_chain_file":			self._dirname + "/certificate_chain.pem",
			"renewed_trigger_file":				self._dirname + "/csr_renewed.trigger",
			"renew_days_before_expiry":			30,
			"apache2_template_dir":				self._dirname + "/conf",
		}
