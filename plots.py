import matplotlib.pyplot as plt
from collections import defaultdict
from itertools import cycle
from IPython import embed

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
