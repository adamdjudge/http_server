#!/usr/bin/env python3

import socket
import re
import datetime

page_header = "HTTP/1.1 200 OK\x0d\x0aServer: dumb_python_script\x0d\x0aContent-Type: text/html; charset=UTF-8\x0d\x0aConnection: close\x0d\x0a\x0d\x0a"
image_header = "HTTP/1.1 200 OK\x0d\x0aServer: dumb_python_script\x0d\x0aContent-Type: image/gif\x0d\x0aContent-Transfer-Encoding: binary\x0d\x0a\x0d\x0a"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('10.0.0.91', 80))
s.listen(16)

while True:
	client, addr = s.accept()
	try:
		req = ''
		while not re.search(r"(\x0d\x0a\x0d\x0a|\x0a\x0a)$", req):
			req += client.recv(4096).decode('utf-8')
	except:
		client.close()
		print(f"{datetime.datetime.now()}: CLOSED CONNECTION FROM {addr[0]} DUE TO BUFFER OVERFLOW")
		continue

	if not req or req.split() == []:
		print(f"{datetime.datetime.now()}: {addr[0]}: Apparent connection and close without data")
		client.send(bytes("HTTP/1.1 500 Bad Request\x0d\x0a\x0d\x0a", 'utf-8'))
		client.close()
		continue

	full = req
	req = req.split('\n')[0].split()
	cmd = req[0]

	if cmd in ['GET', 'HEAD']:
		if len(req) < 3:
			print(f"{datetime.datetime.now()}: {addr[0]}: {cmd}: Incomplete header")
			print("\t=> Error: 500 bad request")
			client.send(bytes("HTTP/1.1 500 Bad Request\x0d\x0a\x0d\x0a", 'utf-8'))
			client.close()
			continue
		name = req[1]
		if name == '/':
			name = 'index.html'
		else:
			name = name[1:]
		print(f"{datetime.datetime.now()}: {addr[0]}: {cmd} {name}")
		try:
			ext = re.search(r"\.([a-z]+)($|\?)", name).group(1)
			if '..' in name or ext not in ['html', 'css', 'js', 'php', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'ico']:
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
		except Exception as e:
			print(f"\t=> Error: 404 not found")
			client.send(bytes("HTTP/1.1 404 Not Found\x0d\x0a\x0d\x0a", 'utf-8'))

	elif cmd == 'BREW':
		print(f"{datetime.datetime.now()}: {addr[0]}: {cmd}")
		print("\t=> Error: 418 I'm a teapot")
		client.send(bytes("HTTP/1.1 418 I'm a teapot\x0d\x0a\x0d\x0a", 'utf-8'))

	elif cmd == 'KILL':
		print(f"{datetime.datetime.now()}: {addr[0]}: {cmd}")
		print("**** Server shut down remotely ****")
		client.close()
		s.close()
		while True: pass

	elif cmd in ['POST', 'PUT', 'DELETE', 'TRACE', 'OPTIONS', 'CONNECT', 'PATCH']:
		print(f"{datetime.datetime.now()}: {addr[0]}: Showing full request:\n{full}")
		print("\t=> Error: 501 not implemented\n")
		client.send(bytes("HTTP/1.1 501 Not Implemented\x0d\x0a\x0d\x0a", 'utf-8'))

	else:
		print(f"{datetime.datetime.now()}: {addr[0]}: Showing full request:\n{full}")
		print("\t=> Error: 500 bad request\n")
		client.send(bytes("HTTP/1.1 500 Bad Request\x0d\x0a\x0d\x0a", 'utf-8'))

	client.close()