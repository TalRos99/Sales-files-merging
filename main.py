import streamlit as st
import pandas as pd
import time

# Configuration
pd.options.mode.copy_on_write = True

if "output_file_name" not in st.session_state:
    st.session_state.output_file_name = f"Final Keyword File {int(time.time())}.csv"

# Page setup
st.set_page_config(page_title="Keyword Processor", layout="wide")
st.title("Keyword Processor")

# Sidebar inputs
st.sidebar.header("Upload Files & Settings")
target_files = st.sidebar.file_uploader(
    "Select Target CSV files", type=["csv"], accept_multiple_files=True
)
all_files = st.sidebar.file_uploader(
    "Select All CSV files", type=["csv"], accept_multiple_files=True
)

output_filename = st.sidebar.text_input(
    "Output Filename", key="output_file_name"
)

process_button = st.sidebar.button("Process Files")

# Placeholders for logs and status
default_log = "Ready to process files."
log_placeholder = st.empty()
status_placeholder = st.empty()

logs = []
def log(message):
    """Append message to log and update display."""
    timestamp = time.strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    logs.append(entry)
    log_placeholder.text("\n".join(logs))

# Utility functions
def merge_files(df_list):
    if not df_list:
        return pd.DataFrame()
    if len(df_list) == 1:
        return df_list[0]
    keys = df_list[0].columns.tolist()[:5]
    merged = df_list[0]
    for df in df_list[1:]:
        merged = pd.merge(merged, df, on=keys, how="outer")
    return merged


def remove_target_from_all(target_df, all_df):
    keys = target_df.columns.tolist()[:5]
    if keys != all_df.columns.tolist()[:5]:
        raise ValueError("The first 5 columns do not match between target and all files.")
    filtered = all_df[~all_df[keys].apply(tuple, 1).isin(target_df[keys].apply(tuple, 1))]
    return filtered

# Display initial log
log_placeholder.text(default_log)
status_placeholder.info(default_log)

# Processing logic
if process_button:
    logs.clear()
    log("Starting processing...")
    try:
        # Validate
        if not target_files:
            st.error("No Target files selected!")
            log("Error: No Target files selected")
        elif not all_files:
            st.error("No All files selected!")
            log("Error: No All files selected")
        else:
            status_placeholder.info("Processing files...")
            # Read target
            log("Reading Target files...")
            target_dfs = [pd.read_csv(f) for f in target_files]
            if len(target_dfs) > 1:
                log(f"Merging {len(target_dfs)} Target files...")
                target_df = merge_files(target_dfs)
            else:
                target_df = target_dfs[0]
            log(f"Target data shape: {target_df.shape}")

            # Read all
            log("Reading All files...")
            all_dfs = [pd.read_csv(f) for f in all_files]
            if len(all_dfs) > 1:
                log(f"Merging {len(all_dfs)} All files...")
                all_df = merge_files(all_dfs)
            else:
                all_df = all_dfs[0]
            log(f"All data shape: {all_df.shape}")

            # Filter
            log("Removing Target entries from All data...")
            filtered_all = remove_target_from_all(target_df, all_df)
            log(f"Filtered data shape: {filtered_all.shape}")

            # Tag and combine
            log("Adding SELECTED flags and concatenating...")
            target_df['SELECTED'] = True
            filtered_all['SELECTED'] = False
            cols_t = ['SELECTED'] + [c for c in target_df.columns if c != 'SELECTED']
            cols_a = ['SELECTED'] + [c for c in filtered_all.columns if c != 'SELECTED']
            final = pd.concat([
                target_df[cols_t],
                filtered_all[cols_a]
            ], ignore_index=True)
            log(f"Final data shape: {final.shape}")
            st.dataframe(final, height=250)
            # Provide download
            csv_bytes = final.to_csv(index=False).encode('utf-8')
            st.success("Processing complete!")
            st.download_button(
                label="Download CSV",
                data=csv_bytes,
                file_name=st.session_state.output_file_name,
                mime="text/csv"
            )
    except Exception as e:
        log(f"Error occurred: {e}")
        st.error(f"An error occurred: {e}")
    finally:
        status_placeholder = st.empty()
