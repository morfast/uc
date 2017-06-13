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
    def set_value(self, v):
        self._value_ = v

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
        try:
            qq = int(qq)
        except ValueError,e:
            continue
        ipport = spline[4]
        ip, port = ipport.split(":")

        res.append(MatrixElement(qq, ip2int(ip), time))

    return res

def print_matrix(matrix):
    for elem in matrix:
        if elem.label:
            print elem.id, int2ip(elem.ip), elem.time, elem.label.value(), elem.delete
        else:
            print elem.id, int2ip(elem.ip), elem.time, elem.label, elem.delete

def mark_according_to_id(matrix):
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
            while (i < length - 1) and (matrix[i].id == matrix[i+1].id):
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

def delete_redundant(matrix):
    return [e for e in matrix if e.delete == False]

def mark_same(matrix, start, length):
    # how many labels?
    labels = [elem.label for elem in matrix[start:start+length] if elem.label != None]
    labels_set = set(labels)

    for l in labels_set:
        if labels.count(l) <= 1:
            continue
        # replace labels between two l
        i = start 
        # search the first l
        while i < start + length:
            if matrix[i].label and matrix[i].label.value() == l.value():
                break
            i += 1
        # begin mark
        i += 1
        while i < start + length:
            if matrix[i].label and matrix[i].label.value() != l.value():
                    matrix[i].label.set_value(l.value())
            else:
                break
            i += 1

def guess_family(matrix, start, length):
    """ guess family label according to time info """
    time_threshold = 60

    labels = [elem.label for elem in matrix[start:start+length] if elem.label != None]
    n_marked = len(set(labels))
    labels = [elem.label for elem in matrix[start:start+length] if elem.label == None]
    n_none = len(set(labels))

    if length == 1 and matrix[start].label == None:
        newlabel = FamilyLabel()
        matrix[start].label = newlabel
        return 1, 0
    elif length == 1 and matrix[start].label:
        return 0, 1

    i = start
    while i < start + length:
        if matrix[i].label == None:
            # look backward
            if i-1 >= start:
                if matrix[i].time - matrix[i-1].time < time_threshold:
                    matrix[i].label = matrix[i-1].label
            # look foreward
            if matrix[i].label == None and i+1 < start + length:
                if matrix[i+1].time - matrix[i].time < time_threshold:
                    if matrix[i+1].label != None:
                        matrix[i].label = matrix[i+1].label
                    else:
                        newlabel = FamilyLabel()
                        matrix[i].label = newlabel
                        #matrix[i+1].label = newlabel
                else:
                    newlabel = FamilyLabel()
                    matrix[i].label = newlabel
        i += 1

    i -= 1
    if matrix[i].label == None:
        newlabel = FamilyLabel()
        matrix[i].label = newlabel

    return n_none, n_marked

def mark_according_to_ip(matrix):
    global Max_Label
    
    matrix.sort(key = lambda x:(x.ip, x.time))
    #print_matrix(matrix)
    i = 0
    length = len(matrix)
    same_len = 1
    same_start = 0
    n_none = 0
    n_marked = 0
    while i < length - 1: 
        if matrix[i].ip == matrix[i+1].ip:
            same_len += 1
        else:
            if same_len >= 3:
                # mark elements between two same id
                mark_same(matrix, same_start, same_len)
            n,m = guess_family(matrix, same_start, same_len)
            n_none += n
            n_marked += m
            same_len = 1
            same_start = i + 1
        i += 1

    if same_len >= 3:
        mark_same(matrix, same_start, same_len)
        n,m = guess_family(matrix, same_start, same_len)
        n_none += n
        n_marked += m

    if matrix[i].ip != matrix[i-1].ip:
        n,m = guess_family(matrix, i, 1)
        n_none += n
        n_marked += m

    return n_none, n_marked

def count_label(matrix):
    return len(set([e.label.value() for e in matrix]))

def count_ip(matrix):
    return len(set([e.ip for e in matrix]))

def count_id(matrix):
    return len(set([e.id for e in matrix]))

def count_none(matrix):
    return len(set([e for e in matrix if e.label == None]))


def test():
    label = FamilyLabel()
    a = MatrixElement(0,0,0)
    b = MatrixElement(0,0,0)
    c = MatrixElement(0,0,0)
    a.label = label
    b.label = label
    c.label = label

    print a.label.value()
    print b.label.value()
    print c.label.value()

    a.label.set_value(3)

    print a.label.value()
    print b.label.value()
    print c.label.value()

#a = FamilyLabel()
#b = FamilyLabel()
#c = a
#print len(set([a,b,c]))
##print a==b
##print a==c
##aa = [a,b,c]
##print aa.count(a)
###print a.get_value()
###print b.get_value()
#sys.exit(0)


sys.stderr.write("construct matrix\n")
m = construct_matrix(sys.argv[1])
sys.stderr.write("mark by id\n")
mark_according_to_id(m)
m = [e for e in m if e.delete == False]
sys.stderr.write("mark by ip\n\n")
n_none, n_marked = mark_according_to_ip(m)
#sys.stderr.write("number of none: %d\n" % n_none)
#sys.stderr.write("number of marked: %d\n" % n_marked)
sys.stderr.write("range: (%d, %d)\n" % (n_marked, n_marked + n_none))
#print_matrix(m)
sys.stderr.write("Number of IP: %d\n" % count_ip(m))
sys.stderr.write("Number of ID: %d\n" % count_id(m))
sys.stderr.write("Number of family: %d\n" % count_label(m))
