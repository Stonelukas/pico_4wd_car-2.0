class Hund():
    def __init__(self, name, art):
        self.name = name

    def bellen(self):
        print(self.name)

bello = Hund("bello", "Hund")
bella = Hund("bella", "Katze")

bello.bellen()
