import threading
from core.sniffer.sniffer import Sniffer
from core.sniffer.detect_worker import DetectWorker
from core.model_pipeline import ModelPipeline


if __name__ == "__main__":
    model_pipeline = ModelPipeline.load_models(
    'models/interval-27-30-reality-0_915/power_transformer.pkl',
    'models/interval-27-30-reality-0_915/ica.pkl',
    'models/interval-27-30-reality-0_915/clf.pkl'
    )
    consumer = DetectWorker(model_pipeline, start_packet_number_threshold=27, end_packet_number_threshold=30)
    sniffer = Sniffer(consumer)
    thread_sniff = threading.Thread(target=sniffer.run, args=())
    thread_sniff.start()