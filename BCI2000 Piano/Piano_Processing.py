##Signal Processing Module for traditional AR decoder written in python
#Imports
import numpy as np 
import dlfx
import memspectrum
import pickle, os, copy, time, re

import scipy
from scipy.signal import resample
import tensorflow as tf
import torch
from BCPy2000.GenericSignalProcessing import BciGenericSignalProcessing

# EEGNet-specific imports
from deepLearning.EEGModels_tf import EEGNet
from tensorflow.keras import utils as np_utils
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras import backend as K
torch.set_default_dtype(torch.float64)

from deepLearning.train_util import TorchPredictor, load_conformer_checkpoint
from deepLearning import torch_decoders


#################################################################
#################################################################

class OnlineMovingAverage:
    def __init__(self, num_classes, window_size=5):
        self.num_classes = num_classes
        self.window_size = window_size
        self.data_windows = [np.zeros(window_size) for _ in range(num_classes)]
        self.indices = [0 for _ in range(num_classes)]
        self.counts = [0 for _ in range(num_classes)]

    def update(self, new_probabilities):
        moving_averages = np.zeros(self.num_classes)
        for i in range(self.num_classes):
            # Update the data window
            self.data_windows[i][self.indices[i]] = new_probabilities[i]
            self.indices[i] = (self.indices[i] + 1) % self.window_size

            # Calculate the moving average
            if self.counts[i] < self.window_size:
                self.counts[i] += 1
            moving_averages[i] = np.sum(self.data_windows[i]) / self.counts[i]

        return moving_averages
	
class ExpMovingAvg:
    def __init__(self, alpha = 0.35):
        self.alpha = alpha
        self.history = 0

    def update(self,prob):
        new_prob = self.alpha * prob + (1.0 - self.alpha) * self.history
        self.history = new_prob
        return new_prob
    
    def reset(self):
        self.history = 0

    def get_history(self):
    	return self.history
    


prob_to_vel_params = {
    "max_velocity": 1.0,
    "direction_deadband": 0.08,
    "full_direction_score": 0.80,
    "move_confidence_deadband": 0.10,
    "full_move_confidence": 0.70,
    "rest_brake_gain": 1.0,
    "direction_exponent": 1.25,
    "confidence_exponent": 1.25,
    "smoothing_alpha": 0.7, # higher - less smoothing
    # "max_delta_per_step": 0.12,
    "stop_velocity": 0.02,
}

def _deadband_to_unit(values, deadband, full_scale):
    if full_scale <= deadband:
        raise ValueError("full_scale must be greater than deadband.")
    return np.clip((values - deadband) / (full_scale - deadband), 0.0, 1.0)

def map_probs_to_velocity(probs, ExpMovingAverage,  mapping_params=None):
    mapping_params = prob_to_vel_params if mapping_params is None else mapping_params
    probs = np.asarray(probs, dtype=np.float32).reshape(-1)
    if probs.size != 3:
        raise ValueError("probs must contain 3 values for left/right/rest.")

    p_left = probs[0]
    p_right = probs[1]
    p_rest = probs[2]

    direction_score = p_right - p_left
    direction_gain = _deadband_to_unit(
        np.abs(direction_score),
        mapping_params["direction_deadband"],
        mapping_params["full_direction_score"],
    )
    move_confidence = np.maximum(p_left, p_right) - mapping_params["rest_brake_gain"] * p_rest
    confidence_gain = _deadband_to_unit(
        move_confidence,
        mapping_params["move_confidence_deadband"],
        mapping_params["full_move_confidence"],
    )
    raw_velocity = (
        np.sign(direction_score)
        * mapping_params["max_velocity"]
        * np.power(direction_gain, mapping_params["direction_exponent"])
        * np.power(confidence_gain, mapping_params["confidence_exponent"])
    )
	
    # velocity = ExpMovingAverage.update(raw_velocity)
    velocity = raw_velocity
    # if mapping_params["max_delta_per_step"] is not None and mapping_params["max_delta_per_step"] > 0:
    #         delta = np.clip(
    #             velocity - ExpMovingAverage.get_history(),
    #             -mapping_params["max_delta_per_step"],
    #             mapping_params["max_delta_per_step"] ,
    #         )
    #         velocity = ExpMovingAverage.get_history() + delta
    
    if np.abs(velocity) < mapping_params["stop_velocity"]:
        velocity = 0.0

    return velocity


