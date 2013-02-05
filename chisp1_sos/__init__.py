from flask import Flask
import sqlite3

# Create application object
app = Flask(__name__)

app.config.from_object('chisp1_sos.defaults')
app.config.from_envvar('APPLICATION_SETTINGS', silent=True)

# Create logging
if app.config.get('LOG_FILE') == True:
    import logging
    from logging import FileHandler
    file_handler = FileHandler('logs/chisp1_sos.log')
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

# Import everything
import chisp1_sos.views
import chisp1_sos.models