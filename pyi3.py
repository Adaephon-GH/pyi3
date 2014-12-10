#!/usr/bin/env python3

__author__ = 'Adaephon'

import json
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
        msgType, data = self._receive()
        isEvent = msgType >> 31
        parsedData = json.loads(data.decode())
        response = {'Origin': 'Event' if isEvent else 'Reply',
                    'Type': eventTypes[msgType & 0x7f] if isEvent
                    else msgTypes[msgType],
                    'Payload': parsedData}
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


