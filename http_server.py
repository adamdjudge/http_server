#!/usr/bin/env python3

import argparse
import socket
import re
import datetime

page_header     = "HTTP/1.1 200 OK\x0d\x0aServer: dumb_python_script\x0d\x0aContent-Type: text/html; charset=UTF-8\x0d\x0aConnection: close\x0d\x0a\x0d\x0a"
image_header    = "HTTP/1.1 200 OK\x0d\x0aServer: dumb_python_script\x0d\x0aContent-Type: image/gif\x0d\x0aContent-Transfer-Encoding: binary\x0d\x0aConnection: close\x0d\x0a\x0d\x0a"
not_found       = "HTTP/1.1 404 Not Found\x0d\x0a\x0d\x0a"
request_timeout = "HTTP/1.1 408 Request Timeout\x0d\x0a\x0d\x0a"
teapot          = "HTTP/1.1 418 I'm a teapot\x0d\x0a\x0d\x0a"
bad_request     = "HTTP/1.1 500 Bad Request\x0d\x0a\x0d\x0a"
not_implemented = "HTTP/1.1 501 Not Implemented\x0d\x0a\x0d\x0a"

def handle_client(client, addr):
	try:
		req = client.recv(4096).decode('utf-8')
	except socket.timeout:
		print(f"{datetime.datetime.now()}: {addr[0]}: Connection timed out")
		client.send(bytes(request_timeout, 'utf-8'))
		client.close()
		return
	except Exception as e:
		print(f"{datetime.datetime.now()}: {addr[0]}: CONNECTION CLOSED DUE TO AN INTERNAL EXCEPTION:")
		print(str(e))
		client.send(bytes(bad_request, 'utf-8'))
		client.close()
		return

	full = req
	req = req.split('\n')[0].split()
	if len(req) < 3 or full[-4:] != '\x0d\x0a\x0d\x0a':
		print(f"{datetime.datetime.now()}: {addr[0]}: Bad header format")
		client.send(bytes(bad_request, 'utf-8'))
		client.close()
		return
	cmd = req[0]
	name = req[1]
	if name == '/':
		name = 'index.html'
	else:
		name = name[1:]

	if cmd in ['GET', 'HEAD']:
		print(f"{datetime.datetime.now()}: {addr[0]}: {cmd} {name}")
		try:
			ext = re.search(r"\.([a-z]+)($|\?)", name).group(1)
			if '../' in name or ext not in ['html', 'css', 'js', 'php', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'ico']:
				raise Exception()
			if ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'ico']:
				with open(name, 'rb') as file:
					response = bytes(image_header, 'utf-8')
					if cmd == 'GET':
						response += file.read()
			else:
				with open(name, 'r') as file:
					response = bytes(page_header, 'utf-8')
					if cmd == 'GET':
						response += bytes(file.read(), 'utf-8')
			client.send(response)
		except Exception:
			print(f"\t=> Error: 404 not found")
			client.send(bytes(not_found, 'utf-8'))

	elif cmd == 'BREW':
		print(f"{datetime.datetime.now()}: {addr[0]}: {cmd} {name}")
		print("\t=> Error: 418 I'm a teapot")
		client.send(bytes(teapot, 'utf-8'))

	elif cmd in ['POST', 'PUT', 'DELETE', 'TRACE', 'OPTIONS', 'CONNECT', 'PATCH']:
		print(f"{datetime.datetime.now()}: {addr[0]}: Showing full request:\n{full}")
		print("\t=> Error: 501 not implemented\n")
		client.send(bytes(not_implemented, 'utf-8'))

	else:
		print(f"{datetime.datetime.now()}: {addr[0]}: Showing full request:\n{full}")
		print("\t=> Error: 500 bad request\n")
		client.send(bytes(bad_request, 'utf-8'))

	client.close()


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description = "Homebrew Python HTTP server.")
	parser.add_argument('address', help = "local IPv4 address to bind to")
	parser.add_argument('-p', '--port', type = int, default = 80, help = 'port to bind to, defaults to 80')
	args = parser.parse_args()

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((args.address, args.port))
	s.listen(16)
	print(f"{datetime.datetime.now()}: Started server at {args.address}:{str(args.port)}")

	while True:
		client, addr = s.accept()
		client.settimeout(10)
		try:
			handle_client(client, addr)
		except Exception:
			client.close()
