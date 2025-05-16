import pandas as pd
from sklearn.model_selection import train_test_split
from pathlib import Path

def split_dataset(df, split_col, split_ratio=(0.7, 0.15, 0.15)):
    train_size, val_size, test_size = split_ratio
    df_train_test, df_val = train_test_split(
        df, test_size=val_size, stratify=df[split_col] if split_col else None
    )

    test_frac_adjusted = test_size / (train_size + test_size)
    df_train, df_test = train_test_split(
        df_train_test, test_size=test_frac_adjusted,
        stratify=df_train_test[split_col] if split_col else None
    )

    return df_train, df_test, df_val
