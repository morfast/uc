#!/usr/bin/python -u

import sys
import socket
import struct

def convert_time(timestr):
    # 2016-10-11 09:11:13 -> 9*60+11
    x = timestr.split(':')
    h = x[0]
    m = x[1]
    return int(h) * 60 + int(m)

def qq_per_ip():
    i = 0
    ip_qq = {}
    for line in open(sys.argv[1]):
        spline = line.strip().split()
        time = convert_time(spline[2])
        qq = spline[3]
        ipport = spline[4]
        ip, port = ipport.split(":")
    
        if ip in ip_qq.keys():
            ip_qq[ip].append([qq, time])
        else:
            ip_qq[ip] = [[qq, time]]
        i += 1
        if i % 1000 == 0:
            sys.stderr.write("%d\n" % i)
    
    for ip in ip_qq.keys():
        print ip, ip_qq[ip]
    
def ip_per_qq():
    i = 0
    ip_per_qq = {}
    for line in open(sys.argv[1]):
        spline = line.strip().split()
        time = convert_time(spline[2])
        qq = spline[3]
        ipport = spline[4]
        ip, port = ipport.split(":")
    
        if qq in ip_per_qq.keys():
            ip_per_qq[qq].add(ip)
        else:
            ip_per_qq[qq] = set()
            ip_per_qq[qq].add(ip)
        i += 1
        if i % 1000 == 0:
            sys.stderr.write("%d\n" % i)
    
    for qq in ip_per_qq.keys():
        print qq, ip_per_qq[qq]

def ip_to_number(ip):
    [int(i) for i in ip.split(".")]

def ip2int( ip ):
    return struct.unpack('!L',socket.inet_aton(ip))[0]
 
def int2ip( ip ):
    return socket.inet_ntoa(struct.pack('I',socket.htonl(ip)))

def get_ip_qq_range(filename):
    i = 0
    min_ip, max_ip = 10e20, 0
    min_qq, max_qq = 10e20, 0

    for line in open(filename):
        spline = line.strip().split()
        time = convert_time(spline[2])
        qq = spline[3]
        ipport = spline[4]
        ip, port = ipport.split(":")

        if int(qq) < min_qq:
            min_qq = int(qq)
        if int(qq) > max_qq:
            max_qq = int(qq)

        if ip2int(ip) < min_ip:
            min_ip = ip2int(ip)
        if ip2int(ip) > max_ip:
            max_ip = ip2int(ip)
    
        # print process
        i += 1
        if i % 1000 == 0:
            sys.stderr.write("%d\n" % i)

    return min_ip, max_ip, min_qq, max_qq
    

print get_ip_qq_range(sys.argv[1])


