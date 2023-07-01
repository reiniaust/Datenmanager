from flask import Flask, render_template
import pyodbc
import json

app = Flask(__name__)

conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    r'DBQ=C:\Users\reinh\OneDrive\Documents\Schützenverein Stukenbrock\Analyse.accdb;'
)
conn = pyodbc.connect(conn_str)
c = conn.cursor()

view = 'kontakte'

column_def = {
    "ID": "ID",
    "Nachname": "NACHNAME",
    "Vorname": "VORNAME"
}


@app.route('/' + view)
def index():
    column_names = ""
    comma = " "
    for key, value in column_def.items():
        column_names += comma + view + "." + value + " as " + key
        comma = ", "

    c.execute("SELECT " + column_names + " FROM " + view)

    rows = c.fetchall()

    columns = [column[0] for column in c.description]

    data = []
    # Daten in JSON konvertieren
    for row in rows:
        obj = {}
        i = 0
        for column in columns:
            obj[column] = row[i]
            i += 1
        data.append(obj)
    json_data = json.dumps(data)

    # Daten an das HTML-Template übergeben
    # return render_template('index.html', data=data)
    return json_data


if __name__ == '__main__':
    app.run(debug=True)
