import pandas as pd
import streamlit as st
from io import BytesIO

def process_timetable(uploaded_file):
    if uploaded_file.name.endswith('.xls') or uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        st.error("Unsupported file format. Please upload a .xls, .xlsx, or .csv file.")
        return None
    header_row = df.iloc[0]
    df.dropna(how='all', inplace=True)  # Remove completely empty rows
    df = df.drop_duplicates(keep=False).dropna()

    # Replace all '---' with 'X'
    df.replace('---', 'X', inplace=True)

    timing_columns = ['9-10','12-1','4-5']

    for timing_col in timing_columns:
        # Check if the timing column exists in the DataFrame
        if timing_col in df.columns:
            # Determine the index of the current timing column
            col_index = df.columns.get_loc(timing_col)
            
            # Create a new column name for copying values
            new_col_name = f'ROOM{col_index + 100}'  # Adjust based on your existing ROOM naming      
            df.insert(col_index + 1, new_col_name, df[df.columns[col_index-1]])  # Insert the new column with the copied values
            
    room_columns = [col for col in df.columns if col.startswith('ROOM')]
    rename_dict = {col: f'ROOM{idx + 1}' for idx, col in enumerate(room_columns)}
    df.rename(columns=rename_dict, inplace=True)

    # Initialize the result list
    result = []

    # Get the actual time slots from the DataFrame columns
    time_slots = [col for col in df.columns if col.startswith('8-') or col.startswith('9-') or col.startswith('10-') or col.startswith('11-') or col.startswith('12-') or col.startswith('1-') or col.startswith('2-') or col.startswith('3-') or col.startswith('4-') or col.startswith('5-')]

    # Function to convert time slots to sortable numbers
    def convert_time_to_sortable(time_slot):
        hour, _ = time_slot.split('-')
        hour = int(hour.split(':')[0]) if ':' in hour else int(hour)
        
        if 1 <= hour <= 7:
            hour += 12  # Convert afternoon times to 24-hour format
        
        return hour

    # Process each row
    for _, row in df.iterrows():
        section = row['Section']
        day = row['DAY']
        
        for i, time_slot in enumerate(time_slots, start=1):
            room_key = f'ROOM{i}'
            subject = row[time_slot] if pd.notna(row[time_slot]) and row[time_slot] != 'X' else None
            
            if pd.notna(row[room_key]) and row[room_key] != 'X' and subject:
                entry = {
                    'Section': section,
                    'Day': day,
                    'Room': row[room_key],
                    'Subject': subject,
                    'Time': time_slot,
                    'Time_Sort': convert_time_to_sortable(time_slot)
                }
                result.append(entry)

    # Convert to DataFrame
    result_df = pd.DataFrame(result)

    # Save to CSV
    csv_buffer = BytesIO()
    result_df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    return csv_buffer

# Streamlit app
st.title("Timetable Processor")

with st.form("upload_form"):
    uploaded_file = st.file_uploader("Choose a file")
    submit_button = st.form_submit_button("Submit")

if submit_button and uploaded_file is not None:
    csv_buffer = process_timetable(uploaded_file)
    if csv_buffer:
        st.success("Timetable processed and CSV file created.")
        st.download_button(
            label="Download CSV",
            data=csv_buffer,
            file_name="core_formatted.csv",
            mime="text/csv"
        )