import argparse
import threading
from pathlib import Path
from core.sniffer.sniffer import Sniffer
from core.sniffer.detect_worker import DetectWorker
from core.model_pipeline import ModelPipeline


def make_argparser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-p",
        "--models_path",
        type=Path,
        required=True,
        help="Directory with datasets",
    )
    parser.add_argument(
        "-s",
        "--start_threshold",
        type=int,
        default=27,
        help="Starting from which package to detect",
    )
    parser.add_argument(
        "-e",
        "--end_threshold",
        type=int,
        default=30,
        help="After flow has processed a given number of packets, delete it from the processing queue."
    )

    return parser

if __name__ == "__main__":
    args = make_argparser().parse_args()
    model_pipeline = ModelPipeline.load_models(
        args.models_path.joinpath('power_transformer.pkl'),
        args.models_path.joinpath('ica.pkl'),
   		args.models_path.joinpath('clf.pkl')
    )
    consumer = DetectWorker(model_pipeline, start_packet_number_threshold=args.start_threshold, end_packet_number_threshold=args.end_threshold)
    sniffer = Sniffer(consumer)
    thread_sniff = threading.Thread(target=sniffer.run, args=())
    thread_sniff.start()