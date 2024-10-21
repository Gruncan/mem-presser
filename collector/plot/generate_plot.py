from datetime import datetime
import sys
import json
import matplotlib.pyplot as plt
import mplcursors



def generate_plot(time, *stats):
    plt.figure()

    lines = []

    for name, stat in stats:
        line, = plt.plot(time, stat, label=name)
        lines.append(line)

    plt.title("Memory Usage")
    plt.xlabel("Time")
    plt.ylabel("Memory Used (KB)")

    plt.legend()

    cursor = mplcursors.cursor(lines, hover=True, annotation_kwargs={'arrowprops': None})

    @cursor.connect("add")
    def on_click(sel):
        for l in lines:
            l.set_linewidth(1)
            l.set_alpha(0.7)
            l.set_markeredgewidth(1)

        selected_line = sel.artist
        selected_line.set_linewidth(3)
        selected_line.set_alpha(1.0)
        selected_line.set_markeredgewidth(3)

        plt.gcf().canvas.draw()

    @cursor.connect("add")
    def on_hover(sel):
        x, y = sel.target

        sel.annotation.set_text(f'{sel.artist.get_label()}: {y:.2f}')

        bbox = sel.annotation.get_bbox_patch()
        if bbox is not None:
            bbox.set(fc="white", alpha=0.6)

    plt.show()





def main():
    args = sys.argv[1:]
    if len(args) != 1:
        print("Unsure how to parse!", file=sys.stderr)
        return

    filename = args[0]

    x = []
    sk = 'Memory Used'
    stats = (sk, "buffers", "cached", "swapCache", "active", "inActive", "swapTotal", "swapFree", "zswap",
             'zswapped', 'dirty', 'writeback', 'pagesAnon', 'pageMapped', 'kernelStack', 'pageTables',
             'bounce', 'vmallocChunk', 'perCPU')

    stats = {key: list() for key in stats}


    with open(filename, "r") as f:
        lines = f.readlines()
        for line in lines:
            d = json.loads(line)
            key = list(d.keys())[0]
            values = d[key]
            x.append(datetime.strptime(key, '%Y-%m-%d %H:%M:%S.%f'))
            stats[sk].append((int(values["total"]) - int(values["free"])))
            for k in stats.keys():
                v = values.get(k, None)
                if v is not None:
                    stats[k].append(int(v))

    generate_plot(x, *tuple(stats.items()))




if __name__ == '__main__':
    main()