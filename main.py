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

views = {
    "kontakte": {
        "table": "Kontakte",
        "columns": {
            "ID": "ID",
            "Nachname": "NACHNAME",
            "Vorname": "VORNAME"
        }
    },
    "spenden": {
        "table": "Spenden",
        "columns": {
            "ID": "ID",
            "Spender": "Spender",
            "Betrag": "Betrag"
        }
    }
}


@app.route('/data/<view_name>')
def index(view_name):
    print(view_name)
    view = views[view_name]
    column_names = ""
    comma = " "
    for key, value in view["columns"].items():
        column_names += comma + view["table"] + "." + value + " as " + key
        comma = ", "

    c.execute("SELECT " + column_names + " FROM " + view["table"])

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
