#!/usr/bin/env python
'''
  logs_api_int_script.py

  This file is a part of the AppMetrica.

  Copyright 2017 YANDEX

  You may not use this file except in compliance with the License.
  You may obtain a copy of the License at https://yandex.com/legal/metrica_termsofuse/
'''

import StringIO
import datetime
import json
import os
import time
import pandas as pd
import requests

if 'CH_HOST' not in os.environ:
    CH_HOST = 'http://localhost:8123'
else:
    CH_HOST = os.environ['CH_HOST']

if 'CH_USER' not in os.environ:
    CH_USER = ''
else:
    CH_USER = os.environ['CH_USER']

if 'CH_PASSWORD' not in os.environ:
    CH_PASS = ''
else:
    CH_PASS = os.environ['CH_PASSWORD']

if 'LOGS_API_HISTORY_PERIOD' not in os.environ:
    LOGS_API_HISTORY_PERIOD = 30
else:
    LOGS_API_HISTORY_PERIOD = int(os.environ['LOGS_API_HISTORY_PERIOD'])

if 'PROCESSING_ROWS' not in os.environ:
    PROCESSING_ROWS = 10000
else:
    PROCESSING_ROWS = int(os.environ['PROCESSING_ROWS'])

CH_DATABASE = 'mobile'
CH_TABLE = 'events_all'


def get_create_date(api_key, token):
    app_details_url = 'https://api.appmetrica.yandex.ru/management/v1/application/{id}?oauth_token={token}'.format(
        id=api_key,
        token=token
    )
    r = requests.get(app_details_url)
    create_date = None
    if r.status_code == 200:
        app_details = json.loads(r.text)
        if ('application' in app_details) and ('create_date' in app_details['application']):
            create_date = app_details['application']['create_date']


def get_clickhouse_data(query, host=CH_HOST):
    '''Returns ClickHouse response'''
    # print query
    if CH_USER == '':
        r = requests.post(host, data=query)
    else:
        r = requests.post(host, data=query, auth=(CH_USER, CH_PASS))
    if r.status_code == 200:
        return r.text
    else:
        raise ValueError(r.text)


def upload(table, content, host=CH_HOST):
    '''Uploads data to table in ClickHouse'''
    query_dict = {
        'query': 'INSERT INTO ' + table + ' FORMAT TabSeparatedWithNames '
    }

    if CH_USER == '':
        r = requests.post(host, data=content, params=query_dict)
    else:
        r = requests.post(host, data=content, params=query_dict, auth=(CH_USER, CH_PASS))

    result = r.text
    if r.status_code == 200:
        return result
    else:
        raise ValueError(r.text)


def drop_table(db, table):
    q = 'DROP TABLE IF EXISTS {db}.{table}'.format(
        db=db,
        table=table
    )

    get_clickhouse_data(q)


def database_exists(db):
    q = 'SHOW DATABASES'
    dbs = get_clickhouse_data(q).strip().split('\n')
    return (db in dbs)


def database_create(db):
    q = 'CREATE DATABASE {db}'.format(db=db)
    get_clickhouse_data(q)


def table_exists(db, table):
    q = 'SHOW TABLES FROM {db}'.format(db=db)
    tables = get_clickhouse_data(q).strip().split('\n')
    return (table in tables)


def table_create(db, table):
    q = '''
    CREATE TABLE {db}.{table} (
        EventDate Date,
        DeviceID String,
        EventName String,
        EventTimestamp UInt64,
        AppPlatform String,
        Country String,
        APIKey UInt64, 
        AppVersionName String,
        AppBuildNumber UInt32
    )
    ENGINE = MergeTree(EventDate, cityHash64(DeviceID), (EventDate, cityHash64(DeviceID)), 8192)
    '''.format(
        db=db,
        table=table
    )
    get_clickhouse_data(q)


