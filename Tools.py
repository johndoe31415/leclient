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

import re
import subprocess
import tempfile
import textwrap
import datetime

class UITools():
	@classmethod
	def confirm(cls, prompt):
		while True:
			yn = input(prompt)
			yn = yn.lower()
			if yn == "y":
				return True
			elif yn == "n":
				return False

	@classmethod
	def choice(cls, options, prompt):
		while True:
			for (oid, (option_id, option_text)) in enumerate(options, 1):
				print("%2d) %s" % (oid, option_text))
			value = input(prompt)
			try:
				value = int(value) - 1
			except ValueError:
				continue
			if (value >= 0) and (value < len(options)):
				return options[value][0]

class CertTools():
	HOSTNAME_REGEX = re.compile(r"X509v3 Subject Alternative Name:[ \t]*\n(?P<names>[^\n]+)", flags = re.MULTILINE)
	DNSNAME_SPLITTER = re.compile(r", ")
	NOT_AFTER_REGEX = re.compile(r"notAfter=(?P<month>[A-Za-z]{3})\s+(?P<day>\d+)\s+(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}) (?P<year>\d{4}) GMT")
	MONTHS = { name: monthno for (monthno, name) in enumerate([ "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec" ], 1) }
	CERT_REGEX = re.compile("^-----BEGIN CERTIFICATE-----.+?-----END CERTIFICATE-----$", flags = re.MULTILINE | re.DOTALL)

	@classmethod
	def create_csr(cls, hostnames, csr_filename, key_filename):
		with tempfile.NamedTemporaryFile(prefix = "openssl_config_", suffix = ".conf", mode = "w") as f:
			config = textwrap.dedent("""\
			[req]
			prompt = no
			req_extensions = req_ext
			distinguished_name = dn

			[dn]
			CN = %s

			[req_ext]
			subjectAltName = @alt_names

			[alt_names]
			""" % (hostnames[0]))
			for (nid, name) in enumerate(hostnames):
				config += "DNS.%d = %s\n" % (nid, name)
			print(config, file = f)
			f.flush()

			cmd = [ "openssl", "req", "-new", "-sha256", "-out", csr_filename, "-config", f.name, "-key", key_filename ]
			subprocess.check_call(cmd)

	@classmethod
	def crt_expires_in_less_than_days(cls, crt_filename, days):
		not_after = subprocess.check_output([ "openssl", "x509", "-in", crt_filename, "-noout", "-enddate" ])
		not_after = not_after.decode("ascii").rstrip("\r\n")
		match = cls.NOT_AFTER_REGEX.fullmatch(not_after)
		match = match.groupdict()
		match["month"] = cls.MONTHS[match["month"].lower()]
		expiry_date_utc = datetime.datetime(int(match["year"]), match["month"], int(match["day"]), int(match["hour"]), int(match["minute"]), int(match["second"]))
		now_utc = datetime.datetime.utcnow()
		remaining_days_valid = (expiry_date_utc - now_utc).total_seconds() / 86400
		return remaining_days_valid < days

	@classmethod
	def _rawtext_get_dnsnames(cls, raw_text):
		text = raw_text.decode()
		match = cls.HOSTNAME_REGEX.search(text)
		names = match["names"].strip()
		split_names = cls.DNSNAME_SPLITTER.split(names)
		dns_names = set()
		for name in split_names:
			if name.startswith("DNS:"):
				dns_names.add(name[4:])
		return dns_names

	@classmethod
	def csr_get_hostnames(cls, csr_filename):
		csr_raw_text = subprocess.check_output([ "openssl", "req", "-text", "-noout", "-in", csr_filename ])
		return cls._rawtext_get_dnsnames(csr_raw_text)

	@classmethod
	def crt_get_hostnames(cls, csr_filename):
		crt_raw_text = subprocess.check_output([ "openssl", "x509", "-text", "-noout", "-in", csr_filename ])
		return cls._rawtext_get_dnsnames(crt_raw_text)

	@classmethod
	def split_certificates(cls, crt_data):
		text = crt_data.decode("ascii")
		certificates = [ ]
		for match in cls.CERT_REGEX.finditer(text):
			crt_text = match.group(0)
			crt = subprocess.check_output([ "openssl", "x509" ], input = crt_text.encode("ascii"))
			certificates.append(crt)
		return certificates

if __name__ == "__main__":
	print(CertTools.split_certificates(open("x", "rb").read()))
	#print(UITools.choice([ ("ecdsa", "ECDSA key"), ("rsa", "RSA key") ], "Please select cryptosystem: "))
