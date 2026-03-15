import math

from numpy import square
class Shape:
    def __init__(self, name):
        self.__name = name
    
    @property
    def name(self):
        return self.__name.upper()

    def area(self):
        return 0.0
    
    def __str__(self):
        return f'Shape: {self.name}, Area: {self.area():.2f}'
    
    def __lt__(self, other):
        if isinstance(other, Shape):
            if self.area() < other.area():
                return True
            else:
                return False
    
class Square(Shape):
    def __init__(self, name, side):
        super().__init__(name)
        self.__side = side 
    
    @property
    def side(self):
        return self.__side
    @side.setter
    def side(self, amount):
        if amount < 0:
            print("Invalid side")
        else:
            self.__side = amount
    def area(self):
        return self.__side ** 2
    @property
    def name(self):
        return super().name
    def __str__(self):
        return f"Square {self.name}: Side {self.__side}, Area {self.area():.2f}"
    def __lt__(self, other):
        return super().__lt__(other)
class Circle(Shape):
    def __init__(self, name, radius):
        super().__init__(name)
        self.__radius = radius
    @property
    def radius(self):
        return self.__radius
    @radius.setter
    def radius(self, amount):
        if amount < 0:
            print("Invalid radius")
        else:
            self.__radius = amount
    @property
    def radius(self):
        return self.__radius
    @property
    def name(self):
        return super().name
    def area(self):
        return math.pi * self.__radius ** 2
    
    def __str__(self):
        return f'Circle {self.name}: Radius {self.__radius:.2f}, Area {self.area():.2f}'
    
    def __lt__(self, other):
        return super().__lt__(other)
    

shapes = []
while True:
    type = input("Enter type (Square/Circle): ").strip()
    if type.lower() == 'done':
        break
    if type is not ('square, circle'):
        continue
    name = input("Enter name: ")
    size = (input("Enter size: ")).strip()
    try:
        float(size)
    except ValueError:
        print('Invalid Input')
        continue
    if size <= 0:
        print("Invalid size")
        continue
    if type == "square":
        shapes.append(Square(name, size))
    else:
        shapes.append(Circle(name, size))

        
print("-----Unsorted-----")
for i in shapes:
    print(i)
shapes.sort()
print("-----Sorted (by Area)-----")
for j in shapes:
    print (j)