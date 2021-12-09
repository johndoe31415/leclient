#	leclient - Let's encrypt frontend tooling and configuration
#	Copyright (C) 2020-2021 Johannes Bauer
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

import base64
import subprocess
import json
import requests
import pyasn1.codec.der.decoder

def _b64enc(data):
	return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")

def _b64enc_data(data):
	return _b64enc(json.dumps(data, sort_keys = True, separators = (",", ":")).encode("ascii"))

class JWK():
	def __init__(self, public_key, key_params):
		self._public_key = public_key
		self._key_params = key_params
		self._key_id = None

	@property
	def key_id(self):
		return self._key_id

	@key_id.setter
	def key_id(self, value):
		self._key_id = value

	@property
	def public_key(self):
		return self._public_key

	@property
	def signing_alg(self):
		return self._key_params["signing_alg"]

	def sign(self, sign_payload):
		signature = subprocess.check_output([ "openssl", "dgst", "-sha256", "-sign", self._key_params["privkey"] ], input = sign_payload)
		return signature

	@classmethod
	def _encode_int(cls, intval):
		return _b64enc(int.to_bytes(intval, length = (intval.bit_length() + 7) // 8, byteorder = "big"))

	@classmethod
	def load_rsa_privkey(cls, pem_keyfile):
		der_data = subprocess.check_output([ "openssl", "rsa", "-in", pem_keyfile, "-outform", "der" ], stderr = subprocess.DEVNULL)
		(asn1, tail) = pyasn1.codec.der.decoder.decode(der_data)
		(n, e) = (int(asn1[1]), int(asn1[2]))
		public_key = {
			"kty":	"RSA",
			"e":	cls._encode_int(e),
			"n":	cls._encode_int(n),
		}
		return cls(public_key = public_key, key_params = {
			"signing_alg":	"RS256",
			"privkey":		pem_keyfile,
		})

class ACMERequest():
	def __init__(self, directory_uri, account_key):
		self._sess = requests.Session()
		self._directory_uri = directory_uri
		self._account_key = account_key
		self._directory_info = None
		self._pending_request = None

	def _request(self, uri, data = None, expect_status_code = 200):
		headers = {
			"User-Agent":	"https://github.com/johndoe31415/leclient",
			"Accept":		"application/json",
		}
		if data is not None:
			headers["Content-Type"] = "application/jose+json"
			data = json.dumps(data, sort_keys = True, separators = (",", ":"))
		response = self._sess.request("GET" if (data is None) else "POST", uri, headers = headers, data = data)


		success = (response.status_code == expect_status_code) if isinstance(expect_status_code, int) else (response.status_code in expect_status_code)
		if not success:
			print("Error when performing request: %s" % (uri))
			print(data)
			print(response)
			print(response.content)
			print()
			raise Exception("Request failed: %s" % (uri))
		return response

	def _retrieve_directory_information(self):
		return self._request(uri = self._directory_uri).json()

	def _request_nonce(self):
		response = self._request(uri = self._directory_info["newNonce"], expect_status_code = 204)
		return response.headers["Replay-Nonce"]

	def _sign_message(self, for_uri, message, key):
		nonce = self._request_nonce()
		payload_b64 = _b64enc_data(message) if (message is not None) else ""
		protected = {
			"alg":		key.signing_alg,
			"nonce":	nonce,
			"url":		for_uri,
		}
		if key.key_id is None:
			protected["jwk"] = key.public_key
		else:
			protected["kid"] = key.key_id
		protected_b64 = _b64enc_data(protected)
		signature_bin = key.sign((protected_b64 + "." + payload_b64).encode("ascii"))
		return {
			"payload":		payload_b64,
			"protected":	protected_b64,
			"signature":	_b64enc(signature_bin),
		}

	def _register_account(self):
		message = { "termsOfServiceAgreed": True }
		signed_message = self._sign_message(self._directory_info["newAccount"], message, self._account_key)
		response = self._request(uri = self._directory_info["newAccount"], data = signed_message, expect_status_code = [ 200, 201 ])
		self._account_key.key_id = response.headers["Location"]

	def _new_order(self, dns_domainnames):
		message = { "identifiers": [ { "type": "dns", "value": dns_domainname } for dns_domainname in dns_domainnames ] }
		signed_message = self._sign_message(self._directory_info["newOrder"], message, self._account_key)
		response = self._request(uri = self._directory_info["newOrder"], data = signed_message, expect_status_code = 201)
		return response.json()

	def _handle_authorization(self, authorization_uri):
		signed_message = self._sign_message(authorization_uri, message = None, key = self._account_key)
		response = self._request(uri = authorization_uri, data = signed_message)
		print(response.json())

	def run(self):
		self._directory_info = self._retrieve_directory_information()
		self._register_account()
		pending_request = self._new_order([ "xfoobar.com" ])
		for authorization_uri in pending_request["authorizations"]:
			self._handle_authorization(authorization_uri)


if __name__ == "__main__":
	req = ACMERequest(directory_uri = "https://acme-staging-v02.api.letsencrypt.org/directory", account_key = JWK.load_rsa_privkey("accountkey"))
	req.run()
