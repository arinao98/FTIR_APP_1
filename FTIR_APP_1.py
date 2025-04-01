# -*- coding: utf-8 -*-
"""
Created on Tue Apr  1 14:19:15 2025

@author: arina
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from io import BytesIO

# Initialize st.session_state.stored_results if it doesn't exist
if "stored_results" not in st.session_state:
    st.session_state.stored_results = []

peak_labels = {
    (3700, 3200): ("O-H", "blue"),
    (3500, 3200): ("N-H", "cyan"),
    (3300, 3250): ("≡C-H", "red"),
    (3100, 3000): ("=C-H", "purple"),
    (3000, 2850): ("C-H", "pink"),
    (2260, 2100): ("C≡C / C≡N", "orange"),
    (1750, 1680): ("C=O", "green"),
    (1680, 1620): ("C=C", "brown"),
    (1600, 1450): ("C=C (Ar)", "gray"),
    (1450, 1370): ("C-H", "gold"),
    (1300, 1000): ("C-O", "seagreen"),
    (900, 650): ("C-H (Ar)", "indigo"),
}

# Function to Plot FTIR Spectrum with peak labeling and create table
def plot_ftir(results_list):
    fig, ax = plt.subplots(figsize=(10, 6))
    peak_data = []  # List to store peak data for the table
    labeled_peaks = set() # Track labeled peaks to prevent overlap

    for file_name, results, color in results_list:
        wavenumber_col = next((col for col in results.columns if "cm" in col.lower()), None)
        intensity_col = next((col for col in results.columns if "%t" in col.lower() or "trans" in col.lower()), None)

        if wavenumber_col and intensity_col:
            try:
                x = pd.to_numeric(results[wavenumber_col], errors='coerce').dropna()
                y = pd.to_numeric(results[intensity_col], errors='coerce').dropna()

                if len(x) == 0 or len(y) == 0:
                    continue

                min_length = min(len(x), len(y))
                x, y = x.iloc[:min_length], y.iloc[:min_length]

                smooth_window = min(11, len(y)) if len(y) >= 11 else len(y) - 1
                if smooth_window % 2 == 0:
                    smooth_window += 1

                y_smooth = savgol_filter(y, window_length=smooth_window, polyorder=2)

                ax.plot(x, y_smooth, linestyle='-', color=color, label=file_name, linewidth=1)
                ax.set_xlabel("Wavenumber (cm⁻¹)")
                ax.set_ylabel("% Transmittance")
                ax.invert_xaxis()

                # Shade and label functional group regions and create table data
                for (start, end), (label, shade_color) in peak_labels.items():
                    # Only label major peaks (adjust threshold as needed)
                    if max(y_smooth[(x >= end) & (x <= start)]) < 90: # Only label peaks below 90% transmittance
                        ax.axvspan(end, start, color=shade_color, alpha=0.2)
                        x_pos = (start + end) / 2
                        y_pos = max(y_smooth[(x >= end) & (x <= start)]) * 1.05  # Position label above the peak

                        # Prevent overlapping labels
                        if not any(abs(x_pos - labeled_x) < 100 for labeled_x in labeled_peaks):
                            ax.text(x_pos, y_pos, label, fontsize=8, color=shade_color, ha="center")
                            labeled_peaks.add(x_pos) # Add position to labeled peaks
                            peak_data.append({"Wavenumber Range (cm⁻¹)" : f"{end}-{start}", "Functional Group": label})

            except Exception as e:
                st.warning(f"Error processing {file_name}: {e}")

    ax.legend(loc='lower left', fontsize=9, frameon=True)
    return fig, pd.DataFrame(peak_data) #Return both the figure and the table data.

# Upload files and process them
uploaded_files = st.file_uploader("Upload FTIR files", accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        try:
            results = pd.read_csv(uploaded_file)
            st.session_state.stored_results.append((uploaded_file.name, results, "black"))
        except Exception as e:
            st.warning(f"Error processing {uploaded_file.name}: {e}")

# Display FTIR Plot
st.subheader("FTIR Spectrum with Functional Groups")
if st.session_state.stored_results:
    ftir_fig, peak_table = plot_ftir(st.session_state.stored_results) #Receive both the figure and the table data
    st.pyplot(ftir_fig)
    st.subheader("Detected Peaks")
    st.table(peak_table) #Display the table.

    # Download Button for FTIR Plot
    img_buffer = BytesIO()
    ftir_fig.savefig(img_buffer, format="png")
    img_buffer.seek(0)
    st.download_button(label="Download FTIR Plot", data=img_buffer, file_name="FTIR_Spectrum.png", mime="image/png")
else:
    st.write("Please upload files to display the FTIR plot.")