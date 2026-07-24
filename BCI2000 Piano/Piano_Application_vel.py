##BCI Application Module for the Click Task with AR decoding

#Imports
import numpy as np
import scipy.stats
import time
import copy
import pickle
import random
import csv
import math
import os
from BCPy2000.GenericApplication import BciGenericApplication
from BCPy2000.AppTools.Boxes import Box
from BCPy2000.AppTools.Displays import fullscreen, init_screen
from BCPy2000.AppTools.Shapes import PolygonTexture, Disc, Block
from AppTools.StateMonitors import addstatemonitor, addphasemonitor
#################################################################
#################################################################

class BciApplication(BciGenericApplication):
    #############################################################
    def Description(self):
        return "click task with AR decoding"

    #############################################################

    def Construct(self):
        # format = "Section Datatype Name= Value DefaultValue LowRange HighRange //comment"
        self.define_param(
            "PythonApp:Design   int    ShowFixation=        0     0     0   1  // show a fixation point in the center (boolean)",
            "PythonApp:Design   int    ControlDim=          1     0     0   2  // Control Dimension: 1=1D-Horizontal, 2=1D-Vertical, 3=2D (enumeration)",
            "PythonApp:Screen   int    ScreenId=           -1    -1     %   %  // on which screen should the stimulus window be opened - use -1 for last",
            "PythonApp:Screen   float  WindowHeight=       100   100    %   %  // height of the stimulus window",
            "PythonApp:Screen   float  WindowWidth=        100   100    %   %  // width of the stimulus window",
            "PythonApp:Screen   float  WindowLeft=         100   100    %   %  // horizontal position of the stimulus window",
            "PythonApp:Screen   float  WindowTop=          100   100    %   %  // vertical position of the stimulus window",
            "PythonApp:Stimuli  int  TargetSize=            10  10  0   200 // diameter of target",
            "PythonApp:Stimuli  int  TargetSquareSize=      10  10  1   300 // side length of each target square",
            "PythonApp:Stimuli  int  TargetSquareSpacing=   10  10  0   300 // horizontal gap between adjacent target squares",
            "PythonApp:Stimuli  int  KeyWidth=              90  90  10  300 // piano key width",
            "PythonApp:Stimuli  int  KeyHeight=            320 320  10  800 // piano key height",
            "PythonApp:Stimuli  int  KeySpacing=             4   4   0   40 // gap between piano keys",
            "PythonApp:Feedback float CursorFriction=   1   1   0   10  //constant damping force on cursor movement",
            "PythonApp:Feedback float CursorViscosity=  1   1   0   10  //damping force proportional to velocity",
            "PythonApp:Feedback float CursorVelocity=   1   1   0   1000 //velocity of cursors",
            "PythonApp:Feedback int ControlType=        2   2   0   2   //1=force-based, 2=velocity-based, 0=let program choose",
            "PythonApp:Feedback float MaxArmVelocity=   30   30   0   1000 //maximum arm velocity in key widths per update",
            "PythonApp:Feedback int PosReset=          1   1   0   1 // reset arm start position from ArmStartIdxSeq (boolean)",
            "PythonApp:Feedback int BalancedLabel=          1   1   0   1 // balanced left/right/rest labels for calibration (boolean)",
            "PythonApp:Feedback int FreePlaying=          0   0   0   1 // free playing mode (boolean)",
            "PythonApp:Feedback int SongList=          0   0   0   1 // play songs (boolean)",
            "PythonApp:Feedback int Copilot=          0   0   0   1 // play songs with the copilot guidance (boolean)",
            "PythonApp:Feedback int ShowCopilotStatus=          0   0   0   1 // show copilot status or not (boolean)",
            "PythonApp:Feedback float CopilotThreshold=          0.50   0.50   0   1 // minimum song posterior for copilot assistance",
            "PythonApp:Feedback float CopilotMaxAssist=          1.00   1.00   0   1 // maximum copilot control fraction",
            "PythonApp:Feedback float CopilotAssistGain=         1.00   1.00   0   5 // gain from posterior probability to assist fraction",
            "PythonApp:Feedback float CopilotArmAttractGain=     50.00   50.00   0   100 // velocity gain for copilot arm attraction",
            "PythonApp:Feedback float CopilotSubjectMoveProb=    0.80   0.80   0   1 // likelihood model probability that subject covers target",
            "PythonApp:Feedback float CopilotSubjectFingerProb=  0.60   0.60   0   1 // likelihood model probability that subject presses target finger",
            "PythonApp:Feedback string CopilotProbModel=	exp % % %	//the key probability model, exponential or linear",
            "PythonApp:Feedback int ContinuousFeedback=     1   1       0   1  // show continuous finger feedback (boolean)",
            "PythonApp:Feedback int playSound=     1   1       0   1  // play sound (boolean)",

            "PythonApp:Paradigm float MoveTime=		1.0	1.0	0.0	60.0	//Time (s) for arm movement",
            "PythonApp:Paradigm float PressTime=		1.0	1.0	0.0	60.0	//Time (s) for finger press",
            "PythonApp:Paradigm int ResultHoldTime=    200  200  0   5000 //Time in ms to hold arm/finger result before next task",

            "PythonApp:Click float NewTargetDistance=	0.35	0.35	0	0.5	// distance between successive targets (fraction of screen)",
            "PythonApp:Click int ClickRadius=			37	37	0	2100	//minimum distance between cursor and target for successful click",
            "PythonApp:Click float ClickThreshold=		2	2	0	100		//z-scored threshold for click signal",
            "PythonApp:Click float InterClickTime=		1.0	1.0	0.0	60.0	//Time (s) between clicks",
            "PythonApp:Click int Resistance=      1 1 1 100    //Gain to move cursor towards center"

            )



        self.define_state(
            # "Target_PosX_u        16 0 0 0",
            # "Target_PosY_u        16 0 0 0",
            # "Target_Number		  16 0 0 0",
            # "Click              16 0 0 0",
            # "SignedOffset       16 32767 0 0",
            # "FloatScalar        16 10000 0 0",
            # "BaselineOn   1 0 0 0",
            # "StartCueOn   1 0 0 0",
            # "StopCueOn    1 0 0 0",
            # "Feedback     1 0 0 0",   # bells? whistles?

            # "FingerTask     1 0 0 0",
            # "ArmTask     1 0 0 0",
            # "FingerTarget   4 0 0 0",
            # "ArmTarget   4 0 0 0",
            # "FingerPred 4 0 0 0",
            # "ArmPred_X  16 0 0 0",
            # "Raw_ArmPred_X  16 0 0 0",
            
            "ArmCurrentIndex   4 0 0 0",
            "targetKeyIndex   4 0 0 0",
            "pressedKeyIndex   4 0 0 0",
            "CopilotFingerPred   4 0 0 0",
            "FingerMovePhase     1 0 0 0",
        )

    #############################################################

    ##Preflight is the first thing run upon starting up BCI2000
    def Preflight(self, sigprops):
    	#Set number of input signals, 2 in this case
        self.nclasses = 6
        self.ndim = 2
        self.targetNumber = 0

        if not self.in_signal_dim[0] in (self.nclasses,):
            raise EndUserError('%d-channel input expected, got %d' % (self.nclasses,self.in_signal_dim[0]))

        #Get screen size from parameters
        # screenid = int(self.params['ScreenId'])  # ScreenId 0 is the first screen, 1 the second, -1 the last
        # height = int(self.params['WindowHeight'])
        # width = int(self.params['WindowWidth'])
        # left = int(self.params['WindowLeft'])
        # top = int(self.params['WindowTop'])

        # b = Box(size=[height, width], position=(left + width/2, top + height/2), sticky=True)
        # init_screen(b)


        screenid = int(self.params['ScreenId'])  # ScreenId 0 is the first screen, 1 the second, -1 the last
        height = int(self.params['WindowHeight'])
        width = int(self.params['WindowWidth'])
        left = int(self.params['WindowLeft'])
        top = int(self.params['WindowTop'])
        try:
            b = fullscreen(scale=1.0, id=screenid)
        except TypeError:
            try:
                b = fullscreen()
            except Exception:
                b = Box(size=[height, width], position=(left + width/2, top + 480), sticky=True)
        init_screen(b)

        self.newTargetDistance = float(self.params['NewTargetDistance'])*min(height,width)
        self.clickThreshold = float(self.params['ClickThreshold'])

    #############################################################

    #Function to export floats as BCI2000 states, multiply by a factor of 10, make sure the result is within uint16 size
    def exportFloat(self,stateKey,value):
        #offset = self.states['SignedOffset']
        offset = (2**31 - 1)
        multiplier = self.states['FloatScalar']
        lowerLimit = 0
        upperLimit = 2**32 - 1
        intToExport = value*multiplier + offset

        if intToExport < lowerLimit:
            intToExport = lowerLimit
        elif intToExport > upperLimit:
            #intToExport = upperLimit
            while intToExport > upperLimit:
                intToExport /= 10.0

        self.states[stateKey] = int(intToExport)

    #############################################################

    def setTargetState(self, stateName):
        self.targetStateName = stateName
        self.refreshTargetVisibility()

    def getArmWindowKeyIndices(self, start_index):
        center_index = int(np.clip(start_index, self.minArmCenterIndex, self.maxArmCenterIndex))
        return [center_index - 1, center_index, center_index + 1]
    
    def getExtendedArmWindowKeyIndices(self, start_index):
        center_index = int(np.clip(start_index, self.minArmCenterIndex, self.maxArmCenterIndex))
        return [center_index - 2, center_index - 1, center_index, center_index + 1, center_index + 2]
    
    def getClosestArmWindowIndex(self, mapped_position):
        key_index = np.rint((mapped_position - self.keyPositions[0, 0]) / self.key_step)
        return int(np.clip(key_index, self.minArmCenterIndex, self.maxArmCenterIndex))

    def getArmKeyPosition(self, key_index):
        key_index = int(np.clip(key_index, self.minArmCenterIndex, self.maxArmCenterIndex))
        return float(self.keyPositions[key_index, 0])

    def setRoboHandPosition(self, x_position):
        self.currentRoboX = float(np.clip(
            x_position,
            self.keyPositions[self.minArmCenterIndex, 0],
            self.keyPositions[self.maxArmCenterIndex, 0],
        ))
        if hasattr(self, 'cursorState'):
            self.cursorState[0, 0] = self.currentRoboX
            self.cursorState[1:, 0] = 0
        if hasattr(self, 'stimuli') and 'robo_hand' in self.stimuli:
            self.stimuli['robo_hand'].pos = (self.currentRoboX, 0.0)

    def setArmStartFromIndex(self, key_index):
        self.armStartWindowIndex = int(np.clip(key_index, self.minArmCenterIndex, self.maxArmCenterIndex))
        self.armStartPos = self.getArmKeyPosition(self.armStartWindowIndex)

    def setNextArmStartPosition(self):
        if int(self.params['PosReset']) and not int(self.params['FreePlaying']):
            target_position = self.getArmKeyPosition(self.activeTargetIndex)
            self.setRoboHandPosition(target_position)
            self.currentArmWindowIndex = self.activeTargetIndex
            next_trial_index = self.innerTrialCount
            if next_trial_index < self.innerTrialNum:
                self.setArmStartFromIndex(self.ArmStartIdxSeq[next_trial_index])
            else:
                self.setArmStartFromIndex(self.activeTargetIndex)
        else:
            # nearest_index = self.getClosestArmWindowIndex(self.currentRoboX)
            self.setArmStartFromIndex(self.currentArmWindowIndex)
            self.setRoboHandPosition(self.armStartPos)
            self.currentArmWindowIndex = self.armStartWindowIndex

    # def getArmSignalX(self, arm_signal):
    #     dt = 1/60
    #     mapped_position = self.armStartPos + float(arm_signal) * float(self.params['CursorVelocity']) * self.key_step
    #     max_velocity = float(self.params['MaxArmVelocity']) * dt
    #     current_position = float(getattr(self, 'currentRoboX', self.armStartPos))
    #     mapped_position = float(np.clip(
    #         mapped_position,
    #         current_position - max_velocity,
    #         current_position + max_velocity,
    #     ))
    #     mapped_position = float(np.clip(
    #         mapped_position,
    #         self.keyPositions[self.minArmCenterIndex, 0],
    #         self.keyPositions[self.maxArmCenterIndex, 0],
    #     ))
    #     return mapped_position
    
    def updateObjectPosition(self, objectState, dt=1.0/60):
        objectState[0, :] = objectState[1, :] * dt + objectState[0, :]
        if hasattr(self, 'keyPositions'):
            objectState[0, 0] = np.clip(
                objectState[0, 0],
                self.keyPositions[self.minArmCenterIndex, 0],
                self.keyPositions[self.maxArmCenterIndex, 0],
            )
        if np.abs(objectState[0, 1]) >= self.screenSize[1] / 2.0:
            objectState[0, 1] = np.sign(objectState[0, 1]) * self.screenSize[1] / 2.0
        return objectState


    def updateObjectMovement(self, objectState, externalInput, friction, viscosity, controlType, dt=1.0/40):
        if controlType == 0:
            controlType = 2 # select default
        elif controlType == 2: # regular velocity-based control
            velocity = np.asarray(externalInput, dtype=float).reshape(-1)
            objectState[2, :] = 0
            objectState[1, :] = velocity[:2]
        else:
            raise Exception('Invalid control type')
        return objectState
    
    def updateRoboHandPosition(self):
        if not hasattr(self, 'stimuli') or 'robo_hand' not in self.stimuli:
            return
        if getattr(self, 'currentTask', 'Arm') == 'Arm':
            self.currentRoboX = self.cursorState[0, 0]
        if getattr(self, 'currentTask', 'Arm') == 'ArmHold': # move to the closest key
            # target_position = self.getArmKeyPosition(self.getClosestArmWindowIndex(self.cursorState[0, 0]))
            target_position = self.getArmKeyPosition(self.currentArmWindowIndex)
            current_position = float(getattr(self, 'currentRoboX', self.cursorState[0, 0]))
            max_step = max(0.0, float(self.params['MaxArmVelocity'])) / 60.0
            self.currentRoboX = current_position + float(np.clip(
                target_position - current_position,
                -max_step,
                max_step,
            ))
            self.cursorState[1:, 0] = 0
        
        self.currentRoboX = float(np.clip(
            self.currentRoboX,
            self.keyPositions[self.minArmCenterIndex, 0],
            self.keyPositions[self.maxArmCenterIndex, 0],
        ))
        self.cursorState[0, 0] = self.currentRoboX
        self.stimuli['robo_hand'].pos = (self.currentRoboX, 0.0)

        
    def updateActiveTargetPosition(self):
        if not hasattr(self, 'stimuli'):
            return
        if 'target_arrow' in self.stimuli and hasattr(self, 'fingerTargetKeyIndex'):
            self.stimuli['target_arrow'].pos = (self.keyPositions[self.fingerTargetKeyIndex, 0], self.arrowY)
        
        # self.refreshTargetVisibility()
        self.updateFingerTargetPosition()

    def updateFingerTargetPosition(self):
        self.refreshFingerTargetVisibility()

    def refreshTargetVisibility(self):
        isVisible = getattr(self, 'targetsVisible', False)
        target_window = getattr(self, 'activeTargetIndex', -1)
        current_window = getattr(self, 'currentArmWindowIndex', -1)
        if 'robo_hand' in self.stimuli:
            self.stimuli['robo_hand'].on = bool(isVisible)
        for keyIndex in range(self.numKeys):
            self.stimuli['key_base_%d' % keyIndex].on = bool(isVisible)
            self.stimuli['key_label_%d' % keyIndex].on = bool(isVisible)
            if not int(self.params['FreePlaying']):
                self.stimuli['key_target_%d' % keyIndex].on = bool(
                    isVisible and keyIndex in self.getArmWindowKeyIndices(target_window) and (not self.targetStateName == 'hit') and (not self.targetStateName == 'miss')
                )
            else:
                if getattr(self, 'currentTask', 'Idle') in ['ArmHold', 'Finger', 'FingerHold']:
                    self.stimuli['key_target_%d' % keyIndex].on = bool(
                        isVisible and keyIndex in self.getArmWindowKeyIndices(target_window) and (not self.targetStateName == 'hit') and (not self.targetStateName == 'miss') 
                    )
                else:
                    self.stimuli['key_target_%d' % keyIndex].on = bool(
                        isVisible and keyIndex in self.getExtendedArmWindowKeyIndices(target_window) and (not self.targetStateName == 'hit') and (not self.targetStateName == 'miss') and self.currentTask in ['Arm']
                    )
            self.stimuli['key_target_hit_%d' % keyIndex].on = bool(
                isVisible and self.targetStateName == 'hit' and keyIndex in self.getArmWindowKeyIndices(target_window) and self.currentTask in ['Arm', 'ArmHold']
            )
            self.stimuli['key_target_miss_%d' % keyIndex].on = bool(
                isVisible and self.targetStateName == 'miss' and keyIndex in self.getArmWindowKeyIndices(target_window) and self.currentTask in ['Arm', 'ArmHold']
            )
            # self.stimuli['key_current_%d' % keyIndex].on = bool(
            #     isVisible and self.targetStateName in ['normal', 'light'] and keyIndex in self.getArmWindowKeyIndices(current_window) and self.currentTask in ['Arm', 'ArmHold']
            # )
            
        for blackKeyIndex in getattr(self, 'blackKeyIndices', []):
            self.stimuli['black_key_%d' % blackKeyIndex].on = bool(isVisible)
        if 'target_arrow' in self.stimuli:
            self.stimuli['target_arrow'].on = bool(
                isVisible and getattr(self, 'currentTask', 'Idle') in ['Arm', 'ArmHold', 'Finger', 'FingerHold']
            )
    def setTargetVisibility(self, isVisible):
        self.targetsVisible = isVisible
        self.refreshTargetVisibility()

    def setFingerTargetVisibility(self, isVisible):
        self.fingerTargetsVisible = isVisible
        self.refreshFingerTargetVisibility()

    def setFingerTargetState(self, stateName):
        self.fingerTargetStateName = stateName
        self.refreshFingerTargetVisibility()

    def refreshFingerTargetVisibility(self):
        isVisible = getattr(self, 'fingerTargetsVisible', False)
        active_state = getattr(self, 'fingerTargetStateName', 'light')
        active_index = getattr(self, 'fingerTargetKeyIndex', -1)
        if int(self.params['FreePlaying']):
            active_index = int(np.clip(self.fingerTargetIndex, 0, 2)) + self.activeTargetIndex - 1
        for stateName in ['light', 'hit', 'miss']:
            for keyIndex in range(self.numKeys):
                stimName = 'finger_choice_%s_%d' % (stateName, keyIndex)
                self.stimuli[stimName].on = bool(
                    isVisible and stateName == active_state and keyIndex == active_index
                )

    def getClosestTarget(self):
        return 0.0, int(getattr(self, 'currentArmWindowIndex', 0))

    def pickNewTarget(self):
        if self.innerTrialCount >= self.innerTrialNum:
            return False
        self.activeTargetIndex = int(self.ArmTargetSeq[self.innerTrialCount])
        if int(self.params['PosReset']) and not int(self.params['FreePlaying']):
            self.activeArmStartIdx = int(self.ArmStartIdxSeq[self.innerTrialCount])
            self.activeArmKeyDiff = int(self.ArmKeyDiffSeq[self.innerTrialCount])
        else:
            self.activeArmStartIdx = int(self.armStartWindowIndex)
            self.activeArmKeyDiff = int(self.activeTargetIndex - self.activeArmStartIdx)

        self.fingerTargetIndex = int(self.FingerTargetSeq[self.innerTrialCount])
        self.fingerTargetKeyIndex = self.activeTargetIndex + (self.fingerTargetIndex - 1)
        if int(self.params['FreePlaying']) and int(self.params['SongList']):
            self.updateCopilotPolicy()
        self.updateActiveTargetPosition()
        return True
    
    def updateNewTarget(self):
        self.fingerTargetKeyIndex = self.activeTargetIndex + (self.fingerTargetIndex - 1)
        self.activeTargetIndex = self.currentArmWindowIndex
        self.fingerTargetIndex = self.fingerTargetKeyIndex - self.activeTargetIndex + 1
        self.updateActiveTargetPosition()
        return True
        

    def playFingerFeedbackNote(self, finger_out):
        key_index = int(np.clip(self.activeTargetIndex + (finger_out - 1), 0, self.numKeys - 1))
        note_sounds = getattr(self, 'noteSounds', None)
        if not note_sounds:
            return
        for note_sound in note_sounds:
            try:
                note_sound.stop()
            except Exception:
                pass

        note_sound = note_sounds[key_index]
        try:
            if hasattr(note_sound, 'seek'):
                note_sound.seek(0)
            note_sound.play()
        except Exception:
            pass

    
    def parseKeySequenceText(self, raw_sequence):
        tokens = raw_sequence.replace(',', ' ').replace(';', ' ').split()
        label_to_index = dict((label.upper(), index) for index, label in enumerate(self.keyLabels))
        index_sequence = []
        for token in tokens:
            note = ''.join(ch for ch in token.upper() if ch.isalpha())
            if note in label_to_index:
                index_sequence.append(label_to_index[note])
            elif token.isdigit():
                index_sequence.append(int(np.clip(int(token), 0, self.numKeys - 1)))
        return index_sequence

    def parseSongSequenceLine(self, line, song_id):
        if '\t' in line:
            title, sequence_text = line.split('\t', 1)
        else:
            title = 'Song_%d' % song_id
            sequence_text = line
            for index in range(len(line) - 1):
                if line[index].isspace() and line[index + 1].isspace():
                    title = line[:index].strip() or title
                    sequence_text = line[index:].strip()
                    break
        sequence = self.parseKeySequenceText(sequence_text)
        if not sequence:
            return None
        return {
            'song_id': int(song_id),
            'title': title.strip() or ('Song_%d' % song_id),
            'sequence': sequence,
        }

    def loadKeySequenceBank(self):
        sequence_path = 'C:\\Users\\HeLab\\Desktop\\BCI_DL\\BCI2000\\python\\ArmFingerRobo\\piano_note_sequence_50_clipped.txt'
        sequences = []
        try:
            with open(sequence_path, 'r') as sequence_file:
                for line in sequence_file:
                    line = line.strip()
                    if not line:
                        continue
                    sequence_text = line.split('\t', 1)[-1].strip()
                    if sequence_text == line:
                        for index in range(len(line) - 1):
                            if line[index].isspace() and line[index + 1].isspace():
                                sequence_text = line[index:].strip()
                                break
                    sequence = self.parseKeySequenceText(sequence_text)
                    if sequence:
                        sequences.append(sequence)
        except IOError:
            pass
        return sequences

    def loadSongSequenceBank(self):
        sequence_path = 'C:\\Users\\HeLab\\Desktop\\BCI_DL\\BCI2000\\python\\ArmFingerRobo\\piano_note_sequence_50_clipped.txt'
        
        songs = []
        try:
            with open(sequence_path, 'r') as sequence_file:
                songs = []
                for line in sequence_file:
                    line = line.strip()
                    if not line:
                        continue
                    song = self.parseSongSequenceLine(line, len(songs))
                    if song is not None:
                        songs.append(song)
            if songs:
                return songs
        except IOError:
            pass
        return [{'song_id': 0, 'title': 'Center key fallback', 'sequence': [self.numKeys // 2]}]

    def stablePosteriorFromLog(self, log_values):
        log_values = np.asarray(log_values, dtype=float)
        finite = np.isfinite(log_values)
        if not np.any(finite):
            return np.ones(len(log_values), dtype=float) / max(len(log_values), 1)
        shifted = np.exp(log_values - np.max(log_values[finite]))
        shifted[~finite] = 0.0
        total = shifted.sum()
        if total <= 0:
            return np.ones(len(log_values), dtype=float) / max(len(log_values), 1)
        return shifted / total

    def nearbyKeyIndices(self, target_key, distances=(1, 2)):
        nearby = []
        for distance in distances:
            for key_index in (target_key - distance, target_key + distance):
                if 0 <= key_index < self.numKeys and key_index != target_key:
                    nearby.append(key_index)
        return sorted(set(nearby))

    def subjectEmissionDistribution(self, target_key):
        probs = np.zeros(self.numKeys, dtype=float)
        target_key = int(np.clip(target_key, 0, self.numKeys - 1))
        p_move = float(np.clip(float(self.params['CopilotSubjectMoveProb']), 0.0, 1.0))
        p_finger = float(np.clip(float(self.params['CopilotSubjectFingerProb']), 0.0, 1.0))
        probs[target_key] += p_move * p_finger
        nearby = self.nearbyKeyIndices(target_key)
        if nearby:
            probs[nearby] += p_move * (1.0 - p_finger) / len(nearby)
        wrong = [key_index for key_index in range(self.numKeys) if key_index != target_key]
        if wrong:
            probs[wrong] += (1.0 - p_move) / len(wrong)
        total = probs.sum()
        return probs / total if total > 0 else np.ones(self.numKeys, dtype=float) / self.numKeys

    def copilotEmissionDistribution(self, policy_key):
        probs = np.zeros(self.numKeys, dtype=float)
        if policy_key is None:
            return probs
        policy_key = int(np.clip(policy_key, 0, self.numKeys - 1))
        probs[policy_key] = 1.0
        return probs

    def mixtureEmissionDistribution(self, subject_target_key, policy_key, assist_strength):
        subject_probs = self.subjectEmissionDistribution(subject_target_key)
        assist_strength = float(np.clip(assist_strength, 0.0, float(self.params['CopilotMaxAssist'])))
        if policy_key is None or assist_strength <= 0:
            return subject_probs
        copilot_probs = self.copilotEmissionDistribution(policy_key)
        probs = (1.0 - assist_strength) * subject_probs + assist_strength * copilot_probs
        total = probs.sum()
        return probs / total if total > 0 else subject_probs

    def initializeCopilotTrial(self):
        songs = getattr(self, 'SongSeqBank', [])
        n_songs = max(len(songs), 1)
        self.copilotLogPosterior = np.full(n_songs, -math.log(n_songs), dtype=float)
        self.copilotPosterior = self.stablePosteriorFromLog(self.copilotLogPosterior)
        self.copilotTopSongId = int(np.argmax(self.copilotPosterior))
        self.copilotTopSongProb = float(self.copilotPosterior[self.copilotTopSongId])
        self.copilotActive = False
        self.copilotAssistStrength = 0.0
        self.copilotPolicySongId = -1
        self.copilotPolicyKey = None
        self.copilotArmVelocity = 0.0
        self.copilotOriginalFingerOut = 10
        self.copilotFinalFingerOut = 10
        self.copilotOriginalCorrectCount = 0
        self.copilotCorrectedCorrectCount = 0
        self.copilotTotalStepCount = 0
        self.updateCopilotPolicy()

    def updateCopilotPolicy(self):
        songs = getattr(self, 'SongSeqBank', [])
        if not songs:
            self.copilotActive = False
            self.copilotAssistStrength = 0.0
            self.copilotPolicySongId = -1
            self.copilotPolicyKey = None
            return
        posterior = getattr(self, 'copilotPosterior', np.ones(len(songs), dtype=float) / len(songs))
        top_song_id = int(np.argmax(posterior))
        top_prob = float(posterior[top_song_id])
        threshold = float(self.params['CopilotThreshold'])
        step_index = int(getattr(self, 'innerTrialCount', 0))
        active = (
            int(self.params['FreePlaying'])
            and int(self.params['SongList'])
            and int(self.params['Copilot'])
            and top_prob >= threshold
            and step_index < len(songs[top_song_id]['sequence'])
        )
        assist_strength = 0.0
        policy_key = None
        if active:
            assist_strength = min(float(self.params['CopilotMaxAssist']), float(self.params['CopilotAssistGain']) * top_prob)
            policy_key = int(songs[top_song_id]['sequence'][step_index])
        self.copilotTopSongId = top_song_id
        self.copilotTopSongProb = top_prob
        self.copilotActive = bool(active)
        self.copilotAssistStrength = float(assist_strength)
        self.copilotPolicySongId = top_song_id if active else -1
        self.copilotPolicyKey = policy_key

    def updateCopilotStatusText(self):
        if 'copilot_status' not in self.stimuli:
            return
        songs = getattr(self, 'SongSeqBank', [])
        top_song_id = int(getattr(self, 'copilotTopSongId', -1))
        top_song = songs[top_song_id]['title'] if 0 <= top_song_id < len(songs) else ''
        target_song = getattr(self, 'currentSong', {}).get('title', '')
        status_text = (
            'Copilot: %s\nTarget song: %s\nTop song: %s\nProbability: %.3f\n'
            'Subject velocity: %.3f\nCopilot velocity: %.3f'
        ) % (
            'active' if getattr(self, 'copilotActive', False) else 'inactive',
            target_song,
            top_song,
            float(getattr(self, 'copilotTopSongProb', 0.0)),
            float(getattr(self, 'lastSubjectArmVelocity', 0.0)),
            float(getattr(self, 'copilotArmVelocity', 0.0)),
        )
        if status_text != getattr(self, 'copilotStatusText', ''):
            self.copilotStatusText = status_text
            self.stimuli['copilot_status'].setText(status_text)

    def getCopilotArmVelocity(self):
        self.copilotArmVelocity = 0.0
        if not getattr(self, 'copilotActive', False) or self.copilotPolicyKey is None:
            return 0.0
        target_position = self.getArmKeyPosition(self.copilotPolicyKey)
        current_position = float(getattr(self, 'currentRoboX', self.cursorState[0, 0]))
        normalized_distance = (target_position - current_position) / float(self.key_step)
        max_velocity = max(0.0, float(self.params['MaxArmVelocity']))
        velocity = (
            normalized_distance
            * float(self.params['CopilotArmAttractGain'])
            * float(self.copilotAssistStrength)
        )
        self.copilotArmVelocity = float(np.clip(velocity, -max_velocity, max_velocity))
        return self.copilotArmVelocity
    def getCopilotFingerOut(self, finger_probs):
        eeg_probs = np.asarray(finger_probs, dtype=float).reshape(-1)
        total = float(eeg_probs.sum())
        if total > 0.0:
            eeg_probs = eeg_probs / total
        eeg_finger_out = int(np.argmax(eeg_probs))
        self.copilotOriginalFingerOut = eeg_finger_out
        if not getattr(self, 'copilotActive', False) or self.copilotPolicyKey is None:
            self.copilotFinalFingerOut = eeg_finger_out
            return eeg_finger_out
        copilot_finger_out = int(np.clip(int(self.copilotPolicyKey) - int(self.currentArmWindowIndex) + 1, 0, 2))
        assist = float(np.clip(self.copilotAssistStrength, 0.0, float(self.params['CopilotMaxAssist'])))
        mixed_probs = (1.0 - assist) * eeg_probs
        mixed_probs[copilot_finger_out] += assist
        self.copilotFinalFingerOut = int(np.argmax(mixed_probs))
        return self.copilotFinalFingerOut

    # def updateCopilotPosterior(self, observed_key):
    #     songs = getattr(self, 'SongSeqBank', [])
    #     if not songs:
    #         return
    #     observed_key = int(np.clip(observed_key, 0, self.numKeys - 1))
    #     step_index = int(getattr(self, 'innerTrialCount', 0))
    #     policy_key = getattr(self, 'copilotPolicyKey', None)
    #     assist_strength = float(getattr(self, 'copilotAssistStrength', 0.0)) if getattr(self, 'copilotActive', False) else 0.0
    #     epsilon = 1e-9
    #     for song in songs:
    #         song_id = int(song['song_id'])
    #         if step_index >= len(song['sequence']):
    #             emission_prob = epsilon
    #         else:
    #             candidate_key = int(song['sequence'][step_index])
    #             probs = self.mixtureEmissionDistribution(candidate_key, policy_key, assist_strength)
    #             emission_prob = max(float(probs[observed_key]), epsilon)
    #         self.copilotLogPosterior[song_id] += math.log(emission_prob)
    #     self.copilotPosterior = self.stablePosteriorFromLog(self.copilotLogPosterior)
    #     self.copilotTopSongId = int(np.argmax(self.copilotPosterior))
    #     self.copilotTopSongProb = float(self.copilotPosterior[self.copilotTopSongId])

    def updateCopilotPosterior(self, observed_key):
        songs = getattr(self, 'SongSeqBank', [])
        if not songs:
            return
        observed_key = int(np.clip(observed_key, 0, self.numKeys - 1))
        step_index = int(getattr(self, 'innerTrialCount', 0))
        key_indices = np.arange(self.numKeys, dtype=float)
        epsilon = 1e-9
        for song in songs:
            song_id = int(song['song_id'])
            if step_index >= len(song['sequence']):
                emission_prob = epsilon
            else:
                target_key = int(np.clip(song['sequence'][step_index], 0, self.numKeys - 1))
                distances = np.abs(key_indices - target_key)
                prob_model = str(self.params["CopilotProbModel"]).strip().lower()
                if prob_model in ("exp", "exponential"):
                    distance_probs = np.exp(-distances)
                elif prob_model in ("lin", "linear"):
                    distance_probs = np.maximum(0.0, 1.0 - distances / 4.0)
                else:
                    distance_probs = np.exp(-distances)
                emission_prob = max(float(distance_probs[observed_key] / distance_probs.sum()), epsilon)
            self.copilotLogPosterior[song_id] += math.log(emission_prob)
        self.copilotPosterior = self.stablePosteriorFromLog(self.copilotLogPosterior)
        self.copilotTopSongId = int(np.argmax(self.copilotPosterior))
        self.copilotTopSongProb = float(self.copilotPosterior[self.copilotTopSongId])
        self.updateCopilotPolicy()

    def summarizeCopilotPosterior(self):
        songs = getattr(self, 'SongSeqBank', [])
        posterior = getattr(self, 'copilotPosterior', [])
        parts = []
        for song, prob in zip(songs, posterior):
            parts.append('%s:%.4f' % (song['title'], float(prob)))
        return '|'.join(parts)

    def appendCopilotStepLog(self, row):
        if not getattr(self, 'copilotStepLogPath', ''):
            return
        fieldnames = [
            'timestamp_ms', 'trial_count', 'inner_step', 'selected_song_id', 'selected_song',
            'target_key_index', 'target_key_label', 'arm_start_index', 'arm_window_index',
            'arm_position_x', 'subject_arm_signal', 'subject_arm_velocity', 'copilot_arm_velocity',
            'finger_target_index', 'finger_target_key_index', 'original_finger_out',
            'final_finger_out', 'pressed_key_index', 'original_finger_correct',
            'final_finger_correct', 'original_note_correct', 'final_note_correct',
            'copilot_enabled', 'copilot_active', 'assist_strength',
            'policy_song_id', 'policy_song', 'policy_key_index',
            'top_song_id_before', 'top_song_before', 'top_prob_before',
            'selected_song_prob_before', 'top_song_id_after', 'top_song_after',
            'top_prob_after', 'selected_song_prob_after', 'posterior',
            'original_finger_correct_count', 'final_finger_correct_count', 'copilot_step_count',
        ]
        write_header = not os.path.exists(self.copilotStepLogPath)
        try:
            with open(self.copilotStepLogPath, 'a', newline='') as log_file:
                writer = csv.DictWriter(log_file, fieldnames=fieldnames)
                if write_header:
                    writer.writeheader()
                writer.writerow(row)
        except IOError:
            pass

    def Initialize(self, indim, outdim):
    	#Initialize function is run upon clicking "Set Config" in BCI2000
        import psychopy.visual as psypy
        import BCPy2000.PsychoPyRenderer as renderer

        scrw,scrh = self.screen.size
        scrsiz = min(scrw,scrh)
        print(scrw)
        print(scrh)
        self.screenSize = self.screen.size
        # print(type(self.screenSize[0]))
        siz = (scrsiz, scrsiz)

        # b = Box(size=siz, position=(scrw/2.0,scrh/2.0), sticky=True)

        center = (0,0)

        self.numKeys = 11
        self.numArmWindows = self.numKeys - 2
        self.minArmCenterIndex = 1
        self.maxArmCenterIndex = self.numKeys - 2
        self.minKeyIdx = 2
        self.maxKeyIdx = self.numKeys - 3
        self.keyLabels = ['', '', 'C', 'D', 'E', 'F', 'G', 'A', 'B', '', '']
        self.noteFrequencies = [233.08, 246.94, 261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25, 554.36]
        
        import psychopy.sound as psysound
        self.noteSounds = [
            psysound.Sound(value=frequency, secs=1)
            for frequency in self.noteFrequencies
        ]
        
        key_width = int(self.params['KeyWidth'])
        key_height = int(self.params['KeyHeight'])
        key_spacing = int(self.params['KeySpacing'])
        key_step = key_width + key_spacing
        self.key_step = key_step
        self.stimulusYOffset = key_height / 2.0
        stimulus_center = (0, self.stimulusYOffset)
        x_offset = -((self.numKeys - 1) * key_step) / 2.0
        self.keyPositions = np.array([
            (x_offset + keyIndex * key_step, self.stimulusYOffset)
            for keyIndex in range(self.numKeys)
        ])
        self.arrowY = self.stimulusYOffset + key_height * 0.62
        
        self.blackKeyIndices = [0, 2, 3, 5, 6, 7, 9]
        black_key_width = key_width * 0.58
        black_key_height = key_height * 0.62
        black_key_y = self.stimulusYOffset + (key_height - black_key_height) / 2.0

        self.activeTargetIndex = 10
        self.activeArmStartIdx = 10
        self.activeArmKeyDiff = 10
        self.currentArmWindowIndex = self.numKeys // 2
        self.armStartWindowIndex = self.numKeys // 2
        self.armStartPos = 0
        self.targetsVisible = False
        self.fingerTargetsVisible = False
        self.targetStateName = 'normal'
        self.hitState = 0
        self.missState = 0
        self.clickSum = 0
        self.clickFlag = 0

        self.normSig = np.zeros((2,1))

        # let's have a black background
        self.screen.color = (0.17,0.17,0.17)

        # OK, now register all those stimuli, plus a few more, with the framework
        # Original single-target stimulus retained for reference:
        # self.stimulus('target',   z=2,   stim=psypy.Circle(self.screen.screen, pos=center, radius=int(self.params['TargetSize']),fillColor=(0.5,0.5,0.5)), on=False)
        self.fingerLightColor = (0.3, 1.0, 0.3)
        base_fill = (1, 1, 1)
        base_edge = (0, 0, 0)
        target_edge = (0, 0.4, 0)
        current_fill = (0.6, 1.0, 0.6)

        for keyIndex, keyPos in enumerate(self.keyPositions):
            self.stimulus(
                'key_base_%d' % keyIndex,
                z=5,
                stim=psypy.Rect(
                    self.screen.screen,
                    pos=keyPos,
                    width=key_width,
                    height=key_height,
                    fillColor=base_fill,
                    lineColor=base_edge,
                    lineWidth=0,
                ),
                on=False,
            )
            self.stimulus(
                'key_label_%d' % keyIndex,
                z=11,
                stim=psypy.TextBox(
                    self.screen.screen,
                    text=self.keyLabels[keyIndex],
                    size=[key_width,key_width],
                    pos=(keyPos[0], keyPos[1] - key_height * 0.42),
                    units='pix',
                ),
                on=False,
            )
            # self.stimulus(
            #     'key_current_%d' % keyIndex,
            #     z=4,
            #     stim=psypy.Rect(
            #         self.screen.screen,
            #         pos=keyPos,
            #         width=key_width,
            #         height=key_height,
            #         fillColor=None,
            #         lineColor=target_edge,
            #         lineWidth=10,
            #         opacity=1.0,
            #     ),
            #     on=False,
            # )
            self.stimulus(
                'key_target_hit_%d' % keyIndex,
                z=7,
                stim=psypy.Rect(
                    self.screen.screen,
                    pos=keyPos,
                    width=key_width,
                    height=key_height,
                    fillColor=(0, 1, 0),
                    lineColor=None,
                    lineWidth=0,
                    opacity=1.0,
                ),
                on=False,
            )
            self.stimulus(
                'key_target_miss_%d' % keyIndex,
                z=7,
                stim=psypy.Rect(
                    self.screen.screen,
                    pos=keyPos,
                    width=key_width,
                    height=key_height,
                    fillColor=(1, 0, 0),
                    lineColor=None,
                    lineWidth=0,
                    opacity=1.0,
                ),
                on=False,
            )
            self.stimulus(
                'key_target_%d' % keyIndex,
                z=8,
                stim=psypy.Rect(
                    self.screen.screen,
                    pos=keyPos,
                    width=key_width,
                    height=key_height,
                    fillColor=current_fill,
                    lineColor=None,
                    lineWidth=0,
                    opacity=0.7,
                ),
                on=False,
            )

        for blackKeyIndex in self.blackKeyIndices:
            left_key_pos = self.keyPositions[blackKeyIndex]
            right_key_pos = self.keyPositions[blackKeyIndex + 1]
            self.stimulus(
                'black_key_%d' % blackKeyIndex,
                z=11,
                stim=psypy.Rect(
                    self.screen.screen,
                    pos=((left_key_pos[0] + right_key_pos[0]) / 2.0, black_key_y),
                    width=black_key_width,
                    height=black_key_height,
                    fillColor=(-1, -1, -1),
                    lineColor=(-1, -1, -1),
                    lineWidth=2,
                ),
                on=False,
            )

        for stateName, fillColor in [('light', self.fingerLightColor), ('hit', (0, 1, 0)), ('miss', (1, 0, 0))]:
            for keyIndex, keyPos in enumerate(self.keyPositions):
                self.stimulus(
                    'finger_choice_%s_%d' % (stateName, keyIndex),
                    z=10,
                    stim=psypy.Rect(
                        self.screen.screen,
                        pos=keyPos,
                        width=key_width,
                        height=key_height,
                        fillColor=fillColor,
                        lineColor=None,
                        lineWidth=0,
                        opacity=1.0,
                    ),
                    on=False,
                )
        
        self.targetStateName = 'normal'
        self.stimulus('cue',      z=11,   stim=psypy.TextBox(self.screen.screen,text='Test', size = [200,100], pos=center, units='pix'), on=True)
        
        if int(self.params['FreePlaying']) and int(self.params['SongList']) and int(self.params['Copilot']) and int(self.params['ShowCopilotStatus']):
            self.copilotStatusText = ''
            self.stimulus(
                'copilot_status',
                z=14,
                stim=psypy.TextBox(
                self.screen.screen,
                text=' ',
                font_size=18,
                size=[460, 210],
                pos=(scrw / 2.0 - 250, scrh / 2.0 - 125),
                units='pix',
            ),
                on=True,
            )
        if int(self.params['FreePlaying']):
            self.stimulus(
                'target_arrow',
                z=13,
                stim=psypy.ShapeStim(
                    self.screen.screen,
                    vertices=[(-key_width * 0.25, 0), (key_width * 0.25, 0), (0, -key_width * 0.45)],
                    pos=(0, self.arrowY),
                    fillColor=(0, 1, 0),
                    lineColor=(0, 1, 0),
                    units='pix',
                ),
                on=False,
            )
        image_path = "C:\\Users\\HeLab\\Desktop\\BCI_DL\\BCI2000\\prog\\images\\RoboHand.png"
        img1 = psypy.ImageStim(
            self.screen.screen,
            image=image_path,
            size=[scrh, scrh],
            pos=center,
            units='pix',
        )
        self.stimulus('robo_hand',	z=12,	stim=img1, on = False)

        if int(self.params['ShowSignalTime']):
            # turn on state monitors iff the packet clock is also turned on
            addstatemonitor(self, 'Running', showtime=True)
            addstatemonitor(self, 'CurrentBlock')
            addstatemonitor(self, 'CurrentTrial')
            addstatemonitor(self, 'TargetClass')
            addstatemonitor(self, 'Learn')
            addphasemonitor(self, 'phase', showtime=True)

            m = addstatemonitor(self, 'fs_reg')
            m.func = lambda x: '% 6.1fHz' % x._regfs.get('SamplesPerSecond', 0)
            m.pargs = (self,)
            m = addstatemonitor(self, 'fs_avg')
            m.func = lambda x: '% 6.1fHz' % x.estimated.get('SamplesPerSecond',{}).get('global', 0)
            m.pargs = (self,)
            m = addstatemonitor(self, 'fs_run')
            m.func = lambda x: '% 6.1fHz' % x.estimated.get('SamplesPerSecond',{}).get('running', 0)
            m.pargs = (self,)
            m = addstatemonitor(self, 'fr_run')
            m.func = lambda x: '% 6.1fHz' % x.estimated.get('FramesPerSecond',{}).get('running', 0)
            m.pargs = (self,)

        self.distance = lambda a,b: np.sqrt((np.asarray(a-b)**2).sum(axis=-1))

        #Custom global variables

        self.bufferLength = int(self.params['BufferLength'])*25 #seconds * blocks per second
        self.buffer = np.array([])
        self.normalizationUpdateTime = float(self.params['NormalizationUpdateTime'])
        self.trialCount = 0
        self.timer = 0.0
        self.hitCountArm = 0
        self.missCountArm = 0
        self.hitCountFinger = 0
        self.missCountFinger = 0
        self.fingerTargetIndex = 10
        self.fingerTargetKeyIndex = 10
        self.fingerCurrentKeyIndex = 10
        self.fingerPhaseStartTime = 0
        self.fingerDecisionApplied = False
        self.fingerTargetStateName = 'light'
        self.resultHoldTimeMs = int(self.params['ResultHoldTime'])
        self.resultTimer = 0
        self.currentArmSignal = 0.0
        self.lastSubjectArmSignal = 0.0
        self.lastSubjectArmVelocity = 0.0
        self.innerTrialCount = 0
        self.ArmStartIdxSeq = []
        self.copilotStepLogPath = ''
        self.copilotActive = False
        self.copilotAssistStrength = 0.0
        self.copilotPolicySongId = -1
        self.copilotPolicyKey = None
        self.copilotArmVelocity = 0.0
        self.copilotOriginalFingerOut = 10
        self.copilotFinalFingerOut = 10
        self.copilotOriginalCorrectCount = 0
        self.copilotCorrectedCorrectCount = 0
        self.copilotTotalStepCount = 0
        self.currentSong = {'song_id': -1, 'title': '', 'sequence': []}
        self.cursorState = np.zeros((3,2)) # position, velocity, acceleration in 2D
        self.cursorForce = np.zeros( 2 )
        self.cursorState[0,:] = [0,0]

        self.currentRoboX = 0.0

        
        self.currentTask = 'Idle' # start with an idle state
        self.states['FingerTask'] = 0
        self.states['ArmTask'] = 0
        self.states['Idle'] = 1
    
        if int(self.params['SongList']):
            self.SongSeqBank = self.loadSongSequenceBank()
            # self.KeySeqBank = [song['sequence'] for song in self.SongSeqBank]
            self.availableSongSequences = self.SongSeqBank[:]
            # self.availableKeySequences = self.KeySeqBank[:]
            # random.shuffle(self.availableSongSequences)
            # random.shuffle(self.availableKeySequences)
            log_name = 'piano_copilot_results_%s.csv' % time.strftime('%Y%m%d_%H%M%S')
            data_dir = self.params['DataDirectory'] + '/' + self.params['SubjectName'] + self.params['SubjectSession']
            self.copilotStepLogPath = os.path.join(data_dir, log_name)



    #############################################################

    def StartRun(self):
        pass
    #############################################################

    #Setup the phases of the experiment
    #BCI2000 will keep track of the trial number by using the "new_trial" set in the last line
    def Phases(self) :
        self.phase(next='intertrial', duration=             500, name='startrun')
        self.phase(next='startcue',   duration=             100,    name='baseline')
        self.phase(next='gap',        duration=             1000,   name='startcue')
        self.phase(next='imagine',    duration=              100,   name='gap')
        self.phase(next='stopcue',    duration=             600000,  name='imagine')
        self.phase(next='intertrial', duration=             1000,   name='stopcue')
        self.phase(next='baseline',   duration=             2800,   name='intertrial')
        self.phase(next='intertrial', duration=             1000,   name='idle')
        self.design(start='startrun', new_trial='baseline', interblock='idle')

    #############################################################

    def Transition(self, phase):
    	#Called everytime a phase switches during the experiment
        # record what's going
        self.states['BaselineOn'] = int(phase in ['baseline'])
        self.states['StartCueOn'] = int(phase in ['startcue'])
        self.states['StopCueOn']  = int(phase in ['stopcue'])
        self.states['Feedback'] = int(phase in ['imagine'])
        self.stimuli['cue'].on = (phase in ['startcue', 'stopcue'])

        if phase == 'baseline':
            pass

        if phase == 'startcue':
            self.stimuli['cue'].AddDispatch(lambda: self.stimuli['cue'].setText('Start'))

        if phase == 'stopcue':
            self.stimuli['cue'].AddDispatch(lambda: self.stimuli['cue'].setText('Stop'))
            self.trialCount += 1
            self.hitStateArm = self.hitCountArm
            self.missStateArm = self.missCountArm
            self.hitStateFinger = self.hitCountFinger
            self.missStateFinger = self.missCountFinger
            self.bci2000shell(
                'log Trial ' + str(self.trialCount) +
                ' | arm: ' + str(self.hitCountArm) + ' hits, ' + str(self.missCountArm) + ' misses' +
                ' | finger: ' + str(self.hitCountFinger) + ' hits, ' + str(self.missCountFinger) + ' misses'
            )

            # self.hitCountArm = 0
            # self.missCountArm = 0
            # self.hitCountFinger = 0
            # self.missCountFinger = 0
            #if self.trialCount > int(self.params['TrialsPerBlock']): self.states['Running']=0


        if phase == 'imagine':
            # Specify arm sequence
            # TODO: the following change has been made to the current script: two keys has been added to each side of the keyboard. I would like to make the arm range of motion to be extended as well. i.e. from minArmCenterIndex to minArmCenterIndex. But I want the FingerTargetSeq to be constrained within the center 7 keys. Foe example, when the arm is at the leftmost position, the only possible index of the finger is 2, which corresponding to the key C. Please help me modify ArmStartIdxSeq, ArmTargetSeq, and FingerTargetSeq with the given arm_key_diff_seq
            if int(self.params['PosReset']) and not int(self.params['FreePlaying']):
                if int(self.params['BalancedLabel']):
                    arm_key_diff_seq = [-4, 0, 4] * 9
                else:
                    # arm_key_diff_seq = [-(self.numArmWindows - 1)//2, 0, (self.numArmWindows - 1)//2] * 9
                    arm_key_diff_seq = list(range(-4, 5)) * 3
                arm_key_diff_seq.remove(0)
                random.shuffle(arm_key_diff_seq)
                self.ArmKeyDiffSeq = [0] + arm_key_diff_seq

                center_key_index = self.numKeys // 2
                self.ArmStartIdxSeq = [center_key_index] + [
                    random.randint(
                        max(self.minArmCenterIndex+2, self.minArmCenterIndex+2 - key_diff),
                        min(self.maxArmCenterIndex-2, self.maxArmCenterIndex-2 - key_diff)
                    )
                    for key_diff in arm_key_diff_seq
                ]
                self.ArmTargetSeq = [center_key_index] + [
                    start_index + key_diff
                    for start_index, key_diff in zip(self.ArmStartIdxSeq[1:], arm_key_diff_seq)
                ]

                self.FingerTargetSeq = list(range(3)) * 9
                random.shuffle(self.FingerTargetSeq)
            elif int(self.params['FreePlaying']):
                if int(self.params['SongList']):
                    if not self.availableSongSequences:
                        self.availableSongSequences = self.SongSeqBank[:]
                        # random.shuffle(self.availableSongSequences)
                    self.currentSong = self.availableSongSequences.pop()
                    self.ArmTargetSeq = self.currentSong['sequence'][:]
                    self.FingerTargetSeq = [1]*len(self.ArmTargetSeq)

                else:
                    self.ArmTargetSeq = list(range(2,9)) * 3
                    random.shuffle(self.ArmTargetSeq)
                    self.FingerTargetSeq = [1]*len(self.ArmTargetSeq)
            else:
                self.ArmTargetSeq = list(range(self.minArmCenterIndex+2, self.maxArmCenterIndex-1)) * 3 * 2
                random.shuffle(self.ArmTargetSeq)
                self.FingerTargetSeq = list(range(3)) * (self.numArmWindows-4) * 2
                random.shuffle(self.FingerTargetSeq)

            
            self.innerTrialNum = len(self.ArmTargetSeq)
            #State variables
            self.currentTask = 'Idle' # start with an idle state
            self.states['FingerTask'] = 0
            self.states['ArmTask'] = 0
            self.states['Idle'] = 1

            # self.currentTask = 'Arm' # start with arm decoding
            # self.states['FingerTask'] = 0
            # self.states['ArmTask'] = 1

            self.innerTrialCount = 0
            if int(self.params['FreePlaying']) and int(self.params['SongList']):
                self.initializeCopilotTrial()
            if int(self.params['PosReset']) and self.ArmStartIdxSeq:
                self.setArmStartFromIndex(self.ArmStartIdxSeq[0])
            else:
                self.armStartWindowIndex = self.numKeys // 2
                self.setArmStartFromIndex(self.armStartWindowIndex)
            self.setRoboHandPosition(self.armStartPos)
            self.pickNewTarget()
            self.currentArmWindowIndex = self.armStartWindowIndex

            self.setTargetState('normal')
            
            self.setTargetVisibility(True)

            self.stimuli['robo_hand'].on = True
            self.setFingerTargetVisibility(False)

            self.timer = round(time.time()*1000)

        else:
            self.stimuli['robo_hand'].on = False
            self.setTargetVisibility(False)
            self.setFingerTargetVisibility(False)
            
            for keyIndex in range(self.numKeys):
                self.stimuli['key_base_%d' % keyIndex].on = False
                self.stimuli['key_label_%d' % keyIndex].on = False
                self.stimuli['robo_hand'].on = False
            for blackKeyIndex in getattr(self, 'blackKeyIndices', []):
                self.stimuli['black_key_%d' % blackKeyIndex].on = False

            self.innerTrialCount = 0

    #############################################################

    def Frame(self, phasename):
        
        dt = 1.0/60
    	#Called everytime the screen should be updated
        self.cursorState = self.updateObjectPosition(
            self.cursorState,
            dt)
        self.updateRoboHandPosition()
        if int(self.params['FreePlaying']) and int(self.params['SongList']) and int(self.params['Copilot']):
            self.updateCopilotStatusText()

    def Process(self, sig):

        if self.states['Feedback']:
            # Called every signal block during the imagine phase.
            if self.timer == 0:
                self.timer = round(time.time()*1000)
            self.normSig = copy.deepcopy(sig)
            self.currentArmSignal = float(np.asarray(self.normSig[0]).squeeze())
            # raw = float(np.asarray(self.normSig[0]).squeeze())
            # alpha = 0.2  # lower = smoother, higher = more responsive
            # self.currentArmSignal = (
            #     alpha * raw + (1.0 - alpha) * getattr(self, "smoothedArmSignal", raw)
            # )
            # self.smoothedArmSignal = self.currentArmSignal

            if self.currentTask == 'Idle':
                self.currentArmSignal = 0
                self.setTargetVisibility(True)
                self.setFingerTargetVisibility(False)
                if round(time.time()*1000) - self.timer >= 1000:
                    self.currentTask = 'Arm'
                    self.states['Idle'] = 0
                    self.timer = round(time.time()*1000)

            elif self.currentTask == 'Arm':
                self.setTargetVisibility(True)
                self.setFingerTargetVisibility(False)
                self.setTargetState('normal')
                
                dt = 1.0/40

                if round(time.time()*1000)-self.timer >= int(self.params['ArmWindowLength']):
                    currentRoboIdxFloat = (self.currentRoboX - self.keyPositions[0, 0]) / self.key_step
                    center_space = max((self.maxArmCenterIndex - self.minArmCenterIndex) / 2.0, 1.0)
                    if self.currentArmSignal > 0:
                        arm_signal_scale = (self.maxArmCenterIndex - currentRoboIdxFloat) / center_space
                    elif self.currentArmSignal < 0:
                        arm_signal_scale = (currentRoboIdxFloat - self.minArmCenterIndex) / center_space
                    else:
                        arm_signal_scale = 0.0
                    arm_signal_scale = 1 if arm_signal_scale < 1 else arm_signal_scale**1.5
                    self.currentArmSignal *= arm_signal_scale
                    subject_velocity = self.currentArmSignal * float(self.params['CursorVelocity'])
                    self.lastSubjectArmSignal = float(self.currentArmSignal)
                    self.lastSubjectArmVelocity = float(subject_velocity)
                    copilot_velocity = 0.0
                    if int(self.params['FreePlaying']) and int(self.params['SongList']) and int(self.params['Copilot']):
                        copilot_velocity = self.getCopilotArmVelocity()
                    self.cursorForce = np.array([subject_velocity + copilot_velocity, 0])
                else:
                    self.copilotArmVelocity = 0.0
                    self.lastSubjectArmSignal = 0.0
                    self.lastSubjectArmVelocity = 0.0
                    self.cursorForce = np.array([0, 0])
                self.cursorState = self.updateObjectMovement(
                    self.cursorState,
                    self.cursorForce,
                    self.params['CursorFriction'],
                    self.params['CursorViscosity'],
                    int(self.params['ControlType']),
                    dt,
                )
                
                self.currentArmWindowIndex = self.getClosestArmWindowIndex(self.currentRoboX)
                # if round(time.time()*1000) - self.timer <= 500: # start to move after 500 ms
                #     self.currentArmSignal = 0

                if round(time.time()*1000) - self.timer >= float(self.params['MoveTime']) * 1000:
                    if not int(self.params['FreePlaying']):
                        if self.currentArmWindowIndex == self.activeTargetIndex:
                            self.setTargetState('hit')
                            self.hitCountArm += 1
                        else:
                            self.setTargetState('miss')
                            self.missCountArm += 1
                    else:
                        if np.abs(self.currentArmWindowIndex-self.activeTargetIndex) <= 1:
                            self.hitCountArm += 1
                        else:
                            self.missCountArm += 1
                    self.resultTimer = round(time.time()*1000)
                    self.currentTask = 'ArmHold'


            elif self.currentTask == 'ArmHold':
                self.currentArmSignal = 0
                if int(self.params['FreePlaying']):
                    self.updateNewTarget()
                    self.setTargetState('normal')
                self.setTargetVisibility(True)
                self.setFingerTargetVisibility(False)

                self.cursorForce = np.array([0, 0])
                dt = 1.0/40 #TODO: update
                self.cursorState = self.updateObjectMovement(
                    self.cursorState,
                    self.cursorForce,
                    self.params['CursorFriction'],
                    self.params['CursorViscosity'],
                    int(self.params['ControlType']),
                    dt,
                )

                if round(time.time()*1000) - self.resultTimer >= self.resultHoldTimeMs:
                    self.timer = round(time.time()*1000)
                    self.currentTask = 'Finger'
                    self.fingerDecisionApplied = False
                    self.finger_prob_sum = np.zeros(3, dtype=float)
                    self.finger_prob_count = 0
                    self.setTargetState('normal')
                    self.setFingerTargetState('light')
                    self.setFingerTargetVisibility(True)
                    self.setTargetVisibility(True)

            elif self.currentTask == 'Finger':
                self.currentArmSignal = 0

                self.setTargetVisibility(True)
                self.setFingerTargetVisibility(True)
                # if not int(self.params['FreePlaying']):
                self.setRoboHandPosition(self.getArmKeyPosition(self.activeTargetIndex))

                finger_elapsed = round(time.time()*1000) - self.timer

                if int(self.params["ContinuousFeedback"]) and finger_elapsed >= int(self.params['WindowLength']):

                    finger_prob = np.asarray(self.normSig[-3:], dtype=float).reshape(-1)[:3]
                    self.finger_prob_sum += finger_prob
                    self.finger_prob_count += 1

                    finger_out = int(np.clip(np.rint(float(np.asarray(self.normSig[1]).squeeze())), 0, 2))
                    self.fingerCurrentKeyIndex = self.currentArmWindowIndex + finger_out - 1
                    if finger_out == self.fingerTargetIndex:
                        self.setFingerTargetState('hit')
                    else:
                        self.setFingerTargetState('miss')
                if finger_elapsed >= float(self.params['PressTime']) * 1000:
                    if self.finger_prob_count:
                        finger_prob = self.finger_prob_sum / self.finger_prob_count
                    else:
                        finger_prob = np.asarray(self.normSig[-3:], dtype=float).reshape(-1)[:3]
                    # original_finger_out = int(np.argmax(finger_prob))
                    original_finger_out = int(np.clip(np.rint(float(np.asarray(self.normSig[2]).squeeze())), 0, 2))

                    finger_out = original_finger_out
                    if int(self.params['FreePlaying']) and int(self.params['SongList']) and int(self.params['Copilot']):
                        finger_out = self.getCopilotFingerOut(finger_prob)
                    else:
                        self.copilotOriginalFingerOut = original_finger_out
                        self.copilotFinalFingerOut = finger_out
                    self.fingerCurrentKeyIndex = self.currentArmWindowIndex + finger_out - 1
                    original_pressed_key_index = self.currentArmWindowIndex + original_finger_out - 1
                    top_song_id_before = int(getattr(self, 'copilotTopSongId', -1))
                    top_prob_before = float(getattr(self, 'copilotTopSongProb', 0.0))
                    selected_song_id = int(getattr(self, 'currentSong', {}).get('song_id', -1))
                    selected_song_prob_before = (
                        float(self.copilotPosterior[selected_song_id])
                        if selected_song_id >= 0 and selected_song_id < len(getattr(self, 'copilotPosterior', []))
                        else 0.0
                    )
                    
                    if finger_out == self.fingerTargetIndex:
                        self.setFingerTargetState('hit')
                        self.hitCountFinger += 1
                    else:
                        self.setFingerTargetState('miss')
                        self.missCountFinger += 1
                    if int(self.params['playSound']):
                        self.playFingerFeedbackNote(finger_out)
                    if int(self.params['FreePlaying']) and int(self.params['SongList']):
                        original_finger_correct = int(original_finger_out == self.fingerTargetIndex)
                        final_finger_correct = int(finger_out == self.fingerTargetIndex)
                        original_note_correct = int(original_pressed_key_index == self.fingerTargetKeyIndex)
                        final_note_correct = int(self.fingerCurrentKeyIndex == self.fingerTargetKeyIndex)
                        self.copilotOriginalCorrectCount += original_note_correct
                        self.copilotCorrectedCorrectCount += final_note_correct
                        self.copilotTotalStepCount += 1
                        self.updateCopilotPosterior(self.fingerCurrentKeyIndex)
                        top_song_id_after = int(getattr(self, 'copilotTopSongId', -1))
                        selected_song_prob_after = (
                            float(self.copilotPosterior[selected_song_id])
                            if selected_song_id >= 0 and selected_song_id < len(getattr(self, 'copilotPosterior', []))
                            else 0.0
                        )
                        songs = getattr(self, 'SongSeqBank', [])
                        policy_song_id = int(getattr(self, 'copilotPolicySongId', -1))
                        policy_song = songs[policy_song_id]['title'] if policy_song_id >= 0 and policy_song_id < len(songs) else ''
                        top_song_before = songs[top_song_id_before]['title'] if top_song_id_before >= 0 and top_song_id_before < len(songs) else ''
                        top_song_after = songs[top_song_id_after]['title'] if top_song_id_after >= 0 and top_song_id_after < len(songs) else ''
                        target_label = self.keyLabels[self.fingerTargetKeyIndex] if 0 <= self.fingerTargetKeyIndex < len(self.keyLabels) else ''
                        self.appendCopilotStepLog({
                            'timestamp_ms': round(time.time()*1000),
                            'trial_count': int(self.trialCount),
                            'inner_step': int(self.innerTrialCount + 1),
                            'selected_song_id': selected_song_id,
                            'selected_song': getattr(self, 'currentSong', {}).get('title', ''),
                            'target_key_index': int(self.fingerTargetKeyIndex),
                            'target_key_label': target_label,
                            'arm_start_index': int(self.activeArmStartIdx),
                            'arm_window_index': int(self.currentArmWindowIndex),
                            'arm_position_x': float(self.currentRoboX),
                            'subject_arm_signal': float(getattr(self, 'lastSubjectArmSignal', 0.0)),
                            'subject_arm_velocity': float(getattr(self, 'lastSubjectArmVelocity', 0.0)),
                            'copilot_arm_velocity': float(getattr(self, 'copilotArmVelocity', 0.0)),
                            'finger_target_index': int(self.fingerTargetIndex),
                            'finger_target_key_index': int(self.fingerTargetKeyIndex),
                            'original_finger_out': int(original_finger_out),
                            'final_finger_out': int(finger_out),
                            'pressed_key_index': int(self.fingerCurrentKeyIndex),
                            'original_finger_correct': original_finger_correct,
                            'final_finger_correct': final_finger_correct,
                            'original_note_correct': original_note_correct,
                            'final_note_correct': final_note_correct,
                            'copilot_enabled': int(self.params['Copilot']),
                            'copilot_active': int(getattr(self, 'copilotActive', False)),
                            'assist_strength': float(getattr(self, 'copilotAssistStrength', 0.0)),
                            'policy_song_id': policy_song_id,
                            'policy_song': policy_song,
                            'policy_key_index': '' if getattr(self, 'copilotPolicyKey', None) is None else int(self.copilotPolicyKey),
                            'top_song_id_before': top_song_id_before,
                            'top_song_before': top_song_before,
                            'top_prob_before': top_prob_before,
                            'selected_song_prob_before': selected_song_prob_before,
                            'top_song_id_after': top_song_id_after,
                            'top_song_after': top_song_after,
                            'top_prob_after': float(getattr(self, 'copilotTopSongProb', 0.0)),
                            'selected_song_prob_after': selected_song_prob_after,
                            'posterior': self.summarizeCopilotPosterior(),
                            'original_finger_correct_count': int(self.copilotOriginalCorrectCount),
                            'final_finger_correct_count': int(self.copilotCorrectedCorrectCount),
                            'copilot_step_count': int(self.copilotTotalStepCount),
                        })
                    self.fingerDecisionApplied = True
                    self.resultTimer = round(time.time()*1000)
                    self.currentTask = 'FingerHold'


            else:  # FingerHold
                self.currentArmSignal = 0

                self.setTargetVisibility(True)
                self.setFingerTargetVisibility(True)

                if round(time.time()*1000) - self.resultTimer >= self.resultHoldTimeMs:
                    self.setFingerTargetVisibility(False)
                    self.innerTrialCount += 1
                    if self.innerTrialCount >= self.innerTrialNum:
                        stopcue = self._block_structure.get('stopcue')
                        self.change_phase(stopcue)
                        self.timer = 0
                        return

                    self.setNextArmStartPosition()
                    self.pickNewTarget()
                    self.currentArmWindowIndex = self.armStartWindowIndex
                    self.setRoboHandPosition(self.armStartPos)
                    # self.setTargetState('normal')
                    # self.setTargetVisibility(True)
                    self.currentTask = 'Arm'
                    self.timer = round(time.time()*1000)
                
            if self.innerTrialCount >= self.innerTrialNum:
                stopcue = self._block_structure.get('stopcue')
                self.change_phase(stopcue)
                self.timer = 0
                return
        
        if self.currentTask == 'Arm':
            self.states['FingerTask'] = 0
            self.states['ArmTask'] = 1
        elif  self.currentTask == 'Finger':
            self.states['FingerTask'] = 1
            self.states['ArmTask'] = 0
        else:
            self.states['FingerTask'] = 0
            self.states['ArmTask'] = 0

        if self.currentTask == 'FingerHold':
            self.states['FingerMovePhase'] = 1
        else:
            self.states['FingerMovePhase'] = 0


        self.states['FingerTarget'] = max(self.fingerTargetIndex,0)
        self.states['ArmTarget'] = max(self.activeTargetIndex,0)
        self.states['ArmStart'] = max(self.activeArmStartIdx,0)
        self.states['ArmDiff'] = abs(int(self.activeArmKeyDiff))

        self.states['targetKeyIndex'] = int(self.fingerTargetKeyIndex)
        self.states['pressedKeyIndex'] = int(self.fingerCurrentKeyIndex)
        self.states['ArmCurrentIndex'] = int(self.currentArmWindowIndex)

        self.states['FingerPred'] = max(sig[1],0)
        self.states['AccumFingerPred'] = max(sig[2],0)
        self.states['CopilotFingerPred'] = getattr(self, 'copilotFinalFingerOut', max(sig[2],0))

        self.states['ArmPred_X'] = self.currentRoboX + self.states['SignedOffset']
        self.states['Raw_ArmPred_X'] =int(sig[0]*100 + self.states['SignedOffset']) #real-time vel
        self.states["InnerTrialCount"] = self.innerTrialCount
        
        self.states['FingerHitCount'] = int(self.hitCountFinger)
        self.states['FingerMissCount'] = int(self.missCountFinger)
        self.states['ArmHitCount'] = int(self.hitCountArm)
        self.states['ArmMissCount'] = int(self.missCountArm)



                


    #############################################################


    def StopRun(self):
    	#Called at the end of every run, use to wrap up the experiment
        self.states['Feedback'] = 0
        self.stimuli['cue'].on = True
        self.stimuli['cue'].AddDispatch(lambda: self.stimuli['cue'].setText('Stop'))
        self.setTargetVisibility(False)
        self.setFingerTargetVisibility(False)


#################################################################
#################################################################


