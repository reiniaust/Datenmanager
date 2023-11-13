from flask import Flask, render_template, request, jsonify
import pyodbc
import json
import re

app = Flask(__name__)

with open("config.json") as f:
    config = json.load(f)

views = config["views"]

relations = config["relations"]


def load_data_from_db():

    conn = pyodbc.connect(config["connection_string"])
    c = conn.cursor()

    for view_name, view in views.items():

        column_names = ""
        comma = " "
        for key, value in view["columns"].items():
            column_names += comma + view["table"] + "." + value + " as " + key
            comma = ", "

        orderBy = " order by "
        try:
            orderBy += view["columns"]["Name"]
        except:
            orderBy += view["columns"]["ID"] + " desc"

        c.execute("select " + column_names + " from " +
                  view["table"] + orderBy)

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

        try:
            view["relations"] = {}
            for (key, value) in relations[view_name].items():
                view["relations"][key] = views[value]["data"]
        except:
            view["relations"] = {}

    return views


views_and_data = load_data_from_db()

last_view_name = ""
last_search = ""
last_found_views_and_data = {}
last_view = {}


@app.route("/start")
def index():
    # views = load_data_from_db()

    for view_name, view in views_and_data.items():

        # Es wird nur die erste View verwendet (also break der Schleife nach dem render_template)

        columnsWidth = {}
        for column_name in views[view_name]["columns"].items():
            columnsWidth[column_name] = "50"

        view["data_found"] = view["data"]

        global last_view_name
        last_view_name = view_name

        return render_template("index.html", view_name=view_name, relations=view["relations"], views=views_and_data, columnsWidth=columnsWidth)


@app.route('/form', methods=['POST'])
def form():
    # views = load_data_from_db()

    global last_view_name
    global last_search
    global last_found_views_and_data
    global last_view

    current_view_name = request.form['view_name']
    

    search = request.form['search']
    # Suchtext in Wörter aufteilen
    search_words = search.lower().split()

    if search == last_search and current_view_name == last_view_name:
        # wenn nur auf OK geklickt wurde
        for row in last_view["data"]:
            for key, value in row.items():
                inputName = row["ID"] + key
                newValue = request.form[inputName]
                
        # neu einlesen
        local_views_and_data = load_data_from_db()
    else:
        local_views_and_data = views_and_data

    found_in_current_view = True

    if search == last_search:
        found_views_and_data = last_found_views_and_data
        view = last_view

    else:  # Suchen

        last_search = search

        found_views_and_data = {}
        found_view_name = ""
        found_key = ""
        all_search_words = search_words
        for view_name, view in local_views_and_data.items():
            found_in_view = False
            view["data_found"] = []

            if len(search_words) != 0:
                # mit Suche am Wortanfang deaktiviert (12.10.) if re.compile(r"\b" + all_search_words[0]).search(str(view_name).lower()):
                if re.compile(all_search_words[0]).search(str(view_name).lower()):
                    found_view_name = view_name
                    search_words = all_search_words[1:]
                for key, value in view["data"][0].items():
                    # mit Suche am Wortanfang deaktiviert (12.10.) if re.compile(r"\b" + all_search_words[0]).search(str(key).lower()):
                    if re.compile(all_search_words[0]).search(str(key).lower()):
                        found_key = key
                        search_words = all_search_words[1:]

            for item in view["data"]:
                found = False
                search_in = ""
                for key, value in item.items():

                    if found_view_name == "" and found_key == "" or found_view_name == view_name or found_key == key:
                        search_in += " " + str(value)
                        try:
                            # Suche in Beziehung
                            foreign_view = relations[view_name][key]
                            foreign_data = local_views_and_data[foreign_view]["data"]
                            for d in foreign_data:
                                if d["ID"] == value:
                                    search_in += " " + str(d["Name"])
                                    break
                        except KeyError:
                            pass

                    # mit Suche am Wortanfang deaktiviert (12.10.) if all(re.compile(r"\b" + word).search(str(search_in).lower()) for word in search_words):
                    if all(re.compile(word).search(str(search_in).lower()) for word in search_words):
                        # Wenn alle Wörter im Wert gefunden werden, füge das Element zur Ergebnisliste hinzu
                        view["data_found"].append(item)
                        found = True
                        found_in_view = True
                        break

                if not found:
                    # Wenn das Element oder seine Beziehungstabellen nicht alle Wörter enthalten, überspringen Sie das Element
                    continue
            if found_in_view:
                found_views_and_data[view_name] = view
                if view_name == current_view_name:
                    found_in_current_view = True

    if len(found_views_and_data) == 0:
        found_views_and_data = local_views_and_data
    else:
        if found_in_current_view == False:
            for view_name, view in found_views_and_data.items():
                current_view_name = view_name
                break

        last_view_name = current_view_name
    last_found_views_and_data = found_views_and_data
    last_view = views[current_view_name]

    columnsWidth = {}
    for key, value in views[current_view_name]["columns"].items():
        columnsWidth[key] = 50
        # columnsWidth[column_name] = config["columnsWidth"][column_name]

    return render_template("index.html", view_name=current_view_name, relations=views[current_view_name]["relations"], views=found_views_and_data, columnsWidth=columnsWidth, search=search)


if __name__ == "__main__":
    app.run(debug=True)
