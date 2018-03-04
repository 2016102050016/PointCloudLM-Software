import serial
import matplotlib.pyplot as plt
import numpy as np
import time

def open_port():
    ser = serial.Serial('COM12', 38400)

    return ser

def close_port(port):
    port.close()

def detect_data(port):
    #port.reset_input_buffer()
    flag = True

    while flag:
        anuncio = port.read(1)
        anuncio = ord(anuncio[0]) # convertir en entero

        if (anuncio & 0xf0)  == 0xf0:# Se detecta el byte de anuncio de trama
                n_canales = anuncio & 0x0f # Numero de canales a leer
                return  n_canales

def main():
    port = open_port()
    i = 0.00
    y = 0.00
    Amplitud_matrix = np.array([])
    Time_matrix = np.array([])
    T_Inicio = time.time()
    T_Final = time.time()
    Dif = T_Final-T_Inicio
    while(Dif < 15):  # Contar 10 segundos
        n_canales = detect_data(port)
        data_in = port.read(2*n_canales)
        canal_n1 = (2**7)*ord(data_in[0])+ord(data_in[1])
        y = canal_n1*3.2/(2**12-1) # Escalamiento
        Amplitud_matrix = np.append(Amplitud_matrix, [y])
        T_Final = time.time()
        Dif = T_Final - T_Inicio

    close_port(port)
    np.savetxt('test1.out', Amplitud_matrix, fmt='%1.6e')
    s = np.loadtxt('test1.out')
    plt.hist(s, bins='auto')
    plt.title("Histogramas del Infrarrojo")
    plt.show()


if __name__ == "__main__": main()