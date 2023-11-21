class LinePoint:
    def __init__(self, data):
        self.data = data
        self.next = None

class Queue:
    def __init__(self):
        self.head = None
        self.tail = None
    
    def enqueue(self, item):
        new_linepoint = LinePoint(item)
        if self.tail:
            self.tail.next = new_linepoint
        self.tail = new_linepoint
        if not self.head:
            self.head = new_linepoint
    
    def dequeue(self):
        removed_data = self.head.data
        self.head = self.head.next
        if not self.head:
            self.tail = None
        return removed_data
