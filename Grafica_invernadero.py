import matplotlib.pyplot as plt 
import math

# Definir patrones para el análisis
patterns = {
    'Pattern 1': {'ON': 25, 'OFF': 75},
    'Pattern 2': {'ON': 50, 'OFF': 50},
    'Pattern 3': {'ON': 75, 'OFF': 25}
}

# Función para calcular SDM
def calculate_SDM(voltage):
    offset = 1.3904
    SDM = (voltage - offset) ** 2
    return SDM

# Función para recortar valores del SDM
def crop_sdm(sdm_values, logic_states):
    cropped_sdm = []
    for i in range(len(sdm_values)):
        if i < 5:
            cropped_sdm.append(sdm_values[i])
        elif logic_states[i] == 0:
            cropped_sdm.append(0)
        else:
            max_last_5 = max(sdm_values[i-5:i])
            if sdm_values[i] < 0.5 * max_last_5:
                cropped_sdm.append(0.7 * max_last_5)
            else:
                cropped_sdm.append(sdm_values[i])
    return cropped_sdm

# Función para calcular SumProd y clasificar los valores lógicos
def sum_prod_logic(sdm_values, cropped_values):
    sum_prod_values = []
    for i in range(len(sdm_values)):
        if i < 4:
            sum_prod_values.append(0)
        else:
            sum_prod = sum(sdm_values[i-4+j] * cropped_values[i-4+j] * 1400 for j in range(4))
            sum_prod_values.append(sum_prod)
    return sum_prod_values

# Nueva función para desactivar SDM Crop en caso de cero lógico
def detect_zero_logic(sdm_values):
    zero_logic_states = []
    for i in range(len(sdm_values)):
        if i < 8:
            zero_logic_states.append(1)
        else:
            sum_last_8 = sum(sdm_values[i-8:i])
            if sum_last_8 * 100 < 0.5:
                zero_logic_states.append(0)
            else:
                zero_logic_states.append(1)
    return zero_logic_states

# Función para calcular los valores lógicos ON/OFF usando SumProd
def on_off_logic(sum_prod_values):
    on_off_states = []
    for value in sum_prod_values:
        on_off_states.append(0 if value < 0.1 else 1)
    return on_off_states

# Función para calcular los tiempos entre estados ON y OFF
def calculate_on_off_durations(on_off_states, times):
    durations = []
    last_change_time = None
    current_state = None
    
    for i in range(len(on_off_states)):
        if current_state is None or on_off_states[i] != current_state:
            # Detectar un cambio de estado
            if last_change_time is not None:
                # Calcular la duración entre estados
                durations.append((current_state, times[i] - last_change_time))
            # Actualizar el estado y tiempo del último cambio
            current_state = on_off_states[i]
            last_change_time = times[i]
    
    return durations

# Función para calcular el BER basado en patrones
def detect_patterns_and_calculate_ber(on_off_durations, patterns):
    total_bits = len(on_off_durations)
    correct_bits = 0
    incorrect_bits = 0

    # Detectar patrones y verificar si son correctos
    for state, duration in on_off_durations:
        for pattern_name, pattern_values in patterns.items():
            if state == 1 and abs(duration - pattern_values['ON']) < 10:  # Margen de tolerancia
                correct_bits += 1
                break
            elif state == 0 and abs(duration - pattern_values['OFF']) < 10:
                correct_bits += 1
                break
        else:
            # Si no se encontró un patrón correcto, contar como bit erróneo
            incorrect_bits += 1

    # Calcular el BER
    ber = incorrect_bits / total_bits if total_bits > 0 else 0

    # Calcular BER en escala logarítmica
    if ber > 0:
        ber_log = math.log10(ber)
    else:
        ber_log = float('-inf')  # Representa BER logarítmico muy bajo

    return ber, ber_log, correct_bits, incorrect_bits

