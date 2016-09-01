import pandas as pd
import numpy as np


def dorner_binning(data, bin_width_minutes=20):
    bin_number = 0
    ontime_sum = 0
    bins = []
    for key, row in data.iterrows():
        if ontime_sum + row.fOnTimeAfterCuts > bin_width_minutes * 60:
            bin_number += 1
            ontime_sum = 0
        bins.append(bin_number)
        ontime_sum += row['fOnTimeAfterCuts']
    return pd.Series(bins, index=data.index)


def groupby_observation_blocks(runs):
    ''' Groupby for consecutive runs of the same source'''
    runs = runs.sort_values('fRunStart')
    next_is_different = runs.fSourceName != runs.fSourceName.shift(-1)
    next_is_different.iloc[-1] = False
    observation_blocks = next_is_different.cumsum()
    return runs.groupby(observation_blocks)


def get_qla_data(night, db, bin_width_minutes=20):
    ''' this will get the QLA results to call if you have to send an alert '''
    keys = [
        'QLA.fRunID',
        'QLA.fNight',
        'QLA.fNumExcEvts',
        'QLA.fNumSigEvts',
        'QLA.fNumBgEvts',
        'QLA.fOnTimeAfterCuts',
        'RunInfo.fRunStart',
        'RunInfo.fRunStop',
        'Source.fSourceName',
        'Source.fSourceKEY',
    ]

    sql_query = """SELECT {comma_sep_keys}
        FROM AnalysisResultsRunLP QLA
        LEFT JOIN RunInfo
        ON QLA.fRunID = RunInfo.fRunID AND QLA.fNight = RunInfo.fNight
        LEFT JOIN Source
        ON RunInfo.fSourceKEY = Source.fSourceKEY
        WHERE QLA.fNight = {night}
    """
    sql_query = sql_query.format(
        comma_sep_keys=', '.join(keys),
        night=night,
    )

    data = pd.read_sql_query(
        sql_query,
        db,
        parse_dates=['fRunStart', 'fRunStop'],
    )

    # drop rows with NaNs from the table, these are unfinished qla results
    data.dropna(inplace=True)

    if len(data.index) == 0:
        return

    data.sort_values('fRunStart', inplace=True)
    data.index = np.arange(len(data.index))

    # group by source to do the analysis seperated for each one
    grouped = groupby_observation_blocks(data)
    binned = pd.DataFrame()
    for block, group in grouped:
        group = group.copy()
        group['bin'] = dorner_binning(group, bin_width_minutes)
        agg = group.groupby('bin').aggregate({
            'fOnTimeAfterCuts': 'sum',
            'fNumExcEvts': 'sum',
            'fNumSigEvts': 'sum',
            'fNumBgEvts': 'sum',
            'fRunStart': 'min',
            'fRunStop': 'max',
            'fSourceName': lambda x: x.iloc[0],
        })
        agg['rate'] = agg.fNumExcEvts / agg.fOnTimeAfterCuts * 3600
        agg['xerr'] = (agg.fRunStop - agg.fRunStart) / 2
        agg['timeMean'] = agg.fRunStart + agg.xerr
        agg['yerr'] = np.sqrt(agg.fNumSigEvts + 0.2 * agg.fNumBgEvts)
        agg['yerr'] /= agg.fOnTimeAfterCuts / 3600
        # remove last bin if it has less then 90% OnTime of the required
        # binning
        if agg['fOnTimeAfterCuts'].iloc[-1] < 0.9 * 60 * bin_width_minutes:
            agg = agg.iloc[:-1]
        binned = binned.append(agg, ignore_index=True)

    binned['significance'] = li_ma_significance(
        binned.fNumSigEvts, binned.fNumBgEvts * 5, 0.2
    )

    return binned


def li_ma_significance(N_on, N_off, alpha=0.2):
    N_on = np.array(N_on, copy=False, ndmin=1)
    N_off = np.array(N_off, copy=False, ndmin=1)

    with np.errstate(divide='ignore', invalid='ignore'):
        p_on = N_on / (N_on + N_off)
        p_off = N_off / (N_on + N_off)

        t1 = N_on * np.log(((1 + alpha) / alpha) * p_on)
        t2 = N_off * np.log((1 + alpha) * p_off)

        ts = (t1 + t2)
        significance = np.sqrt(ts * 2)

    significance[np.isnan(significance)] = 0
    significance[N_on < alpha * N_off] = 0

    return significance
