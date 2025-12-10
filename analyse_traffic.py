#! /usr/bin/python3 -u

import re
from datetime import datetime
from statistics import mean, stdev

def decode_frame(frame):
    unit = int(frame[0:2], 16)
    function = int(frame[3:5], 16)
    reg = int(frame[6:8], 16)*256 + int(frame[9:11], 16) 
    count = int(frame[12:14], 16)*256 + int(frame[15:17], 16)
    return {
        'unit': unit,
        'function': function,
        'reg': reg,
        'regHex': f'{frame[6:8]}{frame[9:11]}',
        'count': count
    }



def main():
    requests = {}
    with open("SDM230RTUCapture.log") as file:
        isLeader = True
        lastRequest = None
        for item in file:
            if item.startswith('DATE='):
                #  DATE=2022-05-17T19:42:03.197;ERR=NO;FRAME=02-04-00-00-00-12-70-34;SLAVE=2

                match = re.match(r"DATE=(.*?);ERR=NO;FRAME=(.*?);SLAVE", item)
                if match != None:
                    date = datetime.fromisoformat(match.group(1))
                    frame = match.group(2)
                    if isLeader:
                        if not frame in requests:
                            requests[frame] = {
                                'req': [],
                                'res': []
                            }
                        requests[frame]['req'].append({
                                'date': date,
                                'frame': frame,
                        })
                        lastRequest = requests[frame];
                    else:
                        if lastRequest != None:
                            lastRequest['res'].append({
                                'date': date,
                                'frame': frame,
                            })
                    isLeader = not isLeader
    for k in requests:
        d1 = None
        period = []
        req = requests[k]['req']
        for i in range(len(req)):
            d2 = req[i]['date']
            if d1 != None:
                period.append((d2-d1).total_seconds())
            d1 = d2

        print(f'{decode_frame(k)} {mean(period)} {stdev(period)}')


if __name__ == "__main__":
    main()
