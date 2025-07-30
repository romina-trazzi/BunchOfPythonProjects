document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const chatBox = document.getElementById("chat-box");
    const loading = document.getElementById("loading");

    if (!form || !input || !chatBox || !loading) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const message = input.value.trim();
        if (!message) return;

        appendMessage("user", message);
        input.value = "";
        toggleLoading(true);

        try {
            const res = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message })
            });
            const data = await res.json();
            appendMessage("bot", data.response);
        } catch (err) {
            appendMessage("bot", "❌ Errore nella richiesta.");
        } finally {
            toggleLoading(false);
        }
    });

    function appendMessage(sender, text) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message " + sender;

        const bubble = document.createElement("div");
        bubble.className = "text";
        bubble.innerHTML = text;

        msgDiv.appendChild(bubble);
        chatBox.appendChild(msgDiv);

        // Mostra immagine se presente nel testo
        const imageRegex = /(output\/charts\/\S+\.png)/;
        const match = text.match(imageRegex);
        if (match) {
            const img = document.createElement("img");
            img.src = "/" + match[1];
            img.className = "image-response";
            chatBox.appendChild(img);
        }

        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function toggleLoading(show) {
        input.disabled = show;
        loading.classList.toggle("d-none", !show);
        document.body.style.cursor = show ? "wait" : "default";
    }
});