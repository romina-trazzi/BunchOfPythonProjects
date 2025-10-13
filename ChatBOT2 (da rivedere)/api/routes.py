from flask import Blueprint, request, jsonify
from controller.chat_controller import handle_user_message

api_blueprint = Blueprint("api", __name__)

@api_blueprint.route("/chat", methods=["POST"])
def chat():
    message = request.json.get("message", "")
    response = handle_user_message(message)
    return jsonify({"response": response})
