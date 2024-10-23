from datetime import datetime
import sys
import json
import matplotlib.pyplot as plt
import mplcursors
import math

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks


def generate_plot(time, stats, alloc_start, alloc_end, *vs):
    plt.figure()

    lines = []

    for name, stat in stats:
        line, = plt.plot(time, stat, label=name)
        lines.append(line)


    for i, v in enumerate(vs):
        plt.axvline(x=v, color='black', linestyle='--', linewidth=2, label=f'v{i}={v}')


    plt.axvline(x=alloc_start, color='b', linestyle='--', linewidth=2, label=f'AllocationStart={alloc_start}')
    plt.axvline(x=alloc_end, color='b', linestyle='--', linewidth=2, label=f'AllocationEnd={alloc_end}')


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


    filt =  {sk: stats[sk]} if sk in stats else {}.items()
    x_seconds = np.array([(t - x[0]).total_seconds() for t in x])


    # sk_der1 =  "dx/dy " + sk
    # sk_der2 = "d^2x/dy^2  " + sk
    # sk_der3 = "d^3x/dy^3" + sk

    sk_filter = gaussian_filter1d(filt[sk], sigma=7)

    sk_der1 = np.gradient(filt[sk], x_seconds)
    sk_der1 = gaussian_filter1d(sk_der1, sigma=5)


    sk_der2 = np.gradient(sk_der1, x_seconds)
    sk_der2 = gaussian_filter1d(sk_der2, sigma=14)

    allocation_end = np.argmin(sk_der2)
    allocation_start = np.argmax(sk_der2[:allocation_end])


    sk_der3 = np.gradient(sk_der2, x_seconds)
    sk_der3 = gaussian_filter1d(sk_der3, sigma=15)



    maxima = find_n_maxima(sk_der3[allocation_start:], sk_der1[allocation_start:], N-1)
    maxima = [ima + allocation_start for ima in maxima]


    generate_plot(x_seconds, tuple(filt.items()), x_seconds[allocation_start], x_seconds[allocation_end], *[x_seconds[i] for i in maxima])




if __name__ == '__main__':
    main()