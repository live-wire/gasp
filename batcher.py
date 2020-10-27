# Batcher implementation for sending batches to influxDB
# Fast Writes
import threading
from threading import Thread
import time
import datetime

class Batcher:
	# maxSize is the batch size
    def __init__(self, maxSize = 200, flushEvery = 10, func = print):
        self.lock = threading.Lock()
        self.seq = []
        self.maxSize = maxSize
        self.flushEvery = flushEvery
        self.func = func
        self.lastFlush = datetime.datetime.timestamp(datetime.datetime.now())
        self.bgthread = Thread(target = self.backgroundFlusher)
        self.bgthread.start()
    
    def backgroundFlusher(self):
        def bgtask():
            diff = datetime.datetime.timestamp(datetime.datetime.now()) - self.lastFlush
            if diff > self.flushEvery and len(self.seq) > 0:
                self.flush()
        while True:
            bgtask()
            time.sleep(3)
    
    def flush(self):
        self.lock.acquire()
        if len(self.seq) > 0:
            self.func(self.seq)
        self.seq = []
        self.lastFlush = datetime.datetime.timestamp(datetime.datetime.now())
        self.lock.release()
        
    def send(self, item):
        self.lock.acquire()
        self.seq.append(item)
        self.lock.release()
        if len(self.seq) >= self.maxSize:
            self.flush()



if __name__ == "__main__":
    b = Batcher(100, 5, print)
    while True:
        b.send(input())
    b.bgthread.join()
