# app.py
from flask import Flask, request, render_template, send_file
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from sklearn.cluster import KMeans
import os
from genera_dati import genera_dati

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    os.makedirs("static", exist_ok=True)
    gif_path = "static/kmeans.gif"
    k = int(request.form.get("k", 4))
    genera_dati("dati.csv")
    df = pd.read_csv("dati.csv")

    models = []
    for i in range(1, 11):
        kmeans = KMeans(n_clusters=k, init='random', n_init=1, max_iter=i, random_state=42)
        kmeans.fit(df[['x', 'y']])
        models.append((kmeans.labels_, kmeans.cluster_centers_))

    fig, ax = plt.subplots(figsize=(8, 6))

    def update(frame):
        ax.clear()
        labels, centers = models[frame]
        for j in range(k):
            cluster_points = df[labels == j]
            ax.scatter(cluster_points['x'], cluster_points['y'], s=10, label=f"Cluster {j}", alpha=0.6)
        ax.scatter(centers[:, 0], centers[:, 1], c='black', s=200, marker='X', label='Centroidi')
        ax.set_title(f"K-Means - Iterazione {frame + 1}")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.legend()

    anim = FuncAnimation(fig, update, frames=len(models), interval=1000)
    anim.save(gif_path, writer=PillowWriter(fps=1))

    return render_template("index.html", gif_url=gif_path, k=k)

if __name__ == "__main__":
    app.run(debug=True)