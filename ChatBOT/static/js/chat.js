function appendMessage(sender, text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message " + sender;

    const bubble = document.createElement("div");
    bubble.className = "text";
    bubble.innerHTML = text;

    msgDiv.appendChild(bubble);
    chatBox.appendChild(msgDiv);

    // Se c'è un percorso immagine, lo mostriamo come immagine (es. output/charts/abc.png)
    const imageRegex = /(output\/charts\/\S+\.png)/;
    const match = text.match(imageRegex);
    if (match) {
        const img = document.createElement("img");
        img.src = match[1];
        img.className = "image-response";
        chatBox.appendChild(img);
    }

    chatBox.scrollTop = chatBox.scrollHeight;
}
