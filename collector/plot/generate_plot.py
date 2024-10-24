from datetime import datetime
import sys
import json
from pathlib import Path


import numpy as np
from scipy.signal import find_peaks


import matplotlib.pyplot as plt
import mplcursors
import mpld3


class PlotBar:

    def __init__(self, value, name, color="black", linestyle="--", linewidth=2):
        self.x = value
        self.label = name
        self.color = color
        self.linestyle = linestyle
        self.linewidth = linewidth

    def get_data(self):
        return vars(self)


class MemoryPlotStat:

    def __init__(self, name, data, label=None):
        self.name = name
        self.data = data
        self.label = label if label else name




class MemoryPlotGenerator:

    def __init__(self, time, stats=None):
        if stats is None:
            stats = list()

        self.time = time
        self.title = "Memory Usage"
        self.x_label = "Time (Seconds)"
        self.y_label = "Memory Used (KB)"
        self.start_bar = None
        self.end_bar = None
        self.bars = []
        self.stats = stats


    def add_start_end_bars(self, start_bar, end_bar):
        self.start_bar = start_bar
        self.end_bar = end_bar

    def add_stat(self, stat):
        self.stats.append(stat)

    def add_stats(self, stats):
        self.stats += stats

    def __generic_plot(self):
        fig, ax = plt.subplots(figsize=(16, 9))

        lines = []

        for stat in self.stats:
            line, = ax.plot(self.time, stat.data, label=stat.label)
            lines.append(line)

        ax.set_title(self.title)
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        ax.legend()

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

            ax.figure.canvas.draw()

        @cursor.connect("add")
        def on_hover(sel):
            x, y = sel.target
            sel.annotation.set_text(f'{sel.artist.get_label()}: {y:.2f}')

            bbox = sel.annotation.get_bbox_patch()
            if bbox is not None:
                bbox.set(fc="white", alpha=0.6)


        return fig, ax


    def compile_to_html(self, filename):
        fig, _ = self.__generic_plot()
        mpld3.save_html(fig, filename)
        print(f"Plot saved as {filename}")

    def show_plot(self):
        fig, ax = self.__generic_plot()

        for i, bar in enumerate(self.bars):
            ax.axvline(**bar.get_data())

        if self.start_bar and self.end_bar:
            ax.axvline(**self.start_bar.get_data())
            ax.axvline(**self.end_bar.get_data())

        fig.show()
        plt.show()

    def save_plot(self, filename):
        fig, _ = self.__generic_plot()
        fig.savefig(filename)
        print(f"Plot saved as {filename}")




def find_next_intersection(stat1, stat2, start_index, after=True):
    diff = stat1 - stat2

    sign_diff = np.sign(diff)

    sign_changes = np.where(np.diff(sign_diff) != 0)[0] + 1

    if after:
        next_intersection = sign_changes[sign_changes > start_index]
    else:
        next_intersection = sign_changes[sign_changes < start_index]


    if len(next_intersection) > 0:
        return next_intersection[0]
    else:
        return None

def find_n_maxima(sk_der3, sk_der1, N):
    peaks, _ = find_peaks(sk_der3)

    valid_maxima = []

    for peak in peaks:
        if sk_der3[peak] > sk_der1[peak]:
            valid_maxima.append(peak)

        if len(valid_maxima) >= N:
            break

    return valid_maxima



N = 4

def main():
    args = sys.argv[1:]
    if len(args) < 1 or len(args) > 2:
        print("Unsure how to parse!", file=sys.stderr)
        return

    filename = args[0]

    second_filename = args[1] if len(args) == 2 else None


    times = []
    sk = 'Memory Used'
    stats = (sk, "buffers", "cached", "swapCache", "active", "inActive", "swapTotal", "swapFree", "zswap",
             'zswapped', 'dirty', 'writeback', 'pagesAnon', 'pageMapped', 'kernelStack', 'pageTables',
             'bounce', 'vmallocChunk', 'perCPU')

    data_dictionary = {key: list() for key in stats}


    with open(filename, "r") as f:
        lines = f.readlines()
        for line in lines:
            d = json.loads(line)
            key = list(d.keys())[0]
            values = d[key]
            times.append(datetime.strptime(key, '%Y-%m-%d %H:%M:%S.%f'))
            data_dictionary[sk].append((int(values["total"]) - int(values["free"])))
            for k in data_dictionary.keys():
                v = values.get(k, None)
                if v is not None:
                    data_dictionary[k].append(int(v))



    time_seconds = np.array([(t - times[0]).total_seconds() for t in times])

    stats = [MemoryPlotStat(key, data) for key, data in data_dictionary.items()]

    mpg = MemoryPlotGenerator(time_seconds, stats)

    mpg.show_plot()

    # # filt =  {sk: stats[sk]} if sk in stats else {}.items()
    # #
    # # sk_der1 =  "dx/dy " + sk
    # # sk_der2 = "d^2x/dy^2  " + sk
    # # sk_der3 = "d^3x/dy^3" + sk
    # #
    # # sk_filter = gaussian_filter1d(filt[sk], sigma=7)
    # #
    # # sk_der1 = np.gradient(filt[sk], x_seconds)
    # # sk_der1 = gaussian_filter1d(sk_der1, sigma=5)
    # #
    # #
    # # sk_der2 = np.gradient(sk_der1, x_seconds)
    # # sk_der2 = gaussian_filter1d(sk_der2, sigma=14)
    # #
    # # allocation_end = np.argmin(sk_der2)
    # # allocation_start = np.argmax(sk_der2[:allocation_end])
    # #
    # #
    # # sk_der3 = np.gradient(sk_der2, x_seconds)
    # # sk_der3 = gaussian_filter1d(sk_der3, sigma=15)
    # #
    # #
    # #
    # # maxima = find_n_maxima(sk_der3[allocation_start:], sk_der1[allocation_start:], N-1)
    # # maxima = [ima + allocation_start for ima in maxima]
    # #
    # # filt["sk_der1"] = sk_der1
    # # filt["sk_der2"] = sk_der2
    # # filt["sk_der3"] = sk_der3
    #
    # name = "docs/" + Path(filename).name.split(".")[0] + ".html"
    # # generate_plot(name, x_seconds, tuple(filt.items()), x_seconds[allocation_start], x_seconds[allocation_end], *[x_seconds[i] for i in maxima])
    #
    #
    # generate_plot(name, x_seconds, tuple(stats.items()), None, None)




if __name__ == '__main__':
    main()
