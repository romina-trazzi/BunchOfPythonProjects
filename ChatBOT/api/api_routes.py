from flask import Blueprint, request, jsonify
from controller.chat_controller import handle_user_message

api_blueprint = Blueprint("api", __name__)

@api_blueprint.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        message = data.get("message") if data else None
        if not message:
            return jsonify({"response": "Messaggio non valido."})

        response = handle_user_message(message)
        return jsonify({"response": response})


    except Exception as e:
        return jsonify({"response": f"Errore interno: {str(e)}"}), 500