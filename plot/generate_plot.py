from datetime import datetime

import matplotlib.pyplot as plt
import sys


def generate_plot(x, y):

    plt.figure()

    plt.plot(x, y, label="Memory Usage vs Time", color="blue", marker="o", linestyle="-")

    plt.title("Memory Usage")
    plt.xlabel("Time")
    plt.ylabel("Memory Used (Bytes)")

    plt.legend()

    plt.show()



def main():
    args = sys.argv[1:]
    if len(args) != 1:
        print("Unsure how to parse!", file=sys.stderr)
        return


    x = []
    y = []
    filename = args[0]
    with open(filename, "r") as f:
        lines = f.readlines()
        for line in lines:
            d = line.strip().split("-")
            date_str, mem = "-".join(d[:-1]), int(d[-1].strip())
            x.append(datetime.strptime(date_str.strip(), '%Y-%m-%d %H:%M:%S.%f'))
            y.append(mem)

    generate_plot(x, y)




if __name__ == '__main__':
    main()