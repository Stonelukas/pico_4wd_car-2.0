import random 


def random_line() -> str:
    colors = ["red", "blue", "yellow", "purple"]
    return random.choice(colors) # type: ignore


print(random_line())