# Función para graficar una sola etapa
def plot_stage(x, y, label, xlabel, ylabel, title, color='b', step_plot=False):
    plt.figure(figsize=(10, 6))
    if step_plot:
        plt.step(x, y, label=label, color=color, where='post')
    else:
        plt.plot(x, y, label=label, color=color)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.show()

# Leer datos del archivo con validación
def read_data(file_path):
    voltages = []
    times = []
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split(",")
            if len(parts) < 2:
                continue
            try:
                time = int(parts[0].strip())
                voltage = float(parts[1].strip())
                if time > 1e6 or time < 0:
                    print(f"Dato corrupto ignorado (tiempo): {line.strip()}")
                    continue
                times.append(time)
                voltages.append(voltage)
            except ValueError as e:
                print(f"Dato corrupto ignorado (formato inválido): {line.strip()}")
                continue
    return times, voltages

# Leer datos y calcular resultados
file_path = "Datos Invernadero/Humedad_30%_Temperatura_35°/Lectura_130cm.txt"
times, voltages = read_data(file_path)

# # Limitar a los primeros 30000 datos
times = times[30000:60000]
voltages = voltages[30000:60000]

# Calcular SDM para los voltajes
sdm_values = [calculate_SDM(v) for v in voltages]

# Detectar estados lógicos cero basados en la nueva condición
zero_logic_states = detect_zero_logic(sdm_values)

# Aplicar el recorte a los valores de SDM considerando los estados lógicos cero
smoothed_crop = crop_sdm(sdm_values, zero_logic_states)

# Calcular SumProd para los valores de SDM y SDM Crop
logic_states = sum_prod_logic(sdm_values, smoothed_crop)

# Calcular los valores ON/OFF usando SumProd
on_off_states = on_off_logic(logic_states)

# Calcular tiempos acumulados para los datos
time = []
actual_time = 0
for t in times:
    actual_time += t
    time.append(actual_time)
    

# Calcular las duraciones entre estados ON y OFF
on_off_durations = calculate_on_off_durations(on_off_states, times)

# Imprimir las duraciones calculadas
for state, duration in on_off_durations:
    print(f"Estado: {'ON' if state == 1 else 'OFF'}, Duración: {duration} ms")

# Detectar patrones y calcular BER
ber, ber_log, correct_bits, incorrect_bits = detect_patterns_and_calculate_ber(on_off_durations, patterns)

# Imprimir resultados del análisis
print(f"Total Bits Analizados: {len(on_off_durations)}")
print(f"Bits Correctos: {correct_bits}")
print(f"Bits Erróneos: {incorrect_bits}")
print(f"Bit Error Rate (BER): {ber:.4f}")
print(f"BER en escala logarítmica (log10): {ber_log:.4f}")

# Graficar los resultados
plt.figure(figsize=(14, 12))

# Gráfica de voltajes originales
plt.subplot(4, 1, 1)
plt.plot(time, voltages, label='Voltage', color='b')
plt.xlabel('Time (ms)')
plt.ylabel('Voltage (V)')
plt.title('Voltage vs Time (First 30000 Data Points)')
plt.legend()
plt.grid(True)

# Gráfica de SDM original
plt.subplot(4, 1, 2)
plt.plot(time, sdm_values, label='SDM', color='orange')
plt.xlabel('Time (ms)')
plt.ylabel('SDM')
plt.title('SDM vs Time')
plt.legend()
plt.grid(True)

# Gráfica de SDM recortado
plt.subplot(4, 1, 3)
plt.plot(time, smoothed_crop, label='SDM (Cropped)', color='r')
plt.xlabel('Time (ms)')
plt.ylabel('SDM (Smoothed & Cropped)')
plt.title('SDM Smoothed vs Time (Considering Zero Logic States)')
plt.legend()
plt.grid(True)

# Gráfica de estados ON/OFF
plt.subplot(4, 1, 4)
plt.step(time, on_off_states, label='ON/OFF States', color='g', where='post')
plt.xlabel('Time (ms)')
plt.ylabel('Logic State')
plt.title('ON/OFF Logic States vs Time')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()
