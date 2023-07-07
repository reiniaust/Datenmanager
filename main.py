from flask import Flask, render_template
import pyodbc
import json

app = Flask(__name__)

with open("config.json") as f:
    config = json.load(f)

conn_str = config["connection_string"]
conn = pyodbc.connect(conn_str)
c = conn.cursor()

views = config["views"]
relations = config["relations"]

for key, value in views.items():
    # Den ersten Buchstaben als Großbuchstaben formatieren
    view_name = key

    view = views[view_name]
    column_names = ""
    comma = " "
    for key, value in view["columns"].items():
        column_names += comma + view["table"] + "." + value + " as " + key
        comma = ", "

    try:
        relation = relations[view_name]
        for (key, value) in relation.items():
            joinTbl = views[value]["table"]
            foreignId = views[value]["columns"]["ID"]
            join = " left join " + joinTbl + " on " + \
                view["table"] + "." + key + \
                " = " + joinTbl + "." + foreignId
    except:
        join = ""

    c.execute("select " + column_names + " from " + view["table"] + join)

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

    view["data"] = data


@app.route("/data/<view_name>")
def index(view_name):
    # Den ersten Buchstaben als Großbuchstaben formatieren
    view_name = view_name.capitalize()

    view = views[view_name]
    data = view["data"]
    json_data = json.dumps(data)

    # Daten an das HTML-Template übergeben
    return render_template("index.html", data=data)
    # return json_data


if __name__ == "__main__":
    app.run(debug=True)