def create_tmp_table_for_insert(db, table, date1, date2):
    q = '''
        CREATE TABLE tmp_data_ins ENGINE = MergeTree(EventDate, cityHash64(DeviceID),
                                            (EventDate, cityHash64(DeviceID)), 8192)
        AS
        SELECT
            EventDate,
            DeviceID,
            EventName,
            EventTimestamp,
            AppPlatform,
            Country,
            APIKey,
            AppVersionName, 
            AppBuildNumber
        FROM tmp_data
        WHERE NOT ((EventDate, DeviceID, EventName, EventTimestamp, AppPlatform, Country, APIKey, AppVersionName, AppBuildNumber) GLOBAL IN
            (SELECT
                EventDate,
                DeviceID,
                EventName,
                EventTimestamp,
                AppPlatform,
                Country,
                APIKey,
                AppVersionName,
                AppBuildNumber
            FROM {db}.{table}
            WHERE EventDate >= '{date1}' AND EventDate <= '{date2}'))
    '''.format(
        db=db,
        table=table,
        date1=date1,
        date2=date2
    )

    get_clickhouse_data(q)


def insert_data_to_prod(db, table):
    q = '''
        INSERT INTO {db}.{table}
            SELECT
                EventDate,
                DeviceID,
                EventName,
                EventTimestamp,
                AppPlatform,
                Country,
                APIKey,
                AppVersionName,
                AppBuildNumber
            FROM tmp_data_ins
    '''.format(
        db=db,
        table=table
    )

    get_clickhouse_data(q)

def process_date(date, token, api_key, db, table):
    url_tmpl = 'https://api.appmetrica.yandex.ru/logs/v1/export/events.csv?application_id={api_key}&date_since={date1}%2000%3A00%3A00&date_until={date2}%2023%3A59%3A59&date_dimension=default&fields=event_name%2Cevent_timestamp%2Cappmetrica_device_id%2Cos_name%2Ccountry_iso_code%2Ccity%2Capp_version_name%2Capp_build_number&oauth_token={token}'
    url = url_tmpl.format(api_key=api_key, date1=date, date2=date, token=token)

    print url
    r = requests.get(url)

    while r.status_code != 200:
        print r.status_code,
        if r.status_code != 202:
            raise ValueError, r.text

        time.sleep(10)
        r = requests.get(url)

    for df in pd.read_csv(url, chunksize=PROCESSING_ROWS, iterator=True):
        df = df.drop_duplicates()
        df['event_date'] = map(lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d'), df.event_timestamp)
        df['api_key'] = api_key

        drop_table('default', 'tmp_data')
        drop_table('default', 'tmp_data_ins')

        table_create('default', 'tmp_data')

        upload(
            'tmp_data',
            df[['event_date', 'appmetrica_device_id', 'event_name', 'event_timestamp',
                'os_name', 'country_iso_code', 'api_key', 'app_version_name', 'app_build_number']].to_csv(index=False, sep='\t')
        )
        create_tmp_table_for_insert(db, table, date, date)
        insert_data_to_prod(db, table)
        drop_table('default', 'tmp_data')
        drop_table('default', 'tmp_data_ins')


def main(first_flag=False):
    if 'TOKEN' not in os.environ:
        token = ''
    else:
        token = os.environ['TOKEN']
    if 'API_KEYS' not in os.environ:
        api_keys = []
    else:
        api_keys = json.loads(os.environ['API_KEYS'])

    if first_flag:
        # create_date = get_create_date(api_key, token)
        # if create_date is None:
        #     date1 = (datetime.datetime.today() - datetime.timedelta(365)).strftime('%Y-%m-%d')
        # else:
        #     date1 = create_date
        date1 = (datetime.datetime.today() - datetime.timedelta(LOGS_API_HISTORY_PERIOD)).strftime('%Y-%m-%d')
    else:
        date1 = (datetime.datetime.today() - datetime.timedelta(7)).strftime('%Y-%m-%d')

    date2 = (datetime.datetime.today()).strftime('%Y-%m-%d')

    if not database_exists(CH_DATABASE):
        database_create(CH_DATABASE)
        print 'Database created'

    if not table_exists(CH_DATABASE, CH_TABLE):
        table_create(CH_DATABASE, CH_TABLE)
        print 'Table created'

    print 'Loading period %s - %s' % (date1, date2)
    for api_key in api_keys:
        print api_key
        for date in pd.date_range(date1, date2):
            date_str = date.strftime('%Y-%m-%d')
            print 'Loading data for %s' % date_str
            process_date(date_str, token, api_key, CH_DATABASE, CH_TABLE)
    print 'Finished loading data'


if __name__ == '__main__':
    main()
