import time
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, MinuteLocator
import datetime
import numpy as np
from collections import deque

class Graph:
    def __init__(self, temperature_dict, pressure_dict, balance_dict, flow_rate_dict, 
                 max_points=1000, update_interval=0.5):
        """
        Enhanced graph utility for real-time data visualization.
        
        Args:
            temperature_dict: Dictionary of temperature data series
            pressure_dict: Dictionary of pressure data series
            balance_dict: Dictionary of balance data series  
            flow_rate_dict: Dictionary of flow rate data series
            max_points: Maximum number of data points to keep per series (default: 1000)
            update_interval: Time between plot updates in seconds (default: 0.5)
        """
        self.temperature_dict = temperature_dict
        self.pressure_dict = pressure_dict
        self.balance_dict = balance_dict
        self.flow_rate_dict = flow_rate_dict
        
        self.data_dicts = [
            ('Temperature', self.temperature_dict),
            ('Pressure', self.pressure_dict),
            ('Balance', self.balance_dict),
            ('Flow Rate', self.flow_rate_dict)
        ]
        
        # Dictionary mapping plot types to their properties
        self.plot_properties = {
            'Temperature': {'index': 0, 'ylabel': 'Temperature (°C)', 'color_map': 'inferno'},
            'Pressure': {'index': 1, 'ylabel': 'Pressure (psi)', 'color_map': 'viridis'},
            'Balance': {'index': 2, 'ylabel': 'Balance (g)', 'color_map': 'cividis'},
            'Flow Rate': {'index': 3, 'ylabel': 'Flow Rate (mL/min)', 'color_map': 'plasma'}
        }
        
        self.color_map = {}
        self.gui_plot_stopped = False
        self.max_points = max_points
        self.update_interval = update_interval
        self.last_update_time = time.time()
        
        # For tracking min/max values for each plot type
        self.value_ranges = {
            'Temperature': {'min': float('inf'), 'max': float('-inf')},
            'Pressure': {'min': float('inf'), 'max': float('-inf')},
            'Balance': {'min': float('inf'), 'max': float('-inf')},
            'Flow Rate': {'min': float('inf'), 'max': float('-inf')}
        }
        
        # For tracking time window
        self.start_time = None
        self.time_window = 120  # Default to showing 2 minutes of data
        
        # Statistics storage
        self.statistics = {}

    def toggle_all_series(self, dict_type):
        """
        Toggle visibility of all data series in a specific category.
        
        Args:
            dict_type: Type of dictionary to toggle ('temperature', 'pressure', etc.)
        """
        d = self.get_dict_type(dict_type)
        if d:
            # Check if all are currently on or off
            all_on = all(d[name][0] for name in d)
            
            # Toggle all to the opposite state
            for name in d:
                d[name][0] = not all_on

    def plot(self, plots, canvas, fig=None):
        """
        Main plotting function - continuously updates plots with new data.
        
        Args:
            plots: List of matplotlib subplot axes
            canvas: Canvas to draw on
            fig: Figure object (optional)
        """
        if self.start_time is None:
            self.start_time = time.time()
            
        while not self.gui_plot_stopped:
            current_time = time.time()
            
            # Update plots at specified interval to reduce CPU usage
            if (current_time - self.last_update_time) < self.update_interval:
                time.sleep(0.05)  # Small sleep to prevent CPU hogging
                continue
                
            self.last_update_time = current_time
            
            # Clear plots but maintain settings
            for p in plots:
                p.clear()
            
            # Set up plots
            for label, properties in self.plot_properties.items():
                idx = properties['index']
                plots[idx].set_title(f'{label} Over Time')
                plots[idx].set_xlabel('Time (s)')
                plots[idx].set_ylabel(properties['ylabel'])
                plots[idx].grid(True, linestyle='--', alpha=0.7)
            
            # Plot data series
            for label, data_dict in self.data_dicts:
                plotted = False
                p_idx = self.plot_properties[label]['index']
                p = plots[p_idx]
                
                for name, var_value in data_dict.items():
                    if var_value[0] and var_value[1] and len(var_value[2]) > 0:
                        # Filter out None values and limit to max points
                        valid_data = [(t, v) for t, v in var_value[2][-self.max_points:] if t is not None and v is not None]
                        
                        if valid_data:
                            times = [(t - self.start_time) for t, v in valid_data]  # Relative time in seconds
                            values = [v for t, v in valid_data]
                            
                            # Update min/max values for auto-scaling
                            if values:
                                self.value_ranges[label]['min'] = min(self.value_ranges[label]['min'], min(values))
                                self.value_ranges[label]['max'] = max(self.value_ranges[label]['max'], max(values))
                            
                            # Assign consistent colors to each series
                            if name not in self.color_map:
                                cmap = plt.get_cmap(self.plot_properties[label]['color_map'])
                                self.color_map[name] = cmap(hash(name) % 10 / 10.0)
                            
                            line, = p.plot(times, values, label=f'{name}', color=self.color_map[name], 
                                          linewidth=2, marker='o', markersize=2, alpha=0.8)
                            
                            # Add annotation for the latest value if there are values
                            if values:
                                latest_idx = len(values) - 1
                                latest_value = values[latest_idx]
                                latest_time = times[latest_idx]
                                p.annotate(f'{latest_value:.2f}', 
                                          xy=(latest_time, latest_value),
                                          xytext=(4, 4), 
                                          textcoords='offset points',
                                          fontsize=8)
                            
                            # Calculate statistics for this series
                            if values:
                                self.statistics[f"{label}_{name}"] = {
                                    'mean': np.mean(values),
                                    'min': min(values),
                                    'max': max(values),
                                    'std': np.std(values) if len(values) > 1 else 0
                                }
                            
                            plotted = True
                
                if plotted:
                    # Add stats to the plot
                    stats_text = ""
                    for series_name, stats in self.statistics.items():
                        if series_name.startswith(label):
                            name = series_name.split('_', 1)[1]
                            stats_text += f"{name}: avg={stats['mean']:.2f}, min={stats['min']:.2f}, max={stats['max']:.2f}\n"
                    
                    if stats_text:
                        p.text(0.02, 0.98, stats_text.strip(), transform=p.transAxes,
                               fontsize=8, verticalalignment='top', 
                               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
                    
                    # Set better y limits with padding
                    if self.value_ranges[label]['min'] != float('inf'):
                        data_range = self.value_ranges[label]['max'] - self.value_ranges[label]['min']
                        padding = max(0.1 * data_range, 0.1)  # At least 0.1 unit padding
                        p.set_ylim(
                            self.value_ranges[label]['min'] - padding,
                            self.value_ranges[label]['max'] + padding
                        )
                    
                    p.legend(loc='upper right', fontsize=8)
            
            # Adjust the time window - dynamic based on available data
            latest_times = []
            for label, data_dict in self.data_dicts:
                for name, var_value in data_dict.items():
                    if var_value[0] and var_value[1] and var_value[2]:
                        valid_times = [t for t, v in var_value[2] if t is not None]
                        if valid_times:
                            latest_times.append(max(valid_times))
            
            if latest_times:
                latest_time = max(latest_times)
                time_range = latest_time - self.start_time
                
                # Update all x-axes to show the same time range
                for p in plots:
                    # Show at most the last time_window seconds of data
                    if time_range > self.time_window:
                        p.set_xlim(time_range - self.time_window, time_range + 2)
                    else:
                        p.set_xlim(0, max(time_range + 2, self.time_window))
            
            # Make plots look good
            if fig:
                fig.tight_layout()
            
            # Draw the canvas
            canvas.draw()
            
            # Small sleep to prevent CPU hogging
            time.sleep(0.05)

    def update_dict(self, dict_type, name, value):
        """
        Add a new data point to the specified dictionary.
        
        Args:
            dict_type: Type of dictionary to update
            name: Name of the data series
            value: New data value
        """
        d = self.get_dict_type(dict_type)
        if d and name in d and d[name][0] and d[name][1]:
            # If we've reached max points, use a deque-like behavior
            if len(d[name][2]) >= self.max_points:
                d[name][2] = d[name][2][-(self.max_points-1):] + [(time.time(), value)]
            else:
                d[name][2].append((time.time(), value))

    def toggle_series(self, dict_type, name, is_visible=None):
        """
        Set the visibility of a specific data series.
        
        Args:
            dict_type: Type of dictionary containing the series
            name: Name of the data series to toggle
            is_visible: If provided, set to this visibility state; if None, toggle current state
        """
        d = self.get_dict_type(dict_type)
        if d and name in d:
            # If is_visible is provided, set to that state
            if is_visible is not None:
                # If turning off, add a discontinuity marker
                if d[name][1] and not is_visible:
                    d[name][2].append((None, None))
                d[name][1] = is_visible
            # Otherwise toggle current state
            else:
                # If turning off, add a discontinuity marker
                if d[name][1]:
                    d[name][2].append((None, None))
                d[name][1] = not d[name][1]
                
    def set_all_series(self, dict_type, is_visible):
        """
        Set visibility for all series in a dictionary.
        
        Args:
            dict_type: Type of dictionary to update
            is_visible: Boolean visibility state to set
        """
        d = self.get_dict_type(dict_type)
        if d:
            for name in d:
                # If turning off and currently visible, add discontinuity marker
                if d[name][1] and not is_visible:
                    d[name][2].append((None, None))
                d[name][1] = is_visible

    def get_dict_type(self, dict_type):
        """
        Get the dictionary corresponding to the specified type.
        
        Args:
            dict_type: Type of dictionary to get ('temperature', 'pressure', etc.)
            
        Returns:
            Dictionary object or None if not found
        """
        return getattr(self, f"{dict_type.lower()}_dict", None)

    def set_time_window(self, seconds):
        """
        Set the time window to display (in seconds).
        
        Args:
            seconds: Number of seconds to display
        """
        self.time_window = seconds

    def export_data(self, filename=None):
        """
        Export all current data to a CSV file.
        
        Args:
            filename: Output filename (default: "system2_data_YYYY-MM-DD_HH-MM-SS.csv")
        """
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"system2_data_{timestamp}.csv"
        
        with open(filename, 'w') as f:
            # Write header
            header = ["Timestamp"]
            for label, data_dict in self.data_dicts:
                for name in data_dict:
                    header.append(f"{label}_{name}")
            f.write(",".join(header) + "\n")
            
            # Collect all timestamps
            all_timestamps = set()
            for label, data_dict in self.data_dicts:
                for name, var_value in data_dict.items():
                    if var_value[0] and var_value[1]:
                        all_timestamps.update([t for t, v in var_value[2] if t is not None])
            
            all_timestamps = sorted(all_timestamps)
            
            # Write data rows
            for ts in all_timestamps:
                row = [str(ts)]
                for label, data_dict in self.data_dicts:
                    for name, var_value in data_dict.items():
                        # Find the value at this timestamp or closest before it
                        value = None
                        if var_value[0] and var_value[1]:
                            for t, v in var_value[2]:
                                if t == ts:
                                    value = v
                                    break
                        row.append(str(value) if value is not None else "")
                
                f.write(",".join(row) + "\n")
        
        return filename

    def clear_data(self, dict_type=None, name=None):
        """
        Clear data points for a specific series or all series.
        
        Args:
            dict_type: Type of dictionary to clear (if None, clear all)
            name: Name of the series to clear (if None, clear all in dict_type)
        """
        if dict_type is None:
            # Clear all data
            for label, data_dict in self.data_dicts:
                for name in data_dict:
                    data_dict[name][2] = []
            # Reset value ranges
            for plot_type in self.value_ranges:
                self.value_ranges[plot_type] = {'min': float('inf'), 'max': float('-inf')}
            # Reset statistics
            self.statistics = {}
            
        elif name is None:
            # Clear all data in the specified dictionary
            d = self.get_dict_type(dict_type)
            if d:
                for name in d:
                    d[name][2] = []
                # Reset value range for this type
                plot_type = dict_type.capitalize()
                self.value_ranges[plot_type] = {'min': float('inf'), 'max': float('-inf')}
                # Reset statistics for this type
                self.statistics = {k: v for k, v in self.statistics.items() 
                                  if not k.startswith(plot_type)}
        else:
            # Clear only the specified series
            d = self.get_dict_type(dict_type)
            if d and name in d:
                d[name][2] = []
                # We'll recalculate min/max on next update
                # Remove statistics for this series
                series_key = f"{dict_type.capitalize()}_{name}"
                if series_key in self.statistics:
                    del self.statistics[series_key]

    def stop_plotting(self, stop=True):
        """
        Stop or resume the plotting loop.
        
        Args:
            stop: True to stop plotting, False to resume
        """
        self.gui_plot_stopped = stop