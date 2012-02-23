#!/usr/bin/python

from Queue import Queue
import dybase
import sys

MAX_INT = sys.maxint
MIN_INT = -MAX_INT - 1

#DEBUG = True
DEBUG = False

class Root(dybase.Persistent):
	def __init__(self):
		self.start = 0
		self.stop = 0

class SizeOfPersistentQueueExceeded(Exception):
	pass

class incomplete_persistent_deque:
	def __init__(self, filename):
		self._init_db(filename)

	def _init_db(self, filename):
		self.db = dybase.Storage()
		if self.db.open(filename):
			self.root = self.db.getRootObject()
			if self.root == None:
				self.root = Root()
				self.root.elements = self.db.createIntIndex() # createLongIndex can be used on 64 bits systems but it is strange to pass 2**32 elements in the queue
				self.root.pending_elements = self.db.createIntIndex()

				self.db.setRootObject(self.root)
				self.db.commit()
			else:
				if DEBUG:
					print "self.root already exists"

		if DEBUG:
			print "self.root.start =", self.root.start
			print "self.root.stop = ", self.root.stop

	def __len__(self):
		if self.root.stop >= self.root.start:
			return self.root.stop - self.root.start
		else:
			return (MAX_INT - self.root.start + 1) + (self.root.stop - MIN_INT)

	def append(self, item):
		# add element to index
		self.root.elements.insert(self.root.stop, item)
		self.root.stop += 1
		if self.root.stop > MAX_INT:
			# check also if stop touches start
			self.root.stop = MIN_INT

		if self.root.start == self.root.stop:
			raise SizeOfPersistentQueueExceeded

		# persist
		self.root.store()
		self.db.commit()

	def popleft(self):
		# don't check if empty, Queue class take charge of that
		# remove element from index
		item = self.root.elements.get(self.root.start)
		self.root.elements.remove(self.root.start)
		self.root.start += 1
		if self.root.start > MAX_INT:
			# check also if start touches stop
			self.root.start = MIN_INT 

		if self.root.start == self.root.stop: # if queue is empty resync start & stop to 0. It is for beautifier purposes can be removed.
			self.root.start = 0
			self.root.stop = 0

		# persist
		self.root.store()
		self.db.commit()

		return item



class PersistentQueue(Queue):
	def __init__(self, filename, maxsize = 0):
		self.filename = filename
		Queue.__init__(self, maxsize)

	def _init(self, maxsize):
		# original: self.queue = deque()

		# incomplete_persistent_deque:
		# - incomplete implementation but enough for Queue:
		# - implemented methods:
		# -- __len__
		# -- append
		# -- popleft
		#

		self.queue = incomplete_persistent_deque(self.filename)

	def connect(self): # to handle failovers
		pass

	def ack(self):
		pass

	#def ack(self, item):

class ElementTest:
	def __init__(self, value):
		self.value = value

	def __repr__(self):
		return self.value

	def __str__(self):
		return self.value

def test1():
	q = PersistentQueue("myqueue.dbs")
	if not q.empty(): # get pending items
		while not q.empty():
			e = q.get()
			print e

	for s in ['one', 'two', 'three']:
		q.put(ElementTest(s))
	

def main(): # run this script twice to see the persisted elements
	test1()


if __name__ == '__main__':
	main()
