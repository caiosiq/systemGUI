import time
import matplotlib.pyplot as plt

class graph:
    def __init__(self, temperature_dict, pressure_dict, balance_dict, flow_rate_dict):
        self.temperature_dict = temperature_dict
        self.pressure_dict = pressure_dict
        self.balance_dict = balance_dict
        self.flow_rate_dict = flow_rate_dict
        self.data_dicts = [('Temperature', self.temperature_dict),('Pressure', self.pressure_dict),
                        ('Balance', self.balance_dict),('Flow Rate', self.flow_rate_dict)]
        self.color_map = {}

        self.gui_plot_stopped = False

    def big_checkmark(self, dict_type):
        #remove all little checkmarks within
        d = self.get_dict_type(dict_type)

        if d:
            for name in d:
                d[name][0] = not d[name][0]

    def plot(self, plots, canvas):
        while not self.gui_plot_stopped:
            for p in plots:
                p.clear()
                
            plots[0].set_title('Temperature Over Time')
            plots[0].set_xlabel('Time (s)')
            plots[0].set_ylabel('Temperature (°C)')

            plots[1].set_title('Pressure Over Time')
            plots[1].set_xlabel('Time (s)')
            plots[1].set_ylabel('Pressure (psi)')

            plots[2].set_title('Balance Over Time')
            plots[2].set_xlabel('Time (s)')
            plots[2].set_ylabel('Balance (g)')

            plots[3].set_title('Flow Rate Over Time')
            plots[3].set_xlabel('Time (s)')
            plots[3].set_ylabel('Flow Rate (mL/min)')

            for label, data_dict in self.data_dicts:
                plotted = False
                p_idx = {'Temperature': 0, 'Pressure': 1, 'Balance': 2, 'Flow Rate': 3}[label]
                p = plots[p_idx]
                for name, var_value in data_dict.items():
                    if var_value[0] and var_value[1]:
                        times = [t for t, v in var_value[2]]
                        values = [v for t, v in var_value[2]]

                        if name not in self.color_map:
                            self.color_map[name] = plt.get_cmap("tab10")(len(self.color_map) % 10)

                        p.plot(times, values, label=f'{label}: {name}', color=self.color_map[name])
                        plotted = True

                if plotted:
                    p.legend()  # Add legend for each specific plot
            canvas.draw()
            time.sleep(.5)

    def update_dict(self, dict_type, name, value):
        d = self.get_dict_type(dict_type)
        if d and d[name][0] and d[name][1]:
            d[name][2].append((time.perf_counter(),value))

    def checkmark(self, dict_type, name):
        d = self.get_dict_type(dict_type)

        if d and d[name][0]:
            if d[name][1]:  # If currently checked, uncheck and insert None to create a gap
                d[name][2].append((None, None))
            d[name][1] = not d[name][1]

    def get_dict_type(self, dict_type):
        return getattr(self, f"{dict_type.lower()}_dict", None)

    def gui_plot_stop(self, boolean):
        self.gui_plot_stopped = boolean