import math

################################################################################
###		Point (x,y) operations
################################################################################
class Point:
	def __init__(self, x, y=None):
		if not y==None:
			self.x, self.y = float(x), float(y)
		else:
			self.x, self.y = float(x[0]), float(x[1])
	def __add__(self, other): return Point(self.x + other.x, self.y + other.y)
	def __sub__(self, other): return Point(self.x - other.x, self.y - other.y)
	def __neg__(self): return Point(-self.x, -self.y)
	def __mul__(self, other):
		if isinstance(other, Point):
			return self.x * other.x + self.y * other.y
		return Point(self.x * other, self.y * other)
	__rmul__ = __mul__
	def __div__(self, other): return Point(self.x / other, self.y / other)
	def mag(self): return math.hypot(self.x, self.y)
	def unit(self):
		h = self.mag()
		if h: return self / h
		else: return Point(0,0)
	def dot(self, other): return self.x * other.x + self.y * other.y
	def rot(self, theta):
		c = math.cos(theta)
		s = math.sin(theta)
		return Point(self.x * c - self.y * s,  self.x * s + self.y * c)
	def angle(self): return math.atan2(self.y, self.x)
	def __repr__(self): return '%f,%f' % (self.x, self.y)
	def pr(self): return "%.2f,%.2f" % (self.x, self.y)
	def to_list(self): return [self.x, self.y]	
	def ccw(self): return Point(-self.y,self.x)
	def l2(self): return self.x*self.x + self.y*self.y

