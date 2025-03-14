from pyannote.audio.pipelines import Resegmentation
from pyannote.audio import Pipeline 
from pyannote.audio import Model
import torch 


class PyannotePipe:
    def __init__(self, args):
        self.args = args 
        self.set_gpu()

    def set_gpu(self):
        self.device = torch.device('cuda') if torch.cuda.is_available() else "cpu"

    def set_pipeline(self, model_name):
        self.pipeline = Pipeline(model_name, use_auth_token=self.args['hf_key'])
        self.pipeline.to(self.device)


class PyannoteVADP(PyannotePipe):
    def __init__(self, args):
        super().__init__(args)

    def get_vad(self, pipeline, audio_file, onset=0.5, offset=0.5, min_duration_on=0.5, min_duration_off=0.5):
        '''
        audio_file = "data_path/tets.wav"
        '''
        hyper_params = {
            "onset": onset, 
            "offset": offset, 
            "min_duration_on": min_duration_on,
            "min_duration_off": min_duration_off
        }
        pipeline.instantiate(hyper_params)
        output = pipeline(audio_file)

        vad_timestamp = [] 
        for speech in output.get_timeline().support():
            vad_timestamp.append((speech.start, speech.end))
        return vad_timestamp
    

class PyannoteDIARP(PyannotePipe):
    def __init__(self, args):
        super().__init__(args)
    
    def get_diar(self, pipeline, audio_file, duration_thresh):
        output = pipeline(audio_file)
        diar_result = [] 
        for segment, _, speaker in output.itertracks(yield_label=True):
            start_time = segment.start 
            end_time = segment.end
            duration = end_time - start_time 
            if duration >= duration_thresh:
                diar_result.append([(start_time, end_time), speaker])
        return diar_result
    

class PyannoteResegmentP(PyannotePipe):
    def __init__(self, args):
        super().__init__(args)
    
    def resegment(self, audio_file, baseline, onset=0.5, offset=0.5, min_duration_on=0.5, min_duration_off=0.5):
        model = Model.from_pretrained("pyannote/segmentation", use_auth_token=self.args['hf_key'])
        pipeline = Resegmentation(segmentation=model, diarization='baseline')
        hyper_params = {
            "onset": onset, 
            "offset": offset, 
            "min_duration_on": min_duration_on,
            "min_duration_off": min_duration_off
        }
        pipeline.instantiate(hyper_params)
        resegmented_baseline = pipeline({"audio": audio_file, "baseline": baseline})
        return resegmented_baseline
        