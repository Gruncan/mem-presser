from datetime import datetime
import sys
import json
from pathlib import Path


import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks


import matplotlib.pyplot as plt
import mplcursors
import mpld3

MU = 'Memory Used'


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
        self.data_der1 = None
        self.data_der2 = None
        self.data_der3 = None


    def calculate_der1(self, time):
        data_der1 = np.gradient(self.data, time)
        self.data_der1 = gaussian_filter1d(data_der1, sigma=5)
        return self.data_der3

    def calculate_der2(self, time):
        if self.data_der1 is None:
            self.calculate_der1(time)

        data_der2 = np.gradient(self.data_der1, time)
        self.data_der2 = gaussian_filter1d(data_der2, sigma=14)
        return self.data_der2

    def calculate_der3(self, time):
        if self.data_der2 is None:
            self.calculate_der2(time)

        data_der3 = np.gradient(self.data_der2, time)
        self.data_der3 = gaussian_filter1d(data_der3, sigma=15)
        return self.data_der3

class MemoryPlotGenerator:

    def __init__(self, *data_sets):
        self.data_sets = data_sets
        self.title = "Memory Usage"
        self.x_label = "Time (Seconds)"
        self.y_label = "Memory Used (KB)"
        self.start_bar = None
        self.end_bar = None
        self.bars = []
        self.filters = None


    def add_start_end_bars(self, start_bar, end_bar):
        self.start_bar = start_bar
        self.end_bar = end_bar


    def __generic_plot(self):
        fig, ax = plt.subplots(figsize=(16, 9))

        lines = []

        for data_set in self.data_sets:
            for stat in data_set.get_stats():
            # if self.filters is None or stat.name in self.filters:
                line, = ax.plot(data_set.time, stat.data, label=f"{data_set.name} ({stat.label})")
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

    def align_memory_data_sets(self):
        m_set0 = self.data_sets[0]
        start_time_0, end_time_0 = m_set0.get_allocation_start_end_time()


        for m_setx in self.data_sets[1:]:
            start_time_x, end_time_x = m_setx.get_allocation_start_end_time()
            offset_required = start_time_x - start_time_0
            m_setx.time -= offset_required

        return self

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

class MemoryDataSet:

    def __init__(self, name, time, stats):
        self.name = name
        self.time = time
        self.stats = stats
        self.filters = []

    def get_allocation_start_end_index(self):
        mu_der2 = self.stats[MU].calculate_der2(self.time)

        allocation_end = np.argmin(mu_der2)
        allocation_start = np.argmax(mu_der2[:allocation_end])

        return allocation_start, allocation_end

    def get_allocation_start_end_time(self):
        s, e = self.get_allocation_start_end_index()
        return self.time[s], self.time[e]

    def __getitem__(self, item):
        return self.stats.get(item)

    def add_filter(self, *values):
        self.filters += values
        return self

    def get_stats(self):
        return [stat for stat in self.stats.values() if len(self.filters) == 0 or stat.name in self.filters]

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


def read_mem_file(filename, name=None):
    data_dictionary = {}
    times = []


    with open(filename, "r") as f:
        lines = f.readlines()
        for line in lines:
            d = json.loads(line)
            key = list(d.keys())[0]
            values = d[key]
            if len(data_dictionary) == 0:
                data_dictionary = {key: list() for key in values.keys()}
                data_dictionary[MU] = []
            times.append(datetime.strptime(key, '%Y-%m-%d %H:%M:%S.%f'))
            data_dictionary[MU].append((int(values["total"]) - int(values["free"])))
            for k in data_dictionary.keys():
                v = values.get(k, None)
                if v is not None:
                    data_dictionary[k].append(int(v))

    stats = {key: MemoryPlotStat(key, data) for key, data in data_dictionary.items()}
    time_seconds = np.array([(t - times[0]).total_seconds() for t in times])

    if name is None:
        name = filename

    return MemoryDataSet(name, time_seconds, stats)

def main():
    args = sys.argv[1:]
    if len(args) < 1 or len(args) > 2:
        print("Unsure how to parse!", file=sys.stderr)
        return

    filename = args[0]

    second_filename = args[1] if len(args) == 2 else None

    stats = (MU, "buffers", "cached", "swapCache", "active", "inActive", "swapTotal", "swapFree", "zswap",
             'zswapped', 'dirty', 'writeback', 'pagesAnon', 'pageMapped', 'kernelStack', 'pageTables',
             'bounce', 'vmallocChunk', 'perCPU')


    base_path = "/home/duncan/Development/Uni/Thesis/Data/memlog_no_swap/"

    mds1 = read_mem_file(base_path + "memlog_nswap2.json", "No Swap 2").add_filter(MU)
    mds2 = read_mem_file(base_path + "memlog_nswap3.json", "No Swap 3").add_filter(MU)
    # mds3 = read_mem_file(base_path + "memlog_nswap4.json", "No Swap 4").add_filter(MU)
    # mds4 = read_mem_file(base_path + "memlog_nswap5.json", "No Swap 5").add_filter(MU)


    mpg = MemoryPlotGenerator(mds1, mds2)

    mpg.save_plot("docs/noswap_unaligned.png")
    # mpg.compile_to_html("docs/noswap_unaligned.html")



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
