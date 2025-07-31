import React, { useState, useRef } from 'react';

function App() {
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [details, setDetails] = useState(null); // 🆕 Aggiunto stato per il report tecnico
  const canvasRef = useRef();

  function handleDrop(event) {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = () => setImage(reader.result);
      reader.readAsDataURL(file);
    }
  }

  function allowDrop(event) {
    event.preventDefault();
  }

  function getAverageColor(ctx, width, height) {
    const imageData = ctx.getImageData(0, 0, width, height);
    const data = imageData.data;
    let r = 0, g = 0, b = 0;
    let pixelCount = 0;

    for (let i = 0; i < data.length; i += 4) {
      const alpha = data[i + 3];
      if (alpha > 0) { // 🆕 Esclude pixel trasparenti
        r += data[i];
        g += data[i + 1];
        b += data[i + 2];
        pixelCount++;
      }
    }

    return {
      r: Math.round(r / pixelCount),
      g: Math.round(g / pixelCount),
      b: Math.round(b / pixelCount),
    };
  }

  // 🆕 Migliorata funzione: ora considera anche bounding box dell’oggetto
  function getShapeRatio(ctx, width, height) {
    const imageData = ctx.getImageData(0, 0, width, height);
    const data = imageData.data;
    let minX = width, maxX = 0, minY = height, maxY = 0;

    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const i = (y * width + x) * 4;
        const alpha = data[i + 3];
        if (alpha > 20) {
          if (x < minX) minX = x;
          if (x > maxX) maxX = x;
          if (y < minY) minY = y;
          if (y > maxY) maxY = y;
        }
      }
    }

    const objectWidth = maxX - minX;
    const objectHeight = maxY - minY;
    const aspect = objectWidth / objectHeight;

    if (aspect < 0.9 || aspect > 1.1) return "curved";
    return "round";
  }

  function classify(color, shape) {
    const { r, g, b } = color;
    const total = r + g + b;
    const redRatio = r / total;
    const greenRatio = g / total;
    const blueRatio = b / total;

    let colorGuess = "mixed";
    if (redRatio > 0.38 && greenRatio < 0.35) colorGuess = "red";
    else if (greenRatio > 0.38 && redRatio < 0.35) colorGuess = "yellow";

    let guess = "🍓 Frutto sconosciuto";
    let confidence = Math.max(redRatio, greenRatio) * 100;

    if (colorGuess === "red" && shape === "round") {
      guess = "🍎 Mela";
    } else if (colorGuess === "yellow" && shape === "curved") {
      guess = "🍌 Banana";
    } else if (colorGuess === "red") {
      guess = "🍎 Mela (forma incerta)";
    } else if (colorGuess === "yellow") {
      guess = "🍌 Banana (forma incerta)";
    }

    // 🆕 Report tecnico
    setDetails({ r, g, b, redRatio, greenRatio, blueRatio, shape });

    return `${guess} - Confidenza colore: ${confidence.toFixed(2)}% (colore: ${colorGuess}, forma: ${shape})`;
  }

  function classifyImage() {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      canvas.width = 100;
      canvas.height = 100;
      ctx.drawImage(img, 0, 0, 100, 100);

      const color = getAverageColor(ctx, 100, 100);
      const shape = getShapeRatio(ctx, 100, 100); // 🆕 passaggio corretto del contesto

      const finalResult = classify(color, shape);
      setResult(finalResult);
    };
    img.src = image;
  }

  return (
    <div style={{ padding: '2rem', fontFamily: 'Arial' }}>
      <h1>🍎🍌 Classificatore Colore + Forma (Senza Librerie)</h1>

      <div
        onDrop={handleDrop}
        onDragOver={allowDrop}
        style={{
          border: '2px dashed gray',
          height: '200px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginTop: '2rem',
          cursor: 'pointer',
        }}
      >
        <p>Trascina qui un'immagine</p>
      </div>

      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {image && (
        <div style={{ marginTop: '2rem', textAlign: 'center' }}>
          <img
            src={image}
            alt="Preview"
            style={{
              maxWidth: '300px',
              borderRadius: '8px',
              boxShadow: '0 0 10px #ccc',
            }}
          />
          <br />
          <button
            onClick={classifyImage}
            style={{ marginTop: '1rem', padding: '0.5rem 1rem' }}
          >
            Classifica immagine
          </button>
        </div>
      )}

      {result && (
        <div style={{ marginTop: '1rem', fontSize: '1.25rem', fontWeight: '600' }}>
          {result}
        </div>
      )}

      {/* 🆕 Dettagli tecnici */}
      {details && (
        <div style={{ marginTop: '1rem', fontSize: '0.9rem', color: '#555' }}>
          <p><strong>🔍 RGB medi:</strong> R {details.r}, G {details.g}, B {details.b}</p>
          <p><strong>🎨 Proporzioni:</strong> Rosso {(details.redRatio * 100).toFixed(1)}% | Verde {(details.greenRatio * 100).toFixed(1)}% | Blu {(details.blueRatio * 100).toFixed(1)}%</p>
          <p><strong>📐 Forma stimata:</strong> {details.shape}</p>
        </div>
      )}
    </div>
  );
}

export default App;