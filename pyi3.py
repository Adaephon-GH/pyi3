#!/usr/bin/env python3

__author__ = 'Adaephon'

import json
import queue
import socket
import struct
import subprocess

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
        parsedData = json.loads(data.decode())
        response = ('event' if isEvent else 'reply',
                    typeName,
                    parsedData)
        return response

    def __getattr__(self, attr):
        if attr in msgTypes:
            def func(msg=b''):
                self._send(msgTypesMap[attr], msg)
                return self._receive()
            return func
        else:
            raise AttributeError("'{}' object has no attribute '{}'".format(
                self.__class__.__name__, attr))


class EventHandler:
    def __init__(self, socket=None):
        self.socket = socket or Socket()
        self.events = [0] * len(eventTypes)
        self._eventqueue = queue.Queue()
        self._subscript_confirmation = queue.Queue()

    def run(self):
        self.isrunning = True

    def _read_socket(self):
        while True:
            dataType, name, payload = self.socket.receive()
            if dataType == 'event':
                self._eventqueue.put((name, payload))
            else if name == 'subcribe':
                self._subscript_confirmation.put(payload)
            else:
                raise UnexpectedDataError((dataType, name, payload))

    def _handle_events(self):
        while True:
            type_, payload = self._eventqueue.get()
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
