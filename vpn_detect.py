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
    parser.add_argument(
        "-f",
        "--flow_storage_size",
        type=int,
        default=100,
        help="Set the maximum allowed number of threads to be processed. If exceeded, the oldest flow will be destroyed"
    )

    return parser

if __name__ == "__main__":
    args = make_argparser().parse_args()
    model_pipeline = ModelPipeline.load_models(
        'models/selected-feature-0_96/power_transformer.pkl',
        'models/selected-feature-0_96/ica.pkl',
        'models/selected-feature-0_96/clf.pkl'
    )
    consumer = DetectWorker(
        model_pipeline,
        start_packet_number_threshold=args.start_threshold,
        end_packet_number_threshold=args.end_threshold,
        flow_storage_size=args.flow_storage_size
    )
    sniffer = Sniffer(consumer)
    thread_sniff = threading.Thread(target=sniffer.run, args=())
    thread_sniff.start()