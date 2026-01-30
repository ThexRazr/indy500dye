from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev"

@app.get("/")
def home():
    return render_template("home.html")

@app.get("/track")
def track():
    return render_template("track.html")

@app.get("/guide")
def guide():
    return render_template("guide.html")

@app.get("/guide/overview")
def overview():
    return render_template("overview.html")

@app.get("/track/control")
def control():
    field = session.get("field") # keep field size from form
    return render_template("control.html", field=field)

# "post" ran when form submission, use length/width in backend
@app.post("/track/control")
def field_submit():
    length = request.form.get("fieldLength")
    width = request.form.get("fieldWidth")
    session["field"] = {"length": length, "width": width}
    return redirect(url_for("control"))

if __name__ == "__main__":
    app.run(debug=True)