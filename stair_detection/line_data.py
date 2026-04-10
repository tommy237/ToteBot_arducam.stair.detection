from dataclasses import dataclass
import numpy as np

@dataclass
class Point:
    x:int|float
    y:int|float

    def __init__(self,x:int|float,y:int|float):
        self.x=x
        self.y=y

    def __neg__(self):
        return Point(x=-self.x,
                     y=-self.y)

    def __add__(self,other):
        return Point(x=self.x-other.x,
                     y=self.y-other.y)

    def __sub__(self,other):
        return self+(-other)
    
    def __floordiv__(self,other):
        if isinstance(other,int|float):
            return Point(x=self.x//other,
                         y=self.y//other)
        
    def __lt__(self,other):
        return self.y<other.y if self.x==other.x else self.x<other.x
        
    def toTuple(self)->tuple[int|float,int|float]:
        return (self.x,self.y)


class Line:
    def __init__(self,
                 pt1:Point,
                 pt2:Point):
        self.Point1:Point=pt1
        self.Point2:Point=pt2
        self.__Midpoint:Point=(pt2-pt1)//2
        self.__Length:int|float=np.sqrt((pt2.x-pt1.x**2)+((pt2.y-pt1.y)**2))

    def getMidpoint(self):
        return self.__Midpoint
    
    def getLength(self):
        return self.__Length

    
