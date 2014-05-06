from flask import Flask, request, current_app
import sqlite3
import datetime

import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText



app = Flask(__name__)
app.debug = True

@app.route('/')
def hello_world():

    output="<h1>Welcome to sensorino</h1>"

   
    return output

def listSensorinos():
	
			


@app.route('/logs/<device>', methods=['GET','PUT', 'POST', "DELETE"])
def getLogs(device):
    conn = sqlite3.connect('/home/elektroid/rest/example.db')
    c = conn.cursor()
    output="<h2>Room states logs</h2>"
    for row in c.execute("SELECT * FROM logs WHERE name=:name", {"name": device}):
        output=output+ "<p>room:<b>"+row[0]+"</b> at "+row[2]+" state: <b>"+row[1]+"</b></p>\n"

    return output
@app.route('/devices/<device>', methods=['PUT', 'POST', "DELETE"])
def update_device_state(device):
    # show the user profile for that user
    if request.method == 'POST':
	conn = sqlite3.connect('/home/elektroid/rest/example.db')
    	c = conn.cursor()
	status=c.execute("UPDATE rooms set state=:state WHERE name=:name",{ "state":request.form['state'] , "name":device})
	c.execute("INSERT INTO logs VALUES (?,?,?)", (device, request.form['state'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

	conn.commit()
	
    	return 'Update room %s with state State %s : result %s' % (device, request.form['state'], status)
    elif request.method == 'PUT':
	conn = sqlite3.connect('/home/elektroid/rest/example.db')
        c = conn.cursor()
        if c.execute("SELECT * from rooms WHERE name=:name", {"name":device}).rowcount>1:
	    return "already exist"
	else:
	     c.execute("INSERT INTO rooms VALUES (?,?)", (device, request.form['state'] ))
	     conn.commit()
	     return 'Created %s with status %s' % (device, request.form['state'])
    elif request.method == 'DELETE':
	conn = sqlite3.connect('/home/elektroid/rest/example.db')
        c = conn.cursor()
        if c.execute("DELETE from rooms WHERE name=:name", {"name":device}):
	     conn.commit()
	     return "deleted %s" % device

    else:
        return "failure"

@app.before_request
def log_request():
    current_app.logger.debug(request.get_data(as_text=True))
    current_app.logger.debug(request.query_string)
    current_app.logger.debug(request.headers)

if __name__ == '__main__':
    if app.debug: use_debugger = True
    try:
        # Disable Flask's debugger if external debugger is requested
        use_debugger = not(app.config.get('DEBUG_WITH_APTANA'))
    except:
        pass
    app.run(port=80, host='0.0.0.0', use_debugger=use_debugger, debug=app.debug,
            use_reloader=use_debugger)

