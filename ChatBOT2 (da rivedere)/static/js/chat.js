document.getElementById("chat-form").addEventListener("submit", function(e) {
    e.preventDefault();
    const input = document.getElementById("chat-input");
    const message = input.value;
    input.value = "";

    appendMessage("Tu", message);

    fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
    })
    .then(res => res.json())
    .then(data => appendMessage("Bot", data.response))
    .catch(err => appendMessage("Bot", "Errore nella richiesta."));
});

function appendMessage(sender, text) {
    const chatBox = document.getElementById("chat-box");
    const message = document.createElement("div");
    message.innerHTML = `<strong>${sender}:</strong> ${text}`;
    chatBox.appendChild(message);
}
