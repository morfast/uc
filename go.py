#!/usr/bin/python -u

import sys
import socket
import struct

Max_Label = 0

class FamilyLabel:
    Max_Label = 0
    def __init__(self):
        FamilyLabel.Max_Label += 1
        self._value_ = FamilyLabel.Max_Label
    def value(self):
        return self._value_

class MatrixElement:
    def __init__(self, id, ip, time):
        self.id = id
        self.ip = ip
        self.time = time
        self.label = None
        self.delete = False

def convert_time(timestr):
    # 2016-10-11 09:11:13 -> 9*60+11
    x = timestr.split(':')
    h = x[0]
    m = x[1]
    return int(h) * 60 + int(m)


def ip2int( ip ):
    return struct.unpack('!L',socket.inet_aton(ip))[0]
 
def int2ip( ip ):
    return socket.inet_ntoa(struct.pack('I',socket.htonl(ip)))

def construct_matrix(filename):
    res = []
    for line in open(sys.argv[1]):
        spline = line.strip().split()
        time = convert_time(spline[2])
        qq = spline[3]
        ipport = spline[4]
        ip, port = ipport.split(":")

        res.append(MatrixElement(int(qq), ip2int(ip), time))

    return res

def print_matrix(matrix):
    for elem in matrix:
        if elem.label:
            print elem.id, elem.ip, elem.time, elem.label.value(), elem.delete

def mark_according_to_id(matrix):
    global Max_Label
    # sort with id
    matrix.sort(key = lambda x:(x.id, x.ip, x.time))
    i = 0
    length = len(matrix)
    while i < length - 1: 
        # same id
        if matrix[i].id == matrix[i+1].id:
            label = FamilyLabel()
            matrix[i].label = label
            ipstate = 0 # 0: starting mark 1: in marking
            while matrix[i].id == matrix[i+1].id:

                # access from the same ip: leave the head and tail only
                if ipstate == 0:
                    if matrix[i].ip == matrix[i+1].ip:
                        matrix[i+1].delete = True
                        ipstate = 1
                    else:
                        pass
                elif ipstate == 1:
                    if matrix[i].ip == matrix[i+1].ip:
                        matrix[i+1].delete = True
                    else:
                        ipstate = 0
                        matrix[i].delete = False

                matrix[i+1].label = label
                i += 1
            matrix[i].delete = False
        i += 1


def mark_according_to_ip(matrix):
    global Max_Label
    
    matrix.sort(key = lambda x:(x.ip, x.time))
    for i,elem in enumerate(matrix[:-1]):
        if matrix[i+1].id == matrix[i].id:
            matrix[i].label = Max_Label
            matrix[i+1].label = Max_Label
        else:
            Max_Label += 1
    print_matrix(matrix)



#a = FamilyLabel()
#b = FamilyLabel()
#print a.get_value()
#print b.get_value()
#sys.exit(0)


m = construct_matrix(sys.argv[1])
mark_according_to_id(m)
print_matrix(m)
#mark_according_to_ip(m)


