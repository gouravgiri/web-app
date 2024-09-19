import streamlit as st
import pandas as pd
import lasio
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
from PIL import Image
import requests
from io import BytesIO

# Global variable to store columns
columns = []

# Function to fetch and display image
def fetch_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        st.image(image, caption='picture')
    else:
        st.write(f"Failed to fetch the image. Status code: {response.status_code}")

# Function to load LAS data
def load_data(uploadedfile):
    if uploadedfile:
        uploadedfile.seek(0) 
        string = uploadedfile.read().decode()
        las_file = lasio.read(string)
        well_data = las_file.df()
    else:
        las_file = None
        well_data = None
    return las_file, well_data

# Function to plot Vshale types
def plot_vshale(vs, well_df, Vsh_linear, Vsh_Larinor_older, Vsh_Larinor_tertiary, Vsh_clavier):
    fig, ax = plt.subplots(figsize=(2, 5))
    color_dict = {
        'Linear': ('teal', Vsh_linear),
        'Vsh_Larinor_older': ('green', Vsh_Larinor_older),
        'Vsh_Larinor_tertiary': ('magenta', Vsh_Larinor_tertiary),
        'Vsh_clavier': ('c', Vsh_clavier)
    }
    
    if vs in color_dict:
        color, data = color_dict[vs]
        ax.plot(data, well_df.DEPT, lw=0.5, color=color)
        ax.set_xlabel(vs)
        ax.set_ylabel('Depth (m)')
        ax.set_xlabel(vs, color=color, fontsize=11)
        ax.grid(which='both', color='black', axis='both', alpha=1, linestyle='--', linewidth=0.8)
        ax.invert_yaxis()
        return fig
    else:
        st.write("Invalid Vshale type selected.")
        return None

# Function to plot well data
def plot(well_data):
    cola, colb, colc = st.columns(3)
    plot_type = cola.radio('Plot type:', ['Line', 'Scatter', 'Histogram', 'Cross-plot'])
    
    if plot_type in ['Line', 'Scatter']:
        curves = colb.multiselect('Select Curves To Plot', columns, key="multiselect1")
        # log_curves = colc.multiselect('Log plot of:', columns, key="multiselect2")
        
        if len(curves) <= 1:
            st.warning('Please select at least 2 curves.')
            return
        
        curve_index = 1
        fig = make_subplots(rows=1, cols=len(curves), subplot_titles=curves, shared_yaxes=True)
        for curve in curves:
            # log_bool = 'log' if curve in log_curves else 'linear'
            mode = 'lines' if plot_type == 'Line' else 'markers'
            fig.add_trace(go.Scatter(x=well_data[curve], y=well_data['DEPT'], mode=mode, marker={'size': 4} if plot_type == 'Scatter' else None), row=1, col=curve_index)
            # fig.update_xaxes(type=log_bool, row=1, col=curve_index)
            curve_index += 1
        
        fig.update_layout(height=1000, showlegend=False, yaxis={'title': 'DEPTH', 'autorange': 'reversed'}, template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
    
    elif plot_type == 'Histogram':
        hist_curve = colb.selectbox('Select a Curve', columns, index=2)
        hist_col = colc.color_picker('Select Histogram Colour', value='#1aa2aa')
        histogram = px.histogram(well_data, x=hist_curve, log_x=False)
        histogram.update_traces(marker_color=hist_col)
        histogram.update_layout(template='plotly_dark')
        st.plotly_chart(histogram, use_container_width=True)
    
    elif plot_type == 'Cross-plot':
        xplot_x = colb.selectbox('X-Axis', columns, index=1)
        xplot_x_log = colb.radio('X Axis - Linear or Logarithmic', ('Linear', 'Logarithmic')) == 'Logarithmic'
        xplot_y = colc.selectbox('Y-Axis', columns, index=2)
        xplot_y_log = colc.radio('Y Axis - Linear or Logarithmic', ('Linear', 'Logarithmic')) == 'Logarithmic'
        xplot_col = st.selectbox('Colour-Bar', columns, index=0)
        
        xplot = px.scatter(well_data, x=xplot_x, y=xplot_y, color=xplot_col, log_x=xplot_x_log, log_y=xplot_y_log)
        xplot.update_layout(template='plotly_dark')
        st.plotly_chart(xplot, use_container_width=True)

# Main Streamlit app
def main():
    global columns  # Use global keyword to modify the global variable
    
    st.title('Formation Evaluation')
    title = st.text_input('Life of Brian')
    
    # Fetch and display image
    image_url = "https://raw.githubusercontent.com/ritgithub02/data/main/Psd1.jpg"
    fetch_image(image_url)
    
    # Tabs for different sections
    t1, t2, t3 = st.tabs(['Data Loading', 'Formation Evaluation', 'Visualization'])
    
    with t1:
        uploaded_file = st.file_uploader("Upload a LAS file", type=["las", "LAS"])
        
        if uploaded_file is not None:
            st.success("LAS file loaded successfully")
            las_file, well_data = load_data(uploaded_file)
            
            if well_data is not None:
                well_data.reset_index(inplace=True)
                well_df = pd.DataFrame(well_data)
                columns = well_df.columns  # Update the global variable
                st.write("Well Data:")
                st.write(well_df)
                st.write("Statistics:")
                st.write(well_df.describe())
            else:
                st.write('Data not available.')
        else:
            st.write("File Upload is Required.")
    
    with t2:
        if uploaded_file is not None and 'GR' in well_df.columns and 'DEPT' in well_df.columns:
            st.title("Vshale Plot")
            gammaray = well_df['GR']
            c1, c2 = st.columns(2)
            max_val_per = c2.text_input("Percentile for max GR:", value="95")
            min_val_per = c1.text_input("Percentile for min GR:", value="5")
            
            if max_val_per.replace('.', '', 1).isdigit() and min_val_per.replace('.', '', 1).isdigit():
                max_val_per = float(max_val_per)
                min_val_per = float(min_val_per)
                
                if 0 <= min_val_per <= 100 and 0 <= max_val_per <= 100:
                    pmax = gammaray.quantile(max_val_per / 100)
                    pmin = gammaray.quantile(min_val_per / 100)
                    Igr = (gammaray - pmin) / (pmax - pmin)
                    
                    Vsh_linear = Igr
                    Vsh_Larinor_older = 0.33 * (2**(2 * Igr) - 1)
                    Vsh_Larinor_tertiary = 0.083 * (2**(3.7 * Igr) - 1)
                    Vsh_clavier = 1.7 - (3.38 - (Igr + 0.7)**2)**0.5
                    
                    vs = st.selectbox('Vshale type', ['Linear', 'Vsh_Larinor_older', 'Vsh_Larinor_tertiary', 'Vsh_clavier'])
                    fig = plot_vshale(vs, well_df, Vsh_linear, Vsh_Larinor_older, Vsh_Larinor_tertiary, Vsh_clavier)
                    if fig:
                        st.pyplot(fig)
                else:
                    st.write("Percentile values should be between 0 and 100.")
            else:
                st.write("Invalid input. Please enter valid percentile values (0-100).")
        else:
            st.write("GR or DEPT column missing in the data.")
    
    with t3:
        if uploaded_file is not None:
            plot(well_df)
        else:
            st.write("Please upload a LAS file first.")

# Execute the app
if __name__ == "__main__":
    main()
