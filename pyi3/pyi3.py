#!/usr/bin/env python3
import threading
import json
import queue
import socket
import struct
import subprocess


__author__ = 'Adaephon'

msgTypes = [
    'command',
    'get_workspaces',
    'subscribe',
    'get_outputs',
    'get_tree',
    'get_marks',
    'get_bar_config',
    'get_version',
]
msgTypesMap = {msgTypes[i]: i for i in range(len(msgTypes))}

eventTypes = [
    'workspace',
    'output',
    'mode',
    'window',
    'barconfig_update',
]
eventTypesMap = {eventTypes[i]: i for i in range(len(eventTypes))}


class Socket:
    magicString = b'i3-ipc'
    headerPacking = bytes('={}sLL'.format(len(magicString)), 'utf-8')
    headerLen = struct.calcsize(headerPacking)

    @staticmethod
    def get_path():
        path = subprocess.check_output(['i3', '--get-socketpath']).rstrip()
        return path

    def __init__(self, socketPath=None):
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.settimeout(1)
        self.socket.connect(socketPath or self.get_path())

    def _send(self, msgType, msg=b''):
        message = (struct.pack(self.headerPacking, self.magicString,
                               len(msg), msgType) + msg)
        self.socket.sendall(message)

    def _receive(self):
        header = self.socket.recv(self.headerLen)
        _, msgSize, msgType = struct.unpack(self.headerPacking, header)
        data = self.socket.recv(msgSize)
        return msgType, data

    def receive(self):
        type_, data = self._receive()
        isEvent = type_ >> 31
        typeName = (eventTypes[type_ & 0x7f] if isEvent
                    else msgTypes[type_])
        # maybe use data.decode(errors=ignore) -> faulty jetbrains class name
        # see http://bugs.i3wm.org/report/ticket/1347
        parsedData = json.loads(data.decode())
        response = ('event' if isEvent else 'reply',
                    typeName,
                    parsedData)
        return response

    def __getattr__(self, attr):
        """
        Provides direct access to all i3 message types and commands

        :param attr: name of the message type or command
        :return: a function that sends the message and returns the response
        """
        print(type(attr))
        if attr in msgTypes:
            msgType = msgTypesMap[attr]
            prefix = b""
        else:
            msgType = msgTypesMap['command']
            prefix = attr.encode() + b" "

        def func(msg=b''):
            self._send(msgType, prefix + msg)
            return self.receive()
        return func


class I3Base:
    def __init__(self, i3socket=None):
        self.socket = i3socket or Socket()


class EventHandler(I3Base):
    def __init__(self, i3socket=None):
        super().__init__(i3socket)
        self.events = [0] * len(eventTypes)
        self._eventqueue = queue.Queue()
        self._subscript_confirmation = queue.Queue()
        self.isrunning = threading.Event()

    def run(self):
        self.isrunning.set()
        handler = threading.Thread(target=self._handle_events)
        reader = threading.Thread(target=self._read_socket)

    def _read_socket(self):
        while self.isrunning.is_set():
            dataType, name, payload = self.socket.receive()
            if dataType == 'event':
                self._eventqueue.put((name, payload))
            elif name == 'subcribe':
                self._subscript_confirmation.put(payload)
            else:
                raise UnexpectedDataError((dataType, name, payload))

    def _handle_events(self):
        while self.isrunning.is_set():
            type_, payload = self._eventqueue.get()
            if type_ == -1:
                break
            self._handle_event(type_, payload)

    def _handle_event(self, type_, payload):
        pass
        print(type_, payload)

    # TODO: something to pause handling (certain) events to avoid recursion
    def pause(self, events=None):
        pass


class Hook:
    def __init__(self, event, change=None, callback=None):
        pass


class UnexpectedDataError(Exception):
    pass


class Item:
    def __init__(self, items):
        self.__dict__.update(items)


class WorkspaceHandler(I3Base):
    def __init__(self, i3socket=None):
        super().__init__(i3socket)

    @property
    def _workspaces(self):
        _, _, wslist = self.socket.get_workspaces()
        return map(lambda ws: Item(ws), wslist)

    def workspaces(self, visible=None, focused=None, urgent=None,
                   num=None):
        pass
