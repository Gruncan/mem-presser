from datetime import datetime

import matplotlib.pyplot as plt
import sys
import os

import json


def generate_plot(x, y):

    plt.figure()

    plt.plot(x, y, label="Memory Usage vs Time", color="blue", marker="o", linestyle="-")

    plt.title("Memory Usage")
    plt.xlabel("Time")
    plt.ylabel("Memory Used (KB)")

    plt.legend()

    plt.show()



def main():
    args = sys.argv[1:]
    if len(args) != 1:
        print("Unsure how to parse!", file=sys.stderr)
        return

    filename = args[0]

    x = []
    y = []

    with open(filename, "r") as f:
        lines = f.readlines()
        for line in lines:
            d = json.loads(line)
            key = list(d.keys())[0]
            values = d[key]
            x.append(datetime.strptime(key, '%Y-%m-%d %H:%M:%S.%f'))
            y.append(int(values["total"]) - int(values["free"]))


    generate_plot(x, y)




if __name__ == '__main__':
    main()