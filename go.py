#!/usr/bin/python -u

import sys
import socket
import struct

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
    def get_label_value(self):
        return self.label.value()
   

def convert_time(timestr):
    """ convert time string to number of seconds """
    # 09:11:13 -> 9*60*60 + 11*60 + 13
    h, m, s = timestr.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


def ip2int(ip):
    return struct.unpack('!L',socket.inet_aton(ip))[0]
 
def int2ip(ip):
    return socket.inet_ntoa(struct.pack('I',socket.htonl(ip)))

def construct_matrix(filename):
    res = []
    for line in open(filename):
        spline = line.strip().split()
        time = convert_time(spline[0])
        userid = spline[2]
        try:
            int(userid)
            userid = 'QQ' + userid
        except ValueError,e:
            if '=' not in userid:
                continue
        #ipport = spline[4]
        ip = spline[1]

        res.append(MatrixElement(userid, ip2int(ip), time))

    return res

def print_matrix(matrix):
    for elem in matrix:
        if elem.label:
            print elem.id, int2ip(elem.ip), elem.time, elem.get_label_value(), elem.delete
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
        # search the first l from the beginning
        while i < start + length:
            if matrix[i].label and matrix[i].get_label_value() == l.value():
                break
            i += 1
        # search the last l from the end
        j = start + length - 1
        while j > i:
            if matrix[j].label and matrix[j].get_label_value() == l.value():
                break
            j -= 1

        # begin mark
        i += 1
        while i < j:
            if matrix[i].label and matrix[i].get_label_value() != l.value():
                    matrix[i].label.set_value(l.value())
            elif matrix[i].label == None:
                    matrix[i].label = l
            i += 1

def mark_according_to_ip(matrix):
    matrix.sort(key = lambda x:(x.ip, x.time, x.id))
    i = 0
    length = len(matrix)
    same_len = 1
    same_start = 0
    while i < length - 1: 
        if matrix[i].ip == matrix[i+1].ip:
            same_len += 1
        else:
            if same_len >= 3:
                # mark elements between two same id
                mark_same(matrix, same_start, same_len)
            same_len = 1
            same_start = i + 1
        i += 1

    if same_len >= 3:
        mark_same(matrix, same_start, same_len)

def group_by_ip(matrix):
    """ group ID by ip (they are possible in the same family) """
    res = []
    # assuming already sorted by IP
    i = 0
    length = len(matrix)
    same_len = 1
    same_start = 0
    while i < length - 1: 
        if matrix[i].ip == matrix[i+1].ip:
            same_len += 1
        else:
            if same_len >= 2:
                # mark elements between two same id
                rset = set([elem.id for elem in matrix[same_start:same_start+same_len]])
                if len(rset) >= 2:
                    res.append(rset)
            same_len = 1
            same_start = i + 1
        i += 1

    if same_len >= 2:
        rset = set([elem.id for elem in matrix[same_start:same_start+same_len]])
        if len(rset) >= 2:
            res.append(rset)

    return res

def find_family_in_possbile_groups(all_possible_family):
    res = []
    print "%d group pair to search" % (len(all_possible_family)/2)
    for fs1, fs2 in zip(all_possible_family[::2], all_possible_family[1::2]):
        print "search in possible groups: %d %d" % (len(fs1), len(fs2))
        for i,f1 in enumerate(fs1):
            if i % 5000 == 0:
                print "%3.1f%% complete" % (float(i)/len(fs1) * 100)
            for f2 in fs2:
                commonid = f1.intersection(f2)
                if len(commonid) > 1:
                    res.append(commonid)
                    break
    return res


def group_by_label(matrix):
    labels = [(x.get_label_value(), x.id) for x in matrix if x.label]
    labels.sort(key=lambda x:x[0])

    if not labels:
        return []

    i = 0
    length = len(labels)
    g = [labels[0][1],]
    res = []
    while i < length - 1: 
        if labels[i][0] == labels[i+1][0]:
            g.append(labels[i+1][1])
        else:
            if len(set(g)) > 1:
                res.append(set(g))
            g = [labels[i+1][1]]
        i += 1

    if len(set(g)) > 1:
        res.append(set(g))

    return res

