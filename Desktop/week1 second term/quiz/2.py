class Product:
    def __init__(self, name: str, price: float, stock: int):
        self._name = name
        self._price = price
        self.__stock = stock

    def get_stock(self) -> int:
        return self.__stock
    
    def __str__(self):
        return f"Product: {self._name} - ${self._price:.1f} (Qty: {self.__stock})"
    
class Electronics(Product):
    def __init__(self, name: str, price: float, stock: int, warranty: int):
        super().__init__(name, price, stock)
        self.__warranty = warranty

    def __str__(self):
        return f"Electronics: {self._name} - ${self._price:.1f} (Qty: {self.get_stock()}) / {self.__warranty}mo Warranty"
    
class Clothing(Product):
    def __init__(self, name: str, price: float, stock: int, material: str):
        super().__init__(name, price, stock)
        self.__material = material

    def __str__(self):
        return f"Clothing: {self._name} - ${self._price:.1f} (Qty: {self.get_stock()}) / {self.__material}"

inventory = []
while True:
    command = input("Command: ")
    if command == "DONE":
        break

    elif command == "ADD":
        type = input("Type (Elec/Cloth): ")
        name = input("Name: ")
        price = float(input("Price: "))
        stock = int(input("Stock: "))
        if type == "elec":
            warranty = int(input("Warranty: "))
            elec = Electronics(name, price, stock, warranty)
            inventory.append(elec)

        elif type == "cloth":
            material = input("Material: ")
            cloth = Clothing(name, price, stock, material)
            inventory.append(cloth)

    elif command == "CLEAR":
        stock_thr = int(input("Stock Threshold: "))
        for i in inventory[::-1]:
            if i.get_stock() < stock_thr:
                inventory.remove(i)
        print("Removed low stock items")
 
print("-----Inventory Report-----")
if len(inventory) == 0:
    print("Store is empty")

else:
    for i in inventory:
        print (i)