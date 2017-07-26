#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
  utils.py

  This file is a part of the AppMetrica.

  Copyright 2017 YANDEX

  You may not use this file except in compliance with the License.
  You may obtain a copy of the License at https://yandex.com/legal/metrica_termsofuse/
'''

import os
import time
import plotly
from plotly import graph_objs as go

# init_notebook_mode(connected = True)


HOST = 'http://mtsmart.yandex.ru:8123'
HOST = 'http://localhost:8123'
if 'CH_HOST' not in os.environ:
    HOST = 'http://localhost:8123'
else:
    HOST = os.environ['CH_HOST']

if 'CH_USER' not in os.environ:
    USER = ''
else:
    USER = os.environ['CH_USER']

if 'CH_PASSWORD' not in os.environ:
    PASS = ''
else:
    PASS = os.environ['CH_PASSWORD']

import httplib

httplib._MAXHEADERS = 100000

import requests
import pandas as pd
import StringIO


def get_clickhouse_data(query, host=HOST, connection_timeout=1500):
    NUMBER_OF_TRIES = 30
    DELAY = 5

    for i in range(NUMBER_OF_TRIES):
        if (USER != '') and (PASS != ''):
            r = requests.post(host, params={'query': query}, auth=(USER, PASS), timeout=connection_timeout)
        else:
            r = requests.post(host, params={'query': query}, timeout=connection_timeout)
        if r.status_code == 200:
            return r.text
        else:
            print 'ATTENTION: try #%d failed' % i
            if i != (NUMBER_OF_TRIES - 1):
                print r.text
                time.sleep(DELAY)
            else:
                raise ValueError, r.text


def get_clickhouse_df(query, host=HOST, connection_timeout=1500):
    data = get_clickhouse_data(query, host, connection_timeout)
    df = pd.read_csv(StringIO.StringIO(data), sep='\t')
    return df


def get_funnel_clickhouse(date1, date2, api_key, platform, country, global_condition, steps_achieved_select,
                          steps_achieved_groupby, steps_indexes):
    q_tmpl = '''
    SELECT
        count() as devices,
{steps_achieved_select}
    FROM
        (SELECT
            DeviceID as device_id,
            groupArray(EventName) as events,
            groupArray(EventTimestamp) as events_index,
{steps_indexes}
        FROM
            (SELECT
                DeviceID,
                EventName,
                EventTimestamp
            FROM mobile.events_all
            WHERE EventDate >= '{start_date}'
                AND EventDate <= '{end_date}' {platform_filter}
                AND APIKey = {api_key} {country_filter}
                AND ({global_condition})
            ORDER BY EventTimestamp)
        GROUP BY DeviceID)
    GROUP BY
{steps_achieved_groupby}
    FORMAT TabSeparatedWithNames
    '''
    if platform != '':
        platform_filter = "\nAND AppPlatform = '{platform}'".format(platform=platform)
    else:
        platform_filter = ""

    if country != '':
        country_filter = "\nAND regionToCountry(RegionID) = {country}".format(country=country)
    else:
        country_filter = ""

    q = q_tmpl.format(
        start_date=date1,
        end_date=date2,
        platform_filter=platform_filter,
        api_key=api_key,
        country_filter=country_filter,
        global_condition=global_condition,
        steps_achieved_select=steps_achieved_select,
        steps_achieved_groupby=steps_achieved_groupby,
        steps_indexes=steps_indexes
    )

    return get_clickhouse_df(q), q


def get_funnel_plotly(values):
    if len(values) == 0:
        return ''

    values_labels = []
    for i in range(len(values)):
        if i == 0:
            values_labels.append(values[0])
        else:
            values_labels.append('%d (%.2f%%)' % (values[i], (100. * values[i]) / values[i - 1]))

    phases = map(lambda x: 'Step ' + str(x + 1), range(len(values)))

    colors = ['#d54936', '#faca34', '#437cba', '#8bc34a', '#795548',
              '#309688', '#000000', '#40bcd4', '#9e9e9e', '#3ca9f4']

    n_phase = len(phases)
    plot_width = 500.

    # height of a section and difference between sections
    section_h = 100
    section_d = 10

    # multiplication factor to calculate the width of other sections
    unit_width = plot_width / max(values)

    # width of each funnel section relative to the plot width
    phase_w = [int(value * unit_width) for value in values]
    print phase_w

    # plot height based on the number of sections and the gap in between them
    height = section_h * n_phase + section_d * (n_phase - 1)

    # list containing all the plot shapes
    shapes = []

    # list containing the Y-axis location for each section's name and value text
    label_y = []

    for i in range(n_phase):
        if (i == n_phase - 1):
            points = [phase_w[i] / 2, height, phase_w[i] / 2, height - section_h]
        else:
            points = [phase_w[i] / 2, height, phase_w[i + 1] / 2, height - section_h]

        path = 'M {0} {1} L {2} {3} L -{2} {3} L -{0} {1} Z'.format(*points)

        shape = {
            'type': 'path',
            'path': path,
            'fillcolor': colors[i],
            'line': {
                'width': 1,
                'color': colors[i]
            }
        }
        shapes.append(shape)

        # Y-axis location for this section's details (text)
        label_y.append(height - (section_h / 2))

        height = height - (section_h + section_d)

    # For phase names
    label_trace = go.Scatter(
        x=[-350] * n_phase,
        y=label_y,
        mode='text',
        text=phases,
        textfont=dict(
            color='rgb(0,0,0)',
            size=15
        )
    )

    # For phase values
    value_trace = go.Scatter(
        x=[350] * n_phase,
        y=label_y,
        mode='text',
        text=values_labels,
        textfont=dict(
            color='rgb(0,0,0)',
            size=15
        )
    )

    data = [label_trace, value_trace]

    layout = go.Layout(
        title="<b>Funnel Chart</b>",
        titlefont=dict(
            size=20,
            color='rgb(0,0,0)'
        ),
        shapes=shapes,
        height=560,
        width=800,
        showlegend=False,
        paper_bgcolor='rgba(255,255,255,1)',
        plot_bgcolor='rgba(255,255,255,1)',
        hovermode=False,
        xaxis=dict(
            showticklabels=False,
            zeroline=False,
            showgrid=False,
            range=[-450, 450]
        ),
        yaxis=dict(
            showticklabels=False,
            zeroline=False,
            showgrid=False
        )
    )

    fig = go.Figure(data=data, layout=layout)
    html = plotly.offline.plot(fig, show_link=False, output_type='div')

    return html


def get_funnel_result(date1, date2, api_key, platform, country, steps):
    all_events = set()
    step_conditions = []
    for step_items in steps:
        step_condition = reduce(lambda x, y: x + ' OR ' + y, map(lambda x: "(name = '%s')" % x, step_items))
        step_conditions.append(step_condition)
        for event in step_items:
            all_events.add(event)

    global_condition = reduce(lambda x, y: x + ' OR ' + y, map(lambda x: "(EventName = '%s')" % x, list(all_events)))

    steps_achieved_select_lst = []
    steps_achieved_groupby_lst = []
    steps_indexes_lst = []
    for i in range(len(step_conditions)):
        steps_achieved_select_lst.append('\t\t(step{i}_index != 0) as step{i}_achieved'.format(i=i))
        steps_achieved_groupby_lst.append('\t\tstep{i}_achieved'.format(i=i))

        if i == 0:
            step_index = "\t\t\tarrayFilter(index, name -> ({condition}), events_index, events)[1] as step{i}_index" \
                .format(condition=step_conditions[i], i=i)
        else:
            not_null_indexes_lst = []
            for j in range(i):
                not_null_indexes_lst.append('(step{j}_index != 0)'.format(j=j))
            not_null_indexes = ' AND '.join(not_null_indexes_lst)

            step_index = "\t\t\tarrayFilter(index, name -> ({condition}) AND (index >= step{prev_i}_index) AND {not_null_indexes}, events_index, events)[1] as step{i}_index" \
                .format(
                condition=step_conditions[i],
                i=i,
                prev_i=i - 1,
                not_null_indexes=not_null_indexes
            )
        steps_indexes_lst.append(step_index)

    steps_achieved_select = ',\n'.join(steps_achieved_select_lst)
    steps_achieved_groupby = ',\n'.join(steps_achieved_groupby_lst)
    steps_indexes = ',\n'.join(steps_indexes_lst)

    df, query = get_funnel_clickhouse(date1, date2, api_key, platform, country, global_condition, steps_achieved_select,
                                      steps_achieved_groupby, steps_indexes)

    df['step'] = df[filter(lambda x: x != 'devices', df.columns)].sum(axis=1)
    df = df[df.step != 0]
    df.sort_values('devices', ascending=False, inplace=True)

    html = get_funnel_plotly(df.devices.values)
    return html, query
