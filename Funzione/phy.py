import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# Funzione obiettivo
def Y(phi):
    return (phi - 3)**2

# Derivata (gradiente)
def gradient(phi):
    return 2 * (phi - 3)

# Gradient Descent (ritorna tutti i phi)
def gradient_descent(phi_0, eta, steps):
    phi_values = [phi_0]
    for _ in range(steps):
        phi_new = phi_values[-1] - eta * gradient(phi_values[-1])
        phi_values.append(phi_new)
    return phi_values

# Parametri iniziali
phi_0 = 0
eta = 0.1
steps = 20

# Calcola la traiettoria
phi_vals = gradient_descent(phi_0, eta, steps)
y_vals = [Y(phi) for phi in phi_vals]

# Setup per la figura
fig, ax = plt.subplots()
x = np.linspace(-1, 5, 200)
y = Y(x)
ax.plot(x, y, label="Y(φ) = (φ - 3)^2")
point, = ax.plot([], [], 'ro')  # punto rosso
text = ax.text(0.02, 0.95, '', transform=ax.transAxes)

ax.set_xlim(-1, 5)
ax.set_ylim(0, max(y_vals)*1.1)
ax.set_xlabel("φ")
ax.set_ylabel("Y(φ)")
ax.set_title("Gradient Descent (Animazione)")

# Inizializzazione dell'animazione
def init():
    point.set_data([], [])
    text.set_text('')
    return point, text

# Aggiornamento per ogni frame
def update(frame):
    phi = phi_vals[frame]
    y = Y(phi)
    point.set_data([phi], [y])  
    text.set_text(f'Step {frame}: φ = {phi:.3f}')
    return point, text

ani = animation.FuncAnimation(
    fig, update, frames=len(phi_vals),
    init_func=init, blit=True, interval=500, repeat=False
)

plt.legend()
plt.grid(True)
plt.show()

# Salva l'animazione in formato .gif
ani.save("gradient_descent.gif", writer="pillow", fps=2)