#################################################################
#################################################################

class BciSignalProcessing(BciGenericSignalProcessing):	
	#############################################################
	def Construct(self):
		parameters = [
			"Filtering:Input string Device=	biosemi	% % %	//EEG device used",
			"Filtering:DeepLearning int Subject= 1	1 	1	15	//Subject number (1-15)",
			"Filtering:DeepLearning int Session= 1	1 	1	10	//Session number (use the current session ex. start at 2 for DL)",
			"Filtering:Normalizer float NormalizationUpdateTime=    1   6   0   30   //How long between normalizer updates",
			"Filtering:Normalizer int BufferLength=    1   30   0   100   //Buffer length in secondss",
			"Filtering:Decoder string ArmDecoder=	DL % % %	//The arm decoder to use",
			"Filtering:Decoder string FingerDecoder=	DL % % %	//The finger decoder to use",
			
			"Filtering:ArmDecoding	int	ArmWindowLength=	500	500	0	5000	// window length in ms",
			"Filtering:ArmDecoding	string ArmModelPath= C:\\Users\\helabrobotics\\Desktop\\BCI_DL\\BCI2000\\python\\models\\Subject1_1s.h5 % % %	// path to the trained model",
			"Filtering:ArmDecoding int ArmSmoothing=	1	1	0	1	//Whether to smooth arm velocity (boolean)",

			"Filtering:FingerDecoding	int	DownsampleRate=	100	100	0	1024	// downsampling rate",
			"Filtering:FingerDecoding	int	WindowLength=	1000	1000	0	5000	// window length in ms",
			"Filtering:FingerDecoding	int SmoothingLength= 5	5	0	10	//smoothing length in number of windows",
			"Filtering:FingerDecoding	string ModelPath= C:\\Users\\helabrobotics\\Desktop\\BCI_DL\\BCI2000\\python\\models\\Subject1_1s.h5 % % %	// path to the trained model",
			"Filtering:Normalizer int ConstantSpeed=	1	1	0	1	//Whether to output constant speed (boolean)"
		]

		states = [
			"prob_thumb     16 0 0 0",
            "prob_index     16 0 0 0",
            "prob_pinky     16 0 0 0",
			"Target_PosX_u        16 0 0 0",
            "Target_PosY_u        16 0 0 0",
            "Target_Number		  16 0 0 0",
            "Click              16 0 0 0",
            "SignedOffset       16 32767 0 0",
            "FloatScalar        16 10000 0 0",
            "BaselineOn   1 0 0 0",
            "StartCueOn   1 0 0 0",
            "StopCueOn    1 0 0 0",
            "Feedback     1 0 0 0",   # bells? whistles?

            "FingerTask     1 0 0 0",
            "ArmTask     1 0 0 0",
            "Idle     1 0 0 0",
            "FingerTarget   4 0 0 0",
            "ArmTarget   4 0 0 0",
            "ArmStart   4 0 0 0",
            "ArmDiff   4 0 0 0",
            "RawFingerPred 4 0 0 0",
            "FingerPred 4 0 0 0",
            "AccumFingerPred 4 0 0 0",
            "ArmPred_X  16 0 0 0",
            "Raw_ArmPred_X  16 0 0 0",

            "FingerHitCount    16 0 0 0",
            "FingerMissCount   16 0 0 0",
            "ArmHitCount    16 0 0 0",
            "ArmMissCount   16 0 0 0",
            "InnerTrialCount    16 0 0 0",

            "FingerTrialLen    16 0 0 0",
            "ArmTrialLen    16 0 0 0",

		]

		return (parameters, states)

		

	#############################################################
	def Preflight(self, sigprops):
		self.out_signal_dim=(6,1) #Define the dimensions of the output signal. Here there are 3: one for horizontal movement, one for finger

	#############################################################
	def Initialize(self, indim, outdim):
		#Get subject number and model path
		self.subj = int(self.params['Subject'])
		self.session = int(self.params['Session'])
		self.subjStr = 'S{}'.format(str(self.subj).zfill(2))
		self.ArmDecoder = self.params['ArmDecoder']
		self.FingerDecoder = self.params['FingerDecoder']
		self.Device = self.params['Device']
		self.states['FingerTrialLen'] = int(float(self.params['PressTime'])*1000)
		self.states['ArmTrialLen'] = int(float(self.params['MoveTime'])*1000)

		self.samplingRate = int(self.params['SamplingRate'].replace("Hz", ""))
		self.newsamplingRate = int(self.params['DownsampleRate'])
		self.b, self.a = scipy.signal.butter(4, [0.5, 40], btype='bandpass', fs=self.newsamplingRate)


		if self.Device == 'biosemi':
			self.blockSize = 128
			self.sampleRate = 1024
		else:
			self.blockSize = 40
			self.sampleRate = 1000

		if self.ArmDecoder == 'DL':

			self.arm_newsig = []
			self.arm_chans = self.in_signal_dim[0]
			self.arm_smoothingLen = int(self.params['SmoothingLength'])
			self.arm_DesiredLen = int(int(self.params['ArmWindowLength'])/1000*self.newsamplingRate)

			self.nclasses = 3
			self.ArmModel = EEGNet(nb_classes = self.nclasses, Chans = self.arm_chans, Samples = self.arm_DesiredLen, 
							dropoutRate = 0.5, kernLength = 32, F1 = 8, D = 2, F2 = 16, 
							dropoutType = 'Dropout')
			self.ArmModel.load_weights(self.params['ArmModelPath'])
			self.ExpMovingAverage = ExpMovingAvg(alpha=prob_to_vel_params["smoothing_alpha"])
		elif self.ArmDecoder == 'DL_RLUD':
			self.arm_newsig = []
			self.arm_chans = self.in_signal_dim[0]
			self.arm_smoothingLen = int(self.params['SmoothingLength'])
			self.arm_DesiredLen = int(int(self.params['ArmWindowLength'])/1000*self.newsamplingRate)

			self.nclasses = 2
			self.ArmModel = EEGNet(nb_classes = self.nclasses, Chans = self.arm_chans, Samples = self.arm_DesiredLen, 
							dropoutRate = 0.5, kernLength = 32, F1 = 8, D = 2, F2 = 16, 
							dropoutType = 'Dropout')
			self.ArmModel.load_weights(self.params['ArmModelPath'])
			self.ExpMovingAverage = ExpMovingAvg(alpha=prob_to_vel_params["smoothing_alpha"])
		elif self.ArmDecoder == 'EEGK_RL':
			weights_path = self.params['ArmModelPath']
			class_match = re.search(r'(\d+)class', weights_path.lower())
			n_classes = int(class_match.group(1)) if class_match else 2
			
			#Data window should be size: (Number of channels, Number of samples)
			self.arm_newsig = []
			self.arm_chans = self.in_signal_dim[0]
			self.arm_smoothingLen = int(self.params['SmoothingLength'])
			self.arm_DesiredLen = int(int(self.params['ArmWindowLength'])/1000*self.newsamplingRate)

			torch_model = torch_decoders.build_torch_model(
				'eegk',
				chans=self.arm_chans,
				samples=self.arm_DesiredLen,
				n_classes=n_classes,
				task='arm'
			).to('cpu')
			load_conformer_checkpoint(torch, torch_model, self.params['ArmModelPath'], 'cpu')
			torch_model.float()
			self.ArmModel = TorchPredictor(torch_model, 'cpu')
			self.ExpMovingAverage = ExpMovingAvg(alpha=prob_to_vel_params["smoothing_alpha"])
		
		elif self.ArmDecoder == 'EEGK':
			weights_path = self.params['ArmModelPath']
			
			#Data window should be size: (Number of channels, Number of samples)
			self.arm_newsig = []
			self.arm_chans = self.in_signal_dim[0]
			self.arm_smoothingLen = int(self.params['SmoothingLength'])
			self.arm_DesiredLen = int(int(self.params['ArmWindowLength'])/1000*self.newsamplingRate)

			torch_model = torch_decoders.build_torch_model(
				'eegk',
				chans=self.arm_chans,
				samples=self.arm_DesiredLen,
				n_classes=3,
			).to('cpu')
			load_conformer_checkpoint(torch, torch_model, self.params['ArmModelPath'], 'cpu')
			torch_model.float()
			self.ArmModel = TorchPredictor(torch_model, 'cpu')
			self.ExpMovingAverage = ExpMovingAvg(alpha=prob_to_vel_params["smoothing_alpha"])
		
		else:
			selChans = [115, 117, 108, 110, 124, 54, 52, 63, 56, 50, 1, 87, 3]		#Labels for reference: C3, C5, FC3, C1, CP3, C4, C2, FC4, C6, CP4, CZ, FCZ, CPZ
			self.selChans = [x-1 for x in selChans] # zero-index
			#Below is the weight matrix used for laplacian spatial filtering. Each output channel is reduced by the average of its four surrounding channels.
			self.weights = np.array([
				[1,-0.25,-0.25,-0.25,-0.25,0,0,0,0,0,0,0,0],
				[0,0,0,0,0,1,-0.25,-0.25,-0.25,-0.25,0,0,0]
				])
			
			#TODO:change the window&bufferlength
			self.window = np.zeros((len(self.selChans),int(4*self.blockSize))) 					#Initialize the data window. Second input is window size in time points, for 1kHz fs this is the same as time in ms
			self.bufferLength = int(self.sampleRate/self.blockSize*int(self.params['BufferLength']))			#Output buffer length, since the data is processed every 40ms (25Hz) this buffer has a length of 25*(buffer length in seconds)
			self.buffer = np.zeros((1,self.bufferLength))						#Initialize the output buffer
			self.updateBool = False 											#Only used for DT tasks. True when normalizer can update, false when normalizer should not update
			self.normMean = np.array([0,0])
			self.normGain = np.array([0,0])
			self.outSignalRecord = []
			self.normalizationUpdateTime=100

		if self.FingerDecoder == 'DL':
			self.FeefbackOn = 0
			self.newsig = []
			self.chans = self.in_signal_dim[0]
			self.finger_smoothingLen = int(self.params['SmoothingLength'])
			self.finger_DesiredLen = int(int(self.params['WindowLength'])/1000*self.newsamplingRate)

			self.finger_nclasses = 3
			self.model = EEGNet(nb_classes = self.finger_nclasses, Chans = self.chans, Samples = self.finger_DesiredLen, 
							dropoutRate = 0.5, kernLength = 32, F1 = 8, D = 2, F2 = 16, 
							dropoutType = 'Dropout')
			self.model.load_weights(self.params['ModelPath'])

			self.moving_avg = OnlineMovingAverage(num_classes=self.finger_nclasses, window_size=self.finger_smoothingLen)
			self.finger_prob_history = []

		else: # no online processing
			pass

	#############################################################

	def Process(self, sig):
		arm_out = np.zeros((1, 1))

		if self.ArmDecoder == 'DL' and self.states['ArmTask']:
			kernels = 1
			# sig: (C,T)
			chans, samples = np.shape(sig)
			sig = sig-sig.mean(axis=0)

			newSamples = max(1, int(round(samples/self.samplingRate*self.newsamplingRate)))

			if not len(self.arm_newsig):
				self.arm_newsig = resample(sig, newSamples, t=None, axis=1, window=None, domain='time')
			else:
				self.arm_newsig = np.concatenate((self.arm_newsig, resample(sig, newSamples, t=None, axis=1, window=None, domain='time')),axis=1)

			if np.size(self.arm_newsig,1) >= self.arm_DesiredLen:
				self.arm_newsig = self.arm_newsig[:,-self.arm_DesiredLen:]
			else:
				return np.zeros((3,1))

			# bandpass filtering
			padding_length = 100  # Number of zeros to pad
			padded_sig = np.pad(self.arm_newsig, ((0,0),(padding_length,padding_length)), 'constant', constant_values=0)

			padded_sig = scipy.signal.lfilter(self.b, self.a, padded_sig, axis=-1)
			insig = padded_sig[:,padding_length:-padding_length]

			# insig = mne.filter.filter_data(self.arm_newsig.astype(np.float64), sfreq = self.samplingRate, l_freq = 0.2, h_freq = 40, verbose = 0)
			insig = scipy.stats.zscore(insig, axis=1, nan_policy='omit')
			insig = np.nan_to_num(insig, nan=0.0, posinf=0.0, neginf=0.0)
			insig = insig.reshape(1,self.arm_chans,self.arm_DesiredLen,kernels)
			arm_prob = self.ArmModel.predict(insig, verbose=0)
			arm_prob	= arm_prob.flatten() # probs for 3-class classification
			pred_label = np.argmax(arm_prob).astype(np.int64)
			class_direction = np.array([-1.0, 1.0, 0.0], dtype=np.float32)
			raw_velocity = class_direction[pred_label] * (arm_prob[pred_label] - arm_prob[2])
			# arm_out = map_probs_to_velocity(arm_prob, self.ExpMovingAverage)
			velocity = self.ExpMovingAverage.update(raw_velocity)
			arm_out = velocity
			arm_out = np.array([[arm_out]])
		elif self.ArmDecoder == 'DL_RLUD' and self.states['ArmTask']:
			kernels = 1
			# sig: (C,T)
			chans, samples = np.shape(sig)
			sig = sig-sig.mean(axis=0)

			newSamples = max(1, int(round(samples/self.samplingRate*self.newsamplingRate)))

			if not len(self.arm_newsig):
				self.arm_newsig = resample(sig, newSamples, t=None, axis=1, window=None, domain='time')
			else:
				self.arm_newsig = np.concatenate((self.arm_newsig, resample(sig, newSamples, t=None, axis=1, window=None, domain='time')),axis=1)

			if np.size(self.arm_newsig,1) >= self.arm_DesiredLen:
				self.arm_newsig = self.arm_newsig[:,-self.arm_DesiredLen:]
			else:
				return np.zeros((3,1))

			# bandpass filtering
			padding_length = 100  # Number of zeros to pad
			padded_sig = np.pad(self.arm_newsig, ((0,0),(padding_length,padding_length)), 'constant', constant_values=0)

			padded_sig = scipy.signal.lfilter(self.b, self.a, padded_sig, axis=-1)
			insig = padded_sig[:,padding_length:-padding_length]

			# insig = mne.filter.filter_data(self.arm_newsig.astype(np.float64), sfreq = self.samplingRate, l_freq = 0.2, h_freq = 40, verbose = 0)
			insig = scipy.stats.zscore(insig, axis=1, nan_policy='omit')
			insig = np.nan_to_num(insig, nan=0.0, posinf=0.0, neginf=0.0)
			insig = insig.reshape(1,self.arm_chans,self.arm_DesiredLen,kernels)
			arm_prob = self.ArmModel.predict(insig, verbose=0)
			arm_prob	= arm_prob.flatten() # probs for 3-class classification
			raw_velocity = arm_prob[0] - arm_prob[1] # may need a threshold for low velocities for it to stop?
			# arm_out = map_probs_to_velocity(arm_prob, self.ExpMovingAverage)
			arm_out = raw_velocity
			arm_out = np.array([[arm_out]])

		elif self.ArmDecoder == 'EEGK_RL' and self.states['ArmTask']:
			kernels = 1
			# sig: (C,T)
			chans, samples = np.shape(sig)
			sig = sig-sig.mean(axis=0)

			newSamples = max(1, int(round(samples/self.samplingRate*self.newsamplingRate)))

			if not len(self.arm_newsig):
				self.arm_newsig = resample(sig, newSamples, t=None, axis=1, window=None, domain='time')
			else:
				self.arm_newsig = np.concatenate((self.arm_newsig, resample(sig, newSamples, t=None, axis=1, window=None, domain='time')),axis=1)

			if np.size(self.arm_newsig,1) >= self.arm_DesiredLen:
				self.arm_newsig = self.arm_newsig[:,-self.arm_DesiredLen:]
			else:
				return np.zeros((3,1))

			# bandpass filtering
			padding_length = 100  # Number of zeros to pad
			padded_sig = np.pad(self.arm_newsig, ((0,0),(padding_length,padding_length)), 'constant', constant_values=0)

			padded_sig = scipy.signal.lfilter(self.b, self.a, padded_sig, axis=-1)
			insig = padded_sig[:,padding_length:-padding_length]

			# insig = mne.filter.filter_data(self.arm_newsig.astype(np.float64), sfreq = self.samplingRate, l_freq = 0.2, h_freq = 40, verbose = 0)
			insig = scipy.stats.zscore(insig, axis=1, nan_policy='omit')
			insig = np.nan_to_num(insig, nan=0.0, posinf=0.0, neginf=0.0)
			insig = insig.reshape(1,self.arm_chans,self.arm_DesiredLen,kernels)

			arm_prob = self.ArmModel.predict(insig, verbose=0)
			arm_prob = arm_prob.flatten() 
			raw_velocity = arm_prob[0] - arm_prob[1] 
			velocity = self.ExpMovingAverage.update(raw_velocity)
			arm_out = velocity if int(self.params['ArmSmoothing']) else raw_velocity
			arm_out = np.array([[arm_out]])

		elif self.ArmDecoder == 'EEGK' and self.states['ArmTask']:
			kernels = 1
			# sig: (C,T)
			chans, samples = np.shape(sig)
			sig = sig-sig.mean(axis=0)

			newSamples = max(1, int(round(samples/self.samplingRate*self.newsamplingRate)))

			if not len(self.arm_newsig):
				self.arm_newsig = resample(sig, newSamples, t=None, axis=1, window=None, domain='time')
			else:
				self.arm_newsig = np.concatenate((self.arm_newsig, resample(sig, newSamples, t=None, axis=1, window=None, domain='time')),axis=1)

			if np.size(self.arm_newsig,1) >= self.arm_DesiredLen:
				self.arm_newsig = self.arm_newsig[:,-self.arm_DesiredLen:]
			else:
				return np.zeros((3,1))

			# bandpass filtering
			padding_length = 100  # Number of zeros to pad
			padded_sig = np.pad(self.arm_newsig, ((0,0),(padding_length,padding_length)), 'constant', constant_values=0)

			padded_sig = scipy.signal.lfilter(self.b, self.a, padded_sig, axis=-1)
			insig = padded_sig[:,padding_length:-padding_length]

			# insig = mne.filter.filter_data(self.arm_newsig.astype(np.float64), sfreq = self.samplingRate, l_freq = 0.2, h_freq = 40, verbose = 0)
			insig = scipy.stats.zscore(insig, axis=1, nan_policy='omit')
			insig = np.nan_to_num(insig, nan=0.0, posinf=0.0, neginf=0.0)
			insig = insig.reshape(1,self.arm_chans,self.arm_DesiredLen,kernels)

			arm_prob = self.ArmModel.predict(insig, verbose=0)
			arm_prob	= arm_prob.flatten() # probs for 3-class classification
			pred_label = np.argmax(arm_prob).astype(np.int64)
			class_direction = np.array([-1.0, 1.0, 0.0], dtype=np.float32)
			raw_velocity = class_direction[pred_label] * (arm_prob[pred_label]) # - arm_prob[2])
			# arm_out = map_probs_to_velocity(arm_prob, self.ExpMovingAverage)
			velocity = self.ExpMovingAverage.update(raw_velocity)
			arm_out = velocity
			arm_out = np.array([[arm_out]])

		elif self.states['ArmTask']:
			#Grab selected channels-----------------------------------------------
			curBlock = sig[self.selChans,:]

			#Windowing------------------------------------------------------------
			#Add current sample block to window
			self.window = np.roll(self.window,-int(self.blockSize),1)
			self.window[:,self.window.shape[1]-int(self.blockSize):self.window.shape[1]] = curBlock
			curWindow = copy.deepcopy(self.window)
			means = np.mean(curWindow,axis=1,keepdims=True)
			curWindow = curWindow - means
			#Spatial Filtering----------------------------------------------------
			filtChans = np.matmul(self.weights,curWindow)					#Out channels: C3, C4

			#Spectral estimation (AR)---------------------------------------------
			specChans = np.zeros((filtChans.shape[0],1))
			for channel in range(filtChans.shape[0]):
				arModel = memspectrum.MESA()
				arModel.solve(filtChans[channel,:],m=17)
				frequencies = np.linspace(10.5,13.5)
				spectrum = arModel.spectrum(0.001,frequencies)
				specChans[channel] = np.sqrt(np.sum(spectrum))					#Power -> amplitude by square-root, compare with taking square root before summation

			#Linear classifier----------------------------------------------------
			outChans = np.zeros((1,1))
			outChans[0] = specChans[1]-specChans[0]

			#Normalizer-----------------------------------------------------------
			#Check whether to add data to buffer
			if (self.states['Feedback']):
				self.buffer = np.roll(self.buffer,1,1)
				self.buffer[:,0] = outChans[:,0]

			##CP updating
			#Get start time if it doesn't exist yet
			if not hasattr(self,'updateTime'):
				self.startTime = round(time.time()*1000)
				self.updateTime = 0
			curTime = round(time.time()*1000)

			#Check for update
			if curTime - self.updateTime >=self.normalizationUpdateTime:
				#Update normalize mean and gain
				self.normMean = np.mean(self.buffer,axis=1,keepdims = True)
				variance = np.std(self.buffer,axis=1,keepdims=True)**2
				for channel in range(variance.shape[0]):
					if variance[channel]<1e-8:
						variance[channel] = 1e-8
				self.normGain = 1 / variance
				self.updateTime = round(time.time()*1000) - self.startTime

			# ##DT updating
			# if (self.updateBool) and (not self.states['Feedback']):
			# 	#Update normalize mean and gain
			# 	self.normMean = np.mean(self.buffer,axis=1,keepdims = True)
			# 	variance = np.std(self.buffer,axis=1,keepdims=True)**2
			# 	for channel in range(variance.shape[0]):
			# 		if variance[channel]<1e-8:
			# 			variance[channel] = 1e-8
			# 	self.normGain = 1 / variance
			# 	self.updateBool = False

			# if (not self.updateBool) and (self.states['Feedback']):
			# 	self.updateBool = True

			#Do normalization
			arm_out = (outChans - self.normMean) * self.normGain

			#Thresholding
			for channel in range(arm_out.shape[0]):
				if abs(arm_out[channel]) > 10:
					arm_out[channel] = np.sign(arm_out[channel]) *10
		else:
			self.arm_newsig = []
			arm_out = np.zeros((1,1))
			if hasattr(self,'ExpMovingAverage'):
				self.ExpMovingAverage.reset()



		if self.FingerDecoder == 'DL' and self.states['FingerTask']:
			finger_out = 10
			accum_finger_out = 10
			finger_prob = np.zeros(3)
			kernels = 1

			# sig: (C,T)
			chans, samples = np.shape(sig)
			sig = sig-sig.mean(axis=0)

			newSamples = int(samples/self.samplingRate*self.newsamplingRate)

			if not len(self.finger_newsig):
				self.finger_newsig = resample(sig, newSamples, t=None, axis=1, window=None, domain='time')
			else:
				self.finger_newsig = np.concatenate((self.finger_newsig, resample(sig, newSamples, t=None, axis=1, window=None, domain='time')),axis=1)

			if np.size(self.finger_newsig,1) >= self.finger_DesiredLen:
				self.FeefbackOn = 1
				self.finger_newsig = self.finger_newsig[:,-self.finger_DesiredLen:]
			else:
				self.FeefbackOn = 0
			# feed into EEGNet
			if self.FeefbackOn:
				# bandpass filtering
				padding_length = 100  # Number of zeros to pad
				padded_sig = np.pad(self.finger_newsig, ((0,0),(padding_length,padding_length)), 'constant', constant_values=0)

				padded_sig = scipy.signal.lfilter(self.b, self.a, padded_sig, axis=-1)
				insig = padded_sig[:,padding_length:-padding_length]

				# insig = mne.filter.filter_data(self.finger_newsig.astype(np.float64), sfreq = self.samplingRate, l_freq = 0.2, h_freq = 40, verbose = 0)
				insig = scipy.stats.zscore(insig, axis=1, nan_policy='omit')
				insig = insig.reshape(1,self.chans,self.finger_DesiredLen,kernels)
				finger_prob = self.model.predict(insig)
				finger_prob	= finger_prob.flatten() # probs for 3-class classification
				smoothed_probs = self.moving_avg.update(finger_prob)

				cur_time = round(time.time()*1000)
				finger_pred = int(np.argmax(finger_prob)) # finger smoothing currently disabled
				
				# self.finger_pred_history = [
				# 	(pred_time, pred_value)
				# 	for pred_time, pred_value in self.finger_pred_history
				# 	if cur_time - pred_time <= max_history_ms
				# ]

				# recent_preds = np.fromiter(
				# 	(pred_value for _, pred_value in self.finger_pred_history),
				# 	dtype=np.int64,
				# 	count=len(self.finger_pred_history)
				# )

				finger_out = finger_pred

				self.states['prob_thumb'] = finger_prob[0]*1000
				self.states['prob_index'] = finger_prob[1]*1000
				self.states['prob_pinky'] = finger_prob[2]*1000
				self.states['RawFingerPred'] = finger_pred

				self.finger_pred_history.append(finger_out)
				accum_finger_out = int(np.argmax(np.bincount(np.array(self.finger_pred_history))))
			else:
				finger_out = 10
				accum_finger_out = 10
		else:			
			finger_out = 10
			accum_finger_out = 10
			finger_prob = np.zeros(3)
			self.finger_newsig = []
			self.FeefbackOn = 0
			self.states['prob_thumb'] = 0
			self.states['prob_index'] = 0
			self.states['prob_pinky'] = 0
			self.states['RawFingerPred'] = 10
			self.finger_pred_history = []
			self.moving_avg = OnlineMovingAverage(num_classes=self.finger_nclasses, window_size=self.finger_smoothingLen) # clear the moving average after the end of the trial

		#out_signal = np.array([1,1])
		#Do constant speed
		# constantSpeedFlag = int(self.params['ConstantSpeed'])
		# if constantSpeedFlag:
		# 	vectorMag = np.sqrt(out_signal[0]**2 + out_signal[1]**2)
		# 	out_signal[0] = out_signal[0]/vectorMag
		# 	out_signal[1] = out_signal[1]/vectorMag
		#Output
		# self.outSignalRecord.append(out_signal[2])

		out_signal = np.vstack((arm_out, np.array([[finger_out]]), np.array([[accum_finger_out]]), finger_prob[:, np.newaxis]))

		return out_signal

	# def StopRun(self):
		#The following files are useful for debugging but are not needed for experiments
		# with open('pickle/outRecord.pkl','wb') as pickleFile:
		# 	pickle.dump(self.outSignalRecord,pickleFile)
		# with open('pickle/buffer.pkl','wb') as pickleFile:
		# 	pickle.dump(self.buffer,pickleFile)
		# with open('pickle/normMean.pkl','wb') as pickleFile2:
		# 	pickle.dump(self.normMean,pickleFile2)
		# with open('pickle/window.pkl','wb') as pickleFile:
		# 	pickle.dump(self.window,pickleFile)
#################################################################
#################################################################

