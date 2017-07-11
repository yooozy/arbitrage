from compare import compare_order_books
from time import strftime, sleep


def loop():
    while True:
        compare_order_books()
        sleep(30)


if __name__ == "__main__":
    loop()
