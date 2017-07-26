#!/usr/bin/env python
'''
  run.py

  This file is a part of the AppMetrica.

  Copyright 2017 YANDEX

  You may not use this file except in compliance with the License.
  You may obtain a copy of the License at https://yandex.com/legal/metrica_termsofuse/
'''

import os
from flask import Flask, request, render_template
from flask_bootstrap import Bootstrap
import utils
from forms import ParamsForm

app = Flask(__name__)
app.debug = True
app.secret_key = 's3cr3t'
Bootstrap(app)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = ParamsForm()
    return render_template("index.html",
                           form=form)


@app.route('/result', methods=['GET', 'POST'])
def get_result():
    params = request.args.to_dict(flat=True)
    print params

    start_date = params['start_date']
    end_date = params['end_date']
    api_key = params['api_key']
    platform = params['platform']
    country = params['country']

    steps = []
    for i in range(10):
        cur_step = params['step%d' % i].strip()
        if cur_step == '':
            break
        cur_steps = cur_step.split(',')
        cur_steps = map(lambda x: x.strip(), cur_steps)
        steps.append(cur_steps)

    funnel, query = utils.get_funnel_result(start_date, end_date, api_key, platform, country, steps)

    return render_template("result.html",
                           query=query,
                           funnel=funnel,
                           start_date=start_date,
                           end_date=end_date,
                           platform=platform,
                           api_key=api_key,
                           country=country,
                           step0=params['step0'],
                           step1=params['step1'],
                           step2=params['step2'],
                           step3=params['step3'],
                           step4=params['step4'],
                           step5=params['step5'],
                           step6=params['step6'],
                           step7=params['step7'],
                           step8=params['step8'],
                           step9=params['step9']
                           )


def main():
    if 'FLASK_PORT' not in os.environ:
        port = 5000
    else:
        port = int(os.environ['FLASK_PORT'])
    app.run(debug=True,
            host='0.0.0.0',
            port=port,
            processes=3)


if __name__ == '__main__':
    main()
