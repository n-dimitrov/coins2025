#!/usr/bin/env python3
"""
Generate groups and group_users CSV files from history data.
"""

import pandas as pd
import os
from pathlib import Path

def generate_groups_csv():
    """Generate groups.csv and group_users.csv from history.csv"""
    
    # Read history.csv to get unique names
    history_file = "data/history.csv"
    if not os.path.exists(history_file):
        print(f"Error: {history_file} not found")
        return False
    
    df_history = pd.read_csv(history_file)
    unique_names = sorted(df_history['name'].unique())
    
    print(f"Found {len(unique_names)} unique users: {', '.join(unique_names)}")
    
    # Create groups DataFrame
    groups_data = {
        'group': ['hippo'],
        'id': [1],
        'name': ['Hippo Collectors']
    }
    df_groups = pd.DataFrame(groups_data)
    
    # Create group_users DataFrame
    group_users_data = {
        'user': unique_names,
        'alias': unique_names,  # Using same name as alias for now
        'group_id': [1] * len(unique_names)  # All users belong to group 1 (hippo)
    }
    df_group_users = pd.DataFrame(group_users_data)
    
    # Save CSV files
    groups_file = "data/groups.csv"
    group_users_file = "data/group_users.csv"
    
    df_groups.to_csv(groups_file, index=False)
    df_group_users.to_csv(group_users_file, index=False)
    
    print(f"\nGenerated files:")
    print(f"  {groups_file} - {len(df_groups)} groups")
    print(f"  {group_users_file} - {len(df_group_users)} users")
    
    # Display the data
    print(f"\nGroups:")
    print(df_groups.to_string(index=False))
    
    print(f"\nGroup Users:")
    print(df_group_users.to_string(index=False))
    
    return True

if __name__ == "__main__":
    if generate_groups_csv():
        print("\nCSV files generated successfully!")
    else:
        print("\nFailed to generate CSV files!")
