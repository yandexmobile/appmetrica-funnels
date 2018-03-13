#!/usr/bin/env python
'''
  forms.py

  This file is a part of the AppMetrica.

  Copyright 2017 YANDEX

  You may not use this file except in compliance with the License.
  You may obtain a copy of the License at https://yandex.com/legal/metrica_termsofuse/
'''

from flask_wtf import Form
from wtforms import TextField, SelectField

COUNTRY_CHOICES = [
    (u'', u'World'),
    (u'RU', u'Russia'),
    (u'TR', u'Turkey'),
    (u'UA', u'Ukraine'),
    (u'BY', u'Belarus'),
    (u'KZ', u'Kazakhstan')
]

PLATFORM_CHOICES = [
    (u'', u'Total'),
    (u'android', u'Android'),
    (u'iOS', u'iOS'),
    (u'WindowsPhone', u'Windows Phone')
]

VERSION_FILTERS_PARAM = [
    (u'', u'Total'),
    (u'AppVersionName', u'App Version'),
    (u'AppBuildNumber', u'Build Number')
]

VERSION_FILTERS_CONDITION = [
    (u'', u''),
    (u'>=', u'>='),
    (u'=', u'='),
    (u'<=', u'<='),
    (u'>', u'>'),
    (u'<', u'<')
]


class ParamsForm(Form):
    start_date = TextField(u'Start Date')
    end_date = TextField(u'End Date')
    api_key = TextField(u'API Key')
    platform = SelectField(u'Platform', choices=PLATFORM_CHOICES)
    country = SelectField(u'Country', choices=COUNTRY_CHOICES)
    version_filters_param = SelectField(u'VersionFilterParam', choices = VERSION_FILTERS_PARAM)
    version_filters_condition = SelectField(u'VersionFilterCondition', choices = VERSION_FILTERS_CONDITION)
    version_filters_limit = TextField(u'Limit')

    step0 = TextField(u'Step0')
    step1 = TextField(u'Step1')
    step2 = TextField(u'Step2')
    step3 = TextField(u'Step3')
    step4 = TextField(u'Step4')
    step5 = TextField(u'Step5')
    step6 = TextField(u'Step6')
    step7 = TextField(u'Step7')
    step8 = TextField(u'Step8')
    step9 = TextField(u'Step9')
