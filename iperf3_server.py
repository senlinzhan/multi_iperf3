#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import threading
import Queue
from subprocess import call, Popen, PIPE, STDOUT

START_PORT = 65000
HELP_MESSAGE = "Usage: python iperf3_server.py -K <concurrency num> <other iperf3 args, but no need to specify the port arg>"

concurrency_name = '-K'
concurrency_value = 1
iperf3_args = ''

output_queue = Queue.Queue()

def read_output(process):
    while True:
        line = process.stdout.readline().rstrip()
        if not line:
            break
        output_queue.put(line)
        time.sleep(1)

def parse_args():
    # global variables need be modified
    global concurrency_value
    global iperf3_args
    
    args = sys.argv[1:]    
    if '-K' not in args:
        print HELP_MESSAGE
        exit(1)
    
    concurrency_value_index = args.index(concurrency_name) + 1
    if concurrency_value_index >= len(args) or not args[concurrency_value_index].isdigit():
        print HELP_MESSAGE
        exit(1)

    concurrency_value = args[concurrency_value_index]
    args.remove(concurrency_name)
    args.remove(concurrency_value)
    concurrency_value = int(concurrency_value)

    args.append('--forceflush')
    iperf3_args = ' '.join(args)
        

if __name__ == "__main__":
    parse_args()

    process_list = []
    for i in range(0, concurrency_value):
        port = str(START_PORT + i)
        iperf3 = "/usr/local/bin/iperf3 {0} -p {1}".format(iperf3_args, port)        
        print "Run:", iperf3
        process = Popen(iperf3, stdout=PIPE, shell=True)
        process_list.append(process)
        thread = threading.Thread(target=read_output, args=[process])
        thread.start()

    process_num = len(process_list)        
    while True:
        lines = []
        for i in range(0, process_num):
            line = output_queue.get()
            lines.append(line)

        first_line = lines[0]
        if 'bits' in first_line:
            total_transfer = 0.0
            total_bitrate = 0.0
            total_jitter = 0.0
            total_lost = 0.0
            total_packets = 0.0
            
            first_line_tokens = first_line.split()
            first_line_transfer = '{0} {1}'.format(first_line_tokens[4],
                                                   first_line_tokens[5])
            first_line_bitrate = '{0} {1}'.format(first_line_tokens[6],
                                                  first_line_tokens[7])
            first_line_jitter = '{0} {1}'.format(first_line_tokens[8],
                                                 first_line_tokens[9])
            first_line_lost_total = first_line_tokens[10]
            first_line_lost_rate = first_line_tokens[11]
                
            for line in lines:
                if 'bits' in line:
                    tokens = line.split()
                    total_transfer += float(tokens[4])
                    total_bitrate += float(tokens[6])
                    total_jitter += float(tokens[8])                    
                    total_lost += int(tokens[10].split('/')[0]) 
                    total_packets += int(tokens[10].split('/')[1])
                else:
                    print("Debug: ", line)
            avg_jitter = total_jitter / len(lines)
            lost_rate = total_lost / total_packets
            
            line_total_transfer = '{0:.2f} {1}'.format(total_transfer, first_line_tokens[5])
            line_total_bitrate = '{0:.2f} {1}'.format(total_bitrate, first_line_tokens[7])
            line_avg_jitter = '{0:.3f} {1}'.format(avg_jitter, first_line_tokens[9])
            line_lost_total = '{0}/{1}'.format(total_lost, total_packets)
            line_lost_rate = '({0:.1f}%)'.format(lost_rate * 100)

            first_line = first_line.replace(
                first_line_transfer, line_total_transfer
            )
            first_line = first_line.replace(
                first_line_bitrate, line_total_bitrate
            )
            first_line = first_line.replace(
                first_line_jitter, line_avg_jitter
            )
            first_line = first_line.replace(
                first_line_lost_total, line_lost_total
            )
            first_line = first_line.replace(
                first_line_lost_rate, line_lost_rate
            )
            
            print(first_line)
        else:
            for line in set(lines):
                print(line)
