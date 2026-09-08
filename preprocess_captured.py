#!/usr/bin/env python

"""

Preprocess captured live flows for model training.



Reads raw CSV from live_capture.py, applies preprocessor.pkl,

splits train/validation/test, and saves processed_live/<dataset>/ datasets.



Usage:

  python preprocess_captured.py --dataset nsl_kdd

  python preprocess_captured.py --dataset cicids2018 --merge-autoencoder

"""



import argparse



from dataset_config import VALID_DATASETS, configure_project

from live_ids.config import CAPTURED_RAW_CSV, PROCESSED_LIVE_FOLDER

from live_ids.prepare_training import preprocess_captured_for_training





def main():

    parser = argparse.ArgumentParser(

        description="Preprocess captured live flows for training"

    )

    parser.add_argument(

        "--dataset",

        "-d",

        choices=VALID_DATASETS,

        default=None,

        help="Dataset profile (default: nsl_kdd)",

    )

    parser.add_argument(

        "--input",

        "-i",

        help="Raw captured CSV (default: captured_data/<dataset>/live_flows_raw.csv)",

    )

    parser.add_argument(

        "--output",

        "-o",

        help="Output folder (default: processed_live/<dataset>/)",

    )

    parser.add_argument(

        "--merge-autoencoder",

        action="store_true",

        help="Append captured normal flows to the dataset's X_train_normal_autoencoder.csv",

    )

    args = parser.parse_args()



    configure_project(args.dataset)



    preprocess_captured_for_training(

        raw_csv_path=args.input or CAPTURED_RAW_CSV,

        output_folder=args.output or PROCESSED_LIVE_FOLDER,

        update_autoencoder_normal=args.merge_autoencoder,

    )





if __name__ == "__main__":

    main()

