from flask import Flask, render_template
import pyodbc
import json

app = Flask(__name__)

conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    r'DBQ=C:\Users\reinh\OneDrive\Documents\Schützenverein Stukenbrock\Analyse.accdb;'
)
conn = pyodbc.connect(conn_str)
# Verbindung zur SQLite-Datenbank herstellen
c = conn.cursor()


# Daten aus der Datenbank abfragen
c.execute('SELECT * FROM Kontakte')

# columns = [column[0] for column in c.description]
rows = c.fetchall()
# data1 = rows.to_dict('records')

# column_names = [r[0] for r in rows]
columns = [column[0] for column in c.description]
# Print the list of column names

data = []
for row in rows:
    obj = {}
    i = 0
    for column in columns:
        obj[column] = row[i]
        i += 1
    data.append(obj)

# Daten in JSON konvertieren
json_data = json.dumps(data)

# Flask-Route definieren


@app.route('/')
def index():
    # Daten an das HTML-Template übergeben
    # return render_template('index.html', data=data)
    return json_data


if __name__ == '__main__':
    app.run(debug=True)
