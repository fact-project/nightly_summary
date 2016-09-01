import matplotlib.pyplot as plt
from collections import defaultdict
from itertools import cycle
import numpy as np

cycle = cycle(plt.rcParams['axes.prop_cycle'])

plt.style.use('ggplot')

colors = defaultdict(lambda: next(cycle)['color'])
colors[None] = 'lightgray'


def plot_runtype(runs, filename):

    fig, ax = plt.subplots()

    (
        runs
        .groupby('fRunTypeName')
        .fOnTime.sum()
        .apply(lambda x: x / 3600)
    ).plot.barh(ax=ax)

    ax.set_xlabel('OnTime / h')
    ax.set_ylabel('')

    fig.tight_layout()
    fig.savefig(filename, dpi=300)


def plot_run_timeline(runs, filename):
    fig = plt.figure(figsize=(15/2.54, 5/2.54))
    ax = fig.add_axes([0.025, 0.3, 0.95, 0.4])

    for run in runs.itertuples():

        ax.fill_between(
            [run.fRunStart, run.fRunStop],
            y1=0,
            y2=1,
            linewidth=0,
            color=colors[run.fSourceName],
        )

    sources = runs.dropna().fSourceName.unique()
    objects = [
        plt.Rectangle((0, 0), 0, 0, facecolor=colors[source])
        for source in sources
    ]
    ax.legend(
        objects,
        sources,
        ncol=3,
        bbox_to_anchor=[0.5, 1.01],
        loc='lower center',
    )

    ax.set_ylim(-0.1, 1.1)
    ax.set_yticks([])
    ax.set_yticklabels([])
    ax.set_xlabel('')
    ax.set_ylabel('')
    fig.autofmt_xdate()

    # fig.tight_layout()
    fig.savefig(filename, dpi=300)


def plot_sources(runs, filename):

    fig, ax = plt.subplots()
    (
        runs
        .dropna()
        .groupby('fSourceName')
        .fOnTime.sum()
        .apply(lambda x: x / 3600)
    ).plot.barh(ax=ax)

    ax.set_xlabel('OnTime / h')
    ax.set_ylabel('')

    fig.tight_layout()
    fig.savefig(filename, dpi=300)


def plot_qla(qla_data, filename):
    fig = plt.figure(figsize=(15/2.54, 10/2.54))

    ax_sig = fig.add_axes([0.11, 0.1, 0.87, 0.2])
    ax_rate = fig.add_axes([0.11, 0.35, 0.87, 0.47], sharex=ax_sig)

    colors = [e['color'] for e in plt.rcParams['axes.prop_cycle']]
    for (name, group), color in zip(qla_data.groupby('fSourceName'), colors):
        if len(group.index) == 0:
            continue

        ax_rate.errorbar(
            x=group.timeMean.values,
            y=group.rate.values,
            xerr=group.xerr.values,
            yerr=group.yerr.values,
            label=name,
            fmt='o',
            mec='none',
            color=color,
        )

        ax_sig.errorbar(
            x=group.timeMean.values,
            y=group.significance.values,
            xerr=group.xerr.values,
            label=name,
            fmt='o',
            mec='none',
            color=color,
        )
    ax_rate.legend(loc='lower center', ncol=3, bbox_to_anchor=[0.5, 1.01])
    ax_rate.set_ylabel('Excess Event Rate / $\mathrm{h}^{-1}$')

    ax_sig.axhline(3, color='darkgray')
    ax_sig.set_ylabel('$S_{\mathrm{Li/Ma}} \,\, / \,\, \sigma$')

    ymax = max(3.25, np.ceil(ax_sig.get_ylim()[1]))
    ax_sig.set_ylim(0, ymax)
    ax_sig.set_yticks(np.arange(0, ymax + 0.1, ymax // 4 + 1))

    plt.setp(ax_rate.get_xticklabels(), visible=False)

    fig.autofmt_xdate()
    fig.savefig(filename)
