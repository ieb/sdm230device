print('Loading mock serial')
import logging
log = logging.getLogger(__name__)

class Serial:

	def __init__(self, *args, **kwargs) -> None:
		log.info(f' Serial {args} {kwargs}')
		self.data = []
		self._lastWrite = []
		pass

	def setbuffer(self, data):
		log.info(f'buffer {data}')
		self.data = data

	def read(self, size):
		log.info(f'<serial {self.data}')
		return self.data

	def write(self, data):
		self._lastWrite = data
		log.info(f'serial> {data}')

	@property
	def lastWrite(self):
		return self._lastWrite

	@property
	def in_waiting(self):
		return len(self.data)
