import socket
import selectors
import types
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

df = pd.read_csv('domaindata.csv')

tr1 = DecisionTreeClassifier()
tr2 = DecisionTreeClassifier()

tr1.fit(df[['hum']], df[['control_sprinkler']])
tr2.fit(df[['temp']], df[['ac_control']])

sel = selectors.DefaultSelector()


def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            x = str(recv_data)
            x = x.split(',')
            print(x)
            s = str(tr1.predict(float(x[0][3:]))) + ", " + str(tr2.predict(float(x[1][:-2])))
            print(s)
            recv_data = bytes(s, 'utf-8')
            data.outb += recv_data
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print("echoing", repr(data.outb), "to", data.addr)
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]


host, port = ('192.168.0.104', 4321)
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print("listening on", (host, port))
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask)
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()