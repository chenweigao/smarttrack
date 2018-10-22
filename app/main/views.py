from flask import render_template, flash
from . import main
import os
from app import create_app, db, mongo
from app.models import User, Role
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from datetime import datetime
from flask import render_template, Flask, Response
import os
from wtforms import ValidationError

from .forms import VideoForm

import operator
from functools import reduce
import pymongo
from app.filter import TracerList

import json

from flask import jsonify

def get_raw_data(count, startdatetime=None):
    db_conn = pymongo.MongoClient()
    dev_names = [d['name'] for d in db_conn['identity']['devices'].find()]
    # print(dev_names)

    ret=None
    if startdatetime is None:
        ret = [list(db_conn['message'][dev_name].find().sort('time', -1).limit(count)) for dev_name in dev_names]
    else:
        ret = [list(db_conn['message'][dev_name].find({'time':{'$gt':str(startdatetime)}}).sort('time', -1).limit(count)) for dev_name in dev_names]
        print('TIMECUT: ', str(startdatetime), 'RETLEN: ', len(ret))
    db_conn.close()

    ret = reduce(operator.add, ret)
    for i in range(len(ret)):
        if 'data' in ret[i].keys():
            ret[i]['data']['time']=ret[i]['time']
            ret[i]['data']['_id']=ret[i]['_id']
            ret[i]=ret[i]['data']

    for i in ret:
        tp = [int(s) for s in i['time'].replace('-', ' ').replace(':', ' ').replace('.', ' ').split()]
        if len(tp) == 7:
            i['time'] = datetime(tp[0], tp[1], tp[2], tp[3], tp[4], tp[5], tp[6])
        else:
            i['time'] = None

    ret.sort(key=lambda d: d['time'])

    return ret[-count:]

@main.route('/', methods=['GET', 'POST'])
@main.route('/index', methods=['GET', 'POST'])
def index():
    form = VideoForm()
    map_on = form.switch_map.data
    video_on = form.switch_video.data
    
    map_switch = Role(map_switch=form.switch_map.data)
    video_switch = Role(video_switch=form.switch_video.data)
    # if map_on == True:
    #     flash(u'success open the map!')
    # else:
    #     flash(u'map closed!')

    # if video_on == True:
    #     flash(u'success open the video!')
    # else:
    #     flash(u'video closed!')
    
    db.session.add(map_switch)
    db.session.add(video_switch)
    # db.session.commit()  
    return render_template('index.html', form=form, map_on=map_on, video_on=video_on)

if os.environ.get('CAMERA'):
    Camera = import_module('camera_' + os.environ['CAMERA']).Camera
else:
    from app.camera import Camera


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@main.route('/data.json')
def data():
    return str([{'x':i['x'], 'y':i['y'], 'time':i['time']} for i in mongo.db.mycol.find()])

@main.route('/path.json')
def path():
    l = TracerList()
    #return str(get_raw_data(10))

    for d in get_raw_data(1000):
        d.pop('_id')
        l.tracetarget(d)

    l=[tl.targetlist for tl in l.tracerlist if len(tl.targetlist) > 1]
    for p in l:
        for t in p:
            t['time']=str(t['time'])

    resp = jsonify(l)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
    # return json.dumps(l)

@main.route('/video_feed', methods=['GET', 'POST'])
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

        
# @main.route('/settings', methods=['GET', 'POST'])
# def settings():
#     from .forms import SetForm
#     form = SetForm()
#     return render_template('settings.html', form = form)


# @main.route('/tables', methods=['GET', 'POST'])
# def tables():
#     return render_template('tables.html')


# @main.route('/charts')
# def charts():
#     legend = 'Monthly Data'
#     labels = ["January", "February", "March",
#               "April", "May", "June", "July", "August"]
#     values = [10, 9, 8, 7, 6, 4, 7, 8]
#     return render_template('charts.html', values=values, labels=labels, legend=legend)

@main.route('/charts')
def charts():
    return render_template('charts.html')

@main.route('/maps')
def maps():
    return render_template('maps.html')
@main.route('/videos')
def videos():
    return render_template('video.html')
