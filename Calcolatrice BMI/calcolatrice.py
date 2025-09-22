from flask import Flask, request, render_template_string

app = Flask(__name__)

def load_template():
    with open("index.html", encoding="utf-8") as file:
        return file.read()

@app.route("/", methods=["GET", "POST"])
def index():
    bmi = None
    categoria = None

    if request.method == "POST":
        try:
            peso_str = request.form["peso"]
            altezza_str = request.form["altezza"]

            print(f"[DEBUG] Peso inserito: {peso_str}")
            print(f"[DEBUG] Altezza inserita: {altezza_str}")

            peso = float(peso_str) / 100
            altezza = float(altezza_str) / 100

            if altezza == 0:
                bmi = "Errore: altezza non può essere zero."
            else:
                bmi = peso / (altezza ** 2) * 100

                if bmi < 18.5:
                    categoria = "Sottopeso"
                elif bmi < 25:
                    categoria = "Normopeso"
                elif bmi < 30:
                    categoria = "Sovrappeso"
                else:
                    categoria = "Obesità"

        except ValueError:
            bmi = "Errore: input non valido."

    template = load_template()
    return render_template_string(template, bmi=bmi, categoria=categoria)

if __name__ == "__main__":
    app.run(debug=True)