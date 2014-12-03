#!/usr/bin/env python3

import socket
import struct
import subprocess

msgTypes = [
    'COMMAND',
    'WORKSPACES',
    'SUBSCRIBE',
    'OUTPUTS',
    'TREE',
    'MARKS',
    'BAR_CONFIG',
    'VERSION',
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


def get_socketpath():
    sp = subprocess.check_output(['i3', '--get-socketpath']).rstrip()
    return sp


class Socket:
    magicString = b'i3-ipc'
    headerPacking = bytes('={}sLL'.format(len(magicString)), 'utf-8')
    headerLen = struct.calcsize(headerPacking)


    def __init__(self, socketPath):
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.settimeout(1)
        self.socket.connect(socketPath)

    def message(self, msgType, payload):
        len(payload)

    def _send(self, msgType, msg):
        message = (struct.pack(self.headerPacking, self.magicString,
                               len(msg), msgType) + msg)
        self.socket.sendall(message)

    def _receive(self):
        header = self.socket.recv(self.headerLen)
        _, msgSize, msgType = struct.unpack(self.headerPacking, header)
        data = self.socket.recv(msgSize)
        return msgType, data



