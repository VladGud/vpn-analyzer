import queue

class ConcurrentQueue:
    def __init__(self):
        self.collection = queue.Queue()

    def append(self, x):
        self.collection.put(x)

    def pop(self):
        return self.collection.get()
    
    def __len__(self):
        return self.collection.qsize()
    
    def __str__(self):
        return f"{len(self)}"
    
    def print_collection(self):
        return self.collection.queue
    
    def empty(self):
        return self.collection.empty()
