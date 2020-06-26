# leclient
leclient is yet another Let's Encrypt client. It runs completely with user
privileges and has no need to bind to port 80. Instead, it requires you to
point your webserver's port 80 to a common directory that is going to be used.

## License
leclient is GNU GPL-3. However, it relies on
[acme_tiny](https://github.com/diafygi/acme-tiny) which itself is under the MIT
license. For convenience, the acme_tiny executable is included.
