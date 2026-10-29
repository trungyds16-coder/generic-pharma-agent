import matplotlib.pyplot as plt
import numpy as np

def plot_integral(func, start, end, resolution=1000):
    x = np.linspace(start, end, resolution)
    y = func(x)
    plt.plot(x, y, label='f(x)')
    plt.fill_between(x, y, where=(y >= 0), color='blue', alpha=0.3)
    plt.fill_between(x, y, where=(y < 0), color='red', alpha=0.3)
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('Graph of the function and its integral')
    plt.legend()
    plt.grid(True)
    plt.show()
