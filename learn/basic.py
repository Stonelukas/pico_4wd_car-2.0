a = 4
b = 2
c = 23


def foobar(num):
    foo = num % 3 == 0
    bar = num % 5 == 0
    if foo and bar:
        print(f"foobar. Mit Zahl {num}")
    if foo:
        print(f"Foo. Mit Zahl {num}")
    elif bar:
        print(f"Bar. Mit Zahl {num}")
    else: 
        print(f"Zahl {num} ist nicht foo oder bar")

num = 0

# while num < 51:
#     foobar(num)

#     num += 1
    
number = 3.555555

print(f"{42:#X}")
