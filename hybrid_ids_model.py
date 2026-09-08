# ================================================================
# HYBRID AUTOENCODER + XGBOOST INTRUSION DETECTION SYSTEM
# ================================================================
#
# Supports NSL-KDD and CICIDS2018 datasets.
#


import argparse



from dataset_config import VALID_DATASETS, configure_project





def main():

    parser = argparse.ArgumentParser(

        description="Train hybrid autoencoder + XGBoost IDS"

    )

    parser.add_argument(

        "--dataset",

        "-d",

        choices=VALID_DATASETS,

        default=None,

        help="Dataset profile (default: nsl_kdd)",

    )

    args = parser.parse_args()



    profile = configure_project(args.dataset)

    print(f"Dataset: {profile.display_name}")

    print(f"Processed data: {profile.data_folder}")

    print(f"Model output:   {profile.model_folder}\n")



    if not __import__("os").path.exists(profile.data_folder):

        raise FileNotFoundError(

            f"Processed data not found: {profile.data_folder}\n"

            f"Run: python {profile.preprocess_script}"

        )



    import hybrid_ids.config as config

    from hybrid_ids.main import run_pipeline



    print(f"Writing models to: {config.MODEL_FOLDER}\n")