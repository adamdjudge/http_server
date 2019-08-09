#!/usr/bin/env python3

import argparse
import socket
import re
import datetime

class LogFile:
	def __init__(self, msg):
		name = f"{str(datetime.datetime.now()).replace(' ', '_')}.log"
		self.file = open(name, 'w+')
		out = f"{datetime.datetime.now()}: {msg}"
		self.file.write(out + '\n')
		self.file.flush()
		print(out)
	def log(self, addr, msg):
		out = f"{datetime.datetime.now()}: {addr[0]}: {msg}"
		self.file.write(out + '\n')
		self.file.flush()
		print(out)
	def log_req(self, addr, req):
		time = datetime.datetime.now()
		self.file.write(f"{time}: {addr[0]}: New request:\n{req}")
		self.file.flush()
		tokens = req.split()
		try:
			cmd = tokens[0]
			name = 'index.html' if tokens[1] == '/' else tokens[1][1:]
			print(f"{time}: {addr[0]}: {cmd} {name}")
		except:
			print(f"{time}: {addr[0]}: Invalid header")
	def log_err(self, msg):
		out = f"\t=> Error: {msg}"
		self.file.write(out + '\n\n')
		self.file.flush()
		print(out)
	def __del__(self):
		self.file.close()

PAGE_HEADER     = "HTTP/1.1 200 OK\x0d\x0aServer: dumb_python_script\x0d\x0aContent-Type: text/html; charset=UTF-8\x0d\x0aConnection: close\x0d\x0a\x0d\x0a"
IMAGE_HEADER    = "HTTP/1.1 200 OK\x0d\x0aServer: dumb_python_script\x0d\x0aContent-Type: image/gif\x0d\x0aContent-Transfer-Encoding: binary\x0d\x0aConnection: close\x0d\x0a\x0d\x0a"
NOT_FOUND       = "HTTP/1.1 404 Not Found\x0d\x0a\x0d\x0a"
REQUEST_TIMEOUT = "HTTP/1.1 408 Request Timeout\x0d\x0a\x0d\x0a"
TEAPOT          = "HTTP/1.1 418 I'm a TEAPOT\x0d\x0a\x0d\x0a"
BAD_REQUEST     = "HTTP/1.1 500 Bad Request\x0d\x0a\x0d\x0a"
NOT_IMPLEMENTED = "HTTP/1.1 501 Not Implemented\x0d\x0a\x0d\x0a"

def handle_client(client, addr, logfile):
	try:
		req = client.recv(4096).decode('utf-8')
	except socket.timeout:
		logfile.log(addr, "Connection timed out")
		client.send(bytes(REQUEST_TIMEOUT, 'utf-8'))
		client.close()
		return
	except Exception as e:
		logfile.log(addr, f"CONNECTION CLOSED DUE TO INTERNAL EXCEPTION:\n\t=> {str(e)}")
		client.send(bytes(BAD_REQUEST, 'utf-8'))
		client.close()
		return

	logfile.log_req(addr, req)
	full = req
	req = req.split('\n')[0].split()
	if len(req) < 3 or '\x0d\x0a\x0d\x0a' not in full:
		logfile.log_err("500 bad request")
		client.send(bytes(BAD_REQUEST, 'utf-8'))
		client.close()
		return
	cmd = req[0]
	name = 'index.html' if req[1] == '/' else req[1][1:]

	if cmd in ['GET', 'HEAD']:
		try:
			ext = re.search(r"\.([a-z]+)($|\?)", name).group(1)
			if '../' in name or ext not in ['html', 'css', 'js', 'php', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'ico']:
				raise Exception()
			if ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'ico']:
				with open(name, 'rb') as file:
					response = bytes(IMAGE_HEADER, 'utf-8')
					if cmd == 'GET':
						response += file.read()
			else:
				with open(name, 'r') as file:
					response = bytes(PAGE_HEADER, 'utf-8')
					if cmd == 'GET':
						response += bytes(file.read(), 'utf-8')
			client.send(response)
		except Exception:
			logfile.log_err("404 not found")
			client.send(bytes(NOT_FOUND, 'utf-8'))

	elif cmd == 'BREW':
		logfile.log_err("418 I'm a teapot")
		client.send(bytes(TEAPOT, 'utf-8'))

	elif cmd in ['POST', 'PUT', 'DELETE', 'TRACE', 'OPTIONS', 'CONNECT', 'PATCH']:
		logfile.log_err("501 not implemented")
		client.send(bytes(NOT_IMPLEMENTED, 'utf-8'))

	else:
		logfile.log_err("500 bad request")
		client.send(bytes(BAD_REQUEST, 'utf-8'))

	client.close()


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description = "Homebrew Python HTTP server.")
	parser.add_argument('address', help = "local IPv4 address to bind to")
	parser.add_argument('-p', '--port', type = int, default = 80, help = 'port to bind to, defaults to 80')
	args = parser.parse_args()

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((args.address, args.port))
	s.listen(16)

	logfile = LogFile(f"Started server on {args.address}:{args.port}")

	while True:
		try:
			client, addr = s.accept()
			client.settimeout(10)
			handle_client(client, addr, logfile)
		except KeyboardInterrupt:
			exit(0)
		except Exception:
			client.close()