def merge_one_set(a):
    """ [ [1,2,3], [1,2,3,4], ] => [ [1,2,3,4], ] """

    merge_to_index = 0
    determined = []
    while merge_to_index < len(a) - 1:
        compare_index = merge_to_index + 1
        while compare_index < len(a):
            intersection = a[merge_to_index].intersection(a[compare_index])
            if intersection:
                a[merge_to_index] = a[merge_to_index].union(a[compare_index])
                a.pop(compare_index)
                compare_index = merge_to_index + 1
                if len(intersection) > 1:
                    determined = merge_two_sets(determined, [intersection,])
            else:
                compare_index += 1
        merge_to_index += 1
                
    return determined
    
def merge_two_sets(a, b):
    res = []
    for i,ea in enumerate(a):
        for j, eb in enumerate(b):
            if isinstance(eb, set) and ea.intersection(eb):
                # have common with each other, merge them
                res.append(ea.union(eb))
                a[i] = 0
                b[j] = 0
                break
        if a[i] != 0: # similar set not found in b
            res.append(a[i])

    for eb in b:
        if isinstance(eb, set):
            res.append(eb)
                
    return res

def exist_in_sets(id, sets):
    for i,s in enumerate(sets):
        if id in s:
            return i
    return -1

def mark_with_dict(matrix, result_dict):
    for elem in matrix:
        try: 
            newlabelvalue = result_dict[elem.id]
            if elem.label == None:
                elem.label = FamilyLabel()
            elem.label.set_value(newlabelvalue)
        except KeyError:
            elem.label = None

def count_user_number_with_dict(matrix, result_dict):
    mark_with_dict(matrix, result_dict)
    mark_according_to_ip(matrix)
    determined_labels = []
    orphan_ids = []
    for elem in matrix:
        if elem.label == None:
            orphan_ids.append(elem.id)
        else:
            determined_labels.append(elem.get_label_value())
    return len(set(determined_labels)), len(set(orphan_ids))

def write_sets(sets, filename):           
    f = open(filename, "w")               
                                          
    for s in sets:                        
        for elem in s:                    
            f.write("%s " % (elem))       
        f.write("\n")                     
                                          
def main():
    if len(sys.argv) < 2:
        sys.exit(0)

    result_set = []
    result_dict = {}
    all_matrix = []
    all_possible_family = []
    for filename in sys.argv[1:]:
        sys.stderr.write("processing file %s\n" % (filename))
        sys.stderr.write("constructing accsess matrix\n")
        m = construct_matrix(filename)

        # mark labels by ID
        sys.stderr.write("marking by id\n")
        mark_according_to_id(m)
        m = [e for e in m if e.delete == False]

        # mark labels by IP
        sys.stderr.write("marking by ip\n")
        mark_according_to_ip(m)
        #print_matrix(m)

        # print_matrix(m)
        r = group_by_label(m)
        print "number of determined family for this file: %d" % (len(r))

        # group IDs which use the same IP, these IDs are possible in the same family
        possible_family = group_by_ip(m)
        print "merging possible_family"
        determined = merge_one_set(possible_family)
        all_possible_family.append(possible_family)

        result_set = merge_two_sets(result_set, r)
        result_set = merge_two_sets(result_set, determined)
        # print result_set
        print "number of determined family in total: %d" % (len(result_set))
        print
        all_matrix.append((filename, m, len(r)))

    # determine in the possible set
    # print "all_possible_family", all_possible_family
    r = find_family_in_possbile_groups(all_possible_family)
    print "number of determined family in the possible set: %d" % (len(r))
    result_set = merge_two_sets(result_set, r)
    print "number of determined family finally: %d" % (len(result_set))
    
    # convert sets to dict
    print "convert sets to dict...",
    for i,s in enumerate(result_set):
        for elem in s:
            result_dict[elem] = i
    print "Done"
    
    print 
    print "================== RESULT ========================="
    for filename, m, n_sets in all_matrix:
        n_family, n_orphan = count_user_number_with_dict(m, result_dict)
        print "RESULT for %s: %d %d %d" % (filename, n_family, n_orphan, n_family+n_orphan)
    print "==================================================="
    
    sys.exit(0)

main()

