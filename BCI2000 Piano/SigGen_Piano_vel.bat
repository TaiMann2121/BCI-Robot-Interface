#! ../prog/BCI2000Shell
@cls & ..\prog\BCI2000Shell %0 %* #! && exit /b 0 || exit /b 1\n


execute script FindPortablePython.bat  # this is necessary so that BCI2000 can find Python


change directory $BCI2000LAUNCHDIR
show window; set title ${Extract file base $0}
reset system
startup system localhost

start executable SignalGenerator
start executable PythonSignalProcessing --local --PythonSigClassFile=Piano_Processing.py --PythonSigShell=0 --PythonSigLog=Siglogger.txt --PythonSigWD=D:/ArmFIngerRoboConnection/BCI_DL/BCI2000/python/ArmFingerRobo

start executable PythonApplication      --local --PythonAppClassFile=Piano_Application_vel.py --PythonAppShell=0 --PythonAppLog=Applogger.txt --PythonAppWD=D:/ArmFIngerRoboConnection/BCI_DL/BCI2000/python/ArmFingerRobo


wait for connected 600
load parameterfile "../parms/BioSemi_Piano.prm"
ADD WATCH CurrentTrial InnerTrialCount ArmPred_X FingerMovePhase CopilotFingerPred targetKeyIndex pressedKeyIndex ArmCurrentIndex AT 127.0.0.1:5005
