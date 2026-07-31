// myAllegroHand.cpp : Defines the entry point for the console application.
//

#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#include "stdafx.h"
#include "windows.h"
#include <conio.h>
#include <process.h>
#include <tchar.h>
#include "canAPI.h"
#include "rDeviceAllegroHandCANDef.h"
#include "rPanelManipulatorCmdUtil.h"
#include "BHand/BHand.h"

/////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////
// IMPORTANT !!
// SET CORRECT HAND PARAMETER HERE BEFORE RUNNING THIS PROGRAM.
const bool	RIGHT_HAND = true;
const int	HAND_VERSION = 4;
/////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////////////////////////////////////
// for CAN communication
const double delT = 0.003;
int CAN_Ch = 0;
bool ioThreadRun = false;
uintptr_t ioThread = 0;
int recvNum = 0;
int sendNum = 0;
double statTime = -1.0;
AllegroHand_DeviceMemory_t vars;

/////////////////////////////////////////////////////////////////////////////////////////
// for rPanelManipulator
rPanelManipulatorData_t* pSHM = NULL;
double curTime = 0.0;

/////////////////////////////////////////////////////////////////////////////////////////
// for BHand library
BHand* pBHand = NULL;
double q[MAX_DOF];
double q_des[MAX_DOF];
double tau_des[MAX_DOF];
double cur_des[MAX_DOF];

/////////////////////////////////////////////////////////////////////////////////////////
// Hand parameters
const double tau_cov_const_v4 = 1200.0; // 1200.0 for SAH040xxxxx
const short pwm_max_DC8V = 800; // 1200 is max
const short pwm_max_DC24V = 500;

/////////////////////////////////////////////////////////////////////////////////////////
// sample motions
#include "RockScissorsPaper.h"

/////////////////////////////////////////////////////////////////////////////////////////
// functions declarations
void PrintInstruction();
void MainLoop();
bool OpenCAN();
void CloseCAN();
int GetCANChannelIndex(const TCHAR* cname);
bool CreateBHandAlgorithm();
void DestroyBHandAlgorithm();
void ComputeTorque();

/////////////////////////////////////////////////////////////////////////////////////////
// CAN communication thread
static unsigned int __stdcall ioThreadProc(void* inst)
{
	int id;
	int len;
	unsigned char data[8];
	unsigned char data_return = 0;
	int i;

	while (ioThreadRun)
	{
		/* wait for the event */
		while (0 == get_message(CAN_Ch, &id, &len, data, FALSE))
		{
			//            printf(">CAN(%d): ", CAN_Ch);
			//            for(int nd=0; nd<len; nd++)
			//                printf("%02x ", data[nd]);
			//            printf("\n");

			switch (id)
			{
			case ID_RTR_HAND_INFO:
			{
				printf(">CAN(%d): AllegroHand hardware version: 0x%02x%02x\n", CAN_Ch, data[1], data[0]);
				printf("                      firmware version: 0x%02x%02x\n", data[3], data[2]);
				printf("                      hardware type: %d(%s)\n", data[4], (data[4] == 0 ? "right" : "left"));
				printf("                      temperature: %d (celsius)\n", data[5]);
				printf("                      status: 0x%02x\n", data[6]);
				printf("                      servo status: %s\n", (data[6] & 0x01 ? "ON" : "OFF"));
				printf("                      high temperature fault: %s\n", (data[6] & 0x02 ? "ON" : "OFF"));
				printf("                      internal communication fault: %s\n", (data[6] & 0x04 ? "ON" : "OFF"));
			}
			break;
			case ID_RTR_SERIAL:
			{
				printf(">CAN(%d): AllegroHand serial number: SAH0%d0 %c%c%c%c%c%c%c%c\n", CAN_Ch, HAND_VERSION
					, data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7]);
			}
			break;
			case ID_RTR_FINGER_POSE_1:
			case ID_RTR_FINGER_POSE_2:
			case ID_RTR_FINGER_POSE_3:
			case ID_RTR_FINGER_POSE_4:
			{
				int findex = (id & 0x00000007);

				vars.enc_actual[findex * 4 + 0] = (short)(data[0] | (data[1] << 8));
				vars.enc_actual[findex * 4 + 1] = (short)(data[2] | (data[3] << 8));
				vars.enc_actual[findex * 4 + 2] = (short)(data[4] | (data[5] << 8));
				vars.enc_actual[findex * 4 + 3] = (short)(data[6] | (data[7] << 8));
				data_return |= (0x01 << (findex));
				recvNum++;

				//                printf(">CAN(%d): Encoder[%d] Count : %6d %6d %6d %6d\n"
				//                    , CAN_Ch, findex
				//                    , vars.enc_actual[findex*4 + 0], vars.enc_actual[findex*4 + 1]
				//                    , vars.enc_actual[findex*4 + 2], vars.enc_actual[findex*4 + 3]);

				if (data_return == (0x01 | 0x02 | 0x04 | 0x08))
				{
					// convert encoder count to joint angle
					for (i = 0; i<MAX_DOF; i++)
					{
						q[i] = (double)(vars.enc_actual[i])*(333.3 / 65536.0)*(3.141592 / 180.0);
					}

					// print joint angles
					//                    for (int i=0; i<4; i++)
					//                    {
					//                        printf(">CAN(%d): Joint[%d] Pos : %5.1f %5.1f %5.1f %5.1f\n"
					//                            , CAN_Ch, i, q[i*4+0]*RAD2DEG, q[i*4+1]*RAD2DEG, q[i*4+2]*RAD2DEG, q[i*4+3]*RAD2DEG);
					//                    }

					// compute joint torque
					ComputeTorque();

					// convert desired torque to desired current and PWM count
					for (int i = 0; i<MAX_DOF; i++)
					{
						cur_des[i] = tau_des[i];
						if (cur_des[i] > 1.0) cur_des[i] = 1.0;
						else if (cur_des[i] < -1.0) cur_des[i] = -1.0;
					}

					// send torques
					for (int i = 0; i<4; i++)
					{
						vars.pwm_demand[i * 4 + 0] = (short)(cur_des[i * 4 + 0] * tau_cov_const_v4);
						vars.pwm_demand[i * 4 + 1] = (short)(cur_des[i * 4 + 1] * tau_cov_const_v4);
						vars.pwm_demand[i * 4 + 2] = (short)(cur_des[i * 4 + 2] * tau_cov_const_v4);
						vars.pwm_demand[i * 4 + 3] = (short)(cur_des[i * 4 + 3] * tau_cov_const_v4);

						command_set_torque(CAN_Ch, i, &vars.pwm_demand[4 * i]);
						//for (int k = 0; k<100000; k++);
						//usleep(5);
					}
					sendNum++;
					curTime += delT;
					data_return = 0;
				}
			}
			break;
			case ID_RTR_IMU_DATA:
			{
				printf(">CAN(%d): AHRS Roll : 0x%02x%02x\n", CAN_Ch, data[0], data[1]);
				printf("               Pitch: 0x%02x%02x\n", data[2], data[3]);
				printf("               Yaw  : 0x%02x%02x\n", data[4], data[5]);
			}
			break;
			case ID_RTR_TEMPERATURE_1:
			case ID_RTR_TEMPERATURE_2:
			case ID_RTR_TEMPERATURE_3:
			case ID_RTR_TEMPERATURE_4:
			{
				int sindex = (id & 0x00000007);
				int celsius = (int)(data[0]) |
					(int)(data[1] << 8) |
					(int)(data[2] << 16) |
					(int)(data[3] << 24);
				printf(">CAN(%d): Temperature[%d]: %d (celsius)\n", CAN_Ch, sindex, celsius);
			}
			break;
			default:
				printf(">CAN(%d): unknown command %d, len %d\n", CAN_Ch, id, len);
				/*for(int nd=0; nd<len; nd++)
				printf("%d \n ", data[nd]);*/
				//return;
			}
		}
	}
	return NULL;
}

// -----------------------------------------------------------------------
// MainLoop — piano task (single combined BCI2000 stream via the dispatcher)
// -----------------------------------------------------------------------
// The piano task streams everything on one BCI2000 port (5005). The Python
// dispatcher (dispatcher/bci2000_dispatcher.py) owns 5005 and forwards the
// cleaned 8-field record to this controller on port 5007:
//
//   CurrentTrial  InnerTrialCount  ArmPred_X  FingerMovePhase
//   CopilotFingerPred  targetKeyIndex  pressedKeyIndex  ArmCurrentIndex
//
// This controller only uses two fields:
//   FingerMovePhase   : 1 during the brief FingerHold phase, else 0. It is an
//                       EDGE-TRIGGERED pulse — press on the 0 -> 1 transition,
//                       NOT while it is held (it is only true for ~100 ms).
//   CopilotFingerPred : 0/1/2 = left/center/right finger to press.
//
// Arm positioning is handled by arm_controller.py, so the pressed key is
// implied by where the arm is; this controller just taps the selected finger.
// -----------------------------------------------------------------------

// Constants — adjust these as needed
#define UDP_PORT        5007     // forwarded from the dispatcher (BCI2000 -> 5005 -> here)
#define BUFFER_SIZE     512
#define PRESS_HOLD_MS   400      // how long to hold a key press before lifting

void MainLoop()
{
	// ---- Socket setup ----
	WSADATA wsaData;
	WSAStartup(MAKEWORD(2, 2), &wsaData);

	SOCKET sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

	// Set socket to non-blocking so we don't freeze waiting for packets
	u_long mode = 1;
	ioctlsocket(sock, FIONBIO, &mode);

	sockaddr_in addr;
	addr.sin_family = AF_INET;
	addr.sin_port = htons(UDP_PORT);
	addr.sin_addr.s_addr = inet_addr("127.0.0.1");
	bind(sock, (sockaddr*)&addr, sizeof(addr));

	printf("Listening for piano finger data on UDP port %d (via dispatcher)...\n", UDP_PORT);
	printf("Press Q to quit.\n\n");

	// Move hand to its resting pose (fingers hovering over the keys)
	MotionReset();

	char buf[BUFFER_SIZE];
	char latestBuf[BUFFER_SIZE] = { 0 };
	bool hasPacket = false;
	bool bRun = true;
	int prevFingerMovePhase = 0;   // for rising-edge detection

	while (bRun)
	{
		// ---- Check for quit key ----
		if (_kbhit())
		{
			int c = _getch();
			if (c == 'q' || c == 'Q')
			{
				if (pBHand) pBHand->SetMotionType(eMotionType_NONE);
				bRun = false;
				break;
			}
			// ---- Bench force-measurement helpers ----
			// Press a finger and HOLD it down (no auto-lift) so a scale can
			// settle. 1/2/3 = left/center/right finger; L or H lifts to rest.
			// The io thread keeps applying q_des, so the press holds until you
			// lift. WARNING: don't leave a finger stalled against a hard surface
			// for more than a few seconds at a time — lift ('L') between reads.
			else if (c == '1') { printf("HOLD press: finger 0 (left)\n");   PressFinger(0); }
			else if (c == '2') { printf("HOLD press: finger 1 (center)\n"); PressFinger(1); }
			else if (c == '3') { printf("HOLD press: finger 2 (right)\n");  PressFinger(2); }
			else if (c == 'l' || c == 'L' || c == 'h' || c == 'H')
			{
				printf("Lift to resting pose\n");
				MotionReset();
			}
		}

		// ---- Drain UDP buffer, keep only the most recent packet ----
		hasPacket = false;
		while (true)
		{
			int bytes = recv(sock, buf, BUFFER_SIZE - 1, 0);
			if (bytes == SOCKET_ERROR)
				break;   // buffer empty — stop draining
			buf[bytes] = '\0';
			memcpy(latestBuf, buf, bytes + 1);
			hasPacket = true;
		}

		if (!hasPacket)
		{
			Sleep(5);   // no data yet, wait a bit
			continue;
		}

		// ---- Parse the packet (8 tab-separated integers) ----
		int currentTrial, innerTrialCount, armPredX, fingerMovePhase;
		int copilotFingerPred, targetKeyIndex, pressedKeyIndex, armCurrentIndex;

		int parsed = sscanf_s(latestBuf, "%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d",
			&currentTrial, &innerTrialCount, &armPredX, &fingerMovePhase,
			&copilotFingerPred, &targetKeyIndex, &pressedKeyIndex, &armCurrentIndex);

		if (parsed != 8)
		{
			printf("Bad packet, skipping: %s\n", latestBuf);
			continue;
		}

		// ---- Edge-triggered press: fire on FingerMovePhase 0 -> 1 ----
		if (fingerMovePhase && !prevFingerMovePhase)
		{
			printf("Press: finger %d (arm key %d, target %d)\n",
				copilotFingerPred, armCurrentIndex, targetKeyIndex);
			PressFinger(copilotFingerPred);   // flex the selected finger down
			Sleep(PRESS_HOLD_MS);             // hold the press briefly
			MotionReset();                    // lift back to the resting pose
		}
		prevFingerMovePhase = fingerMovePhase;
	}

	// ---- Cleanup ----
	closesocket(sock);
	WSACleanup();
}

/////////////////////////////////////////////////////////////////////////////////////////
// Compute control torque for each joint using BHand library
void ComputeTorque()
{
	if (!pBHand) return;
	pBHand->SetJointPosition(q); // tell BHand library the current joint positions
	pBHand->SetJointDesiredPosition(q_des);
	pBHand->UpdateControl(0);
	pBHand->GetJointTorque(tau_des);

	//    static int j_active[] = {
	//        0, 0, 0, 0,
	//        0, 0, 0, 0,
	//        0, 0, 0, 0,
	//        1, 1, 1, 1
	//    };
	//    for (int i=0; i<MAX_DOF; i++) {
	//        if (j_active[i] == 0) {
	//            tau_des[i] = 0;
	//        }
	//    }
}

/////////////////////////////////////////////////////////////////////////////////////////
// Open a CAN data channel
bool OpenCAN()
{
	int ret;
	
#if defined(PEAKCAN)
	CAN_Ch = GetCANChannelIndex(_T("USBBUS1"));
#elif defined(IXXATCAN)
	CAN_Ch = 1;
#elif defined(SOFTINGCAN)
	CAN_Ch = 1;
#elif defined(NICAN)
	CAN_Ch = 0;
#else
	CAN_Ch = 1;
#endif

	printf(">CAN(%d): open\n", CAN_Ch);
	ret = command_can_open(CAN_Ch);
	if(ret < 0)
	{
		printf("ERROR command_canopen !!! \n");
		return false;
	}

	recvNum = 0;
	sendNum = 0;
	statTime = 0.0;

	ioThreadRun = true;
	ioThread = _beginthreadex(NULL, 0, ioThreadProc, NULL, 0, NULL);
	printf(">CAN: starts listening CAN frames\n");
	
	// query h/w information
	printf(">CAN: query system information\n");
	ret = request_hand_information(CAN_Ch);
	if (ret < 0)
	{
		printf("ERROR request_hand_information !!! \n");
		command_can_close(CAN_Ch);
		return false;
	}
	ret = request_hand_serial(CAN_Ch);
	if (ret < 0)
	{
		printf("ERROR request_hand_serial !!! \n");
		command_can_close(CAN_Ch);
		return false;
	}

	// set periodic communication parameters(period)
	printf(">CAN: Comm period set\n");
	short comm_period[3] = { 3, 0, 0 }; // millisecond {position, imu, temperature}
	ret = command_set_period(CAN_Ch, comm_period);
	if (ret < 0)
	{
		printf("ERROR command_set_period !!! \n");
		command_can_close(CAN_Ch);
		return false;
	}

	// servo on
	printf(">CAN: servo on\n");
	ret = command_servo_on(CAN_Ch);
	if (ret < 0)
	{
		printf("ERROR command_servo_on !!! \n");
		command_set_period(CAN_Ch, 0);
		command_can_close(CAN_Ch);
		return false;
	}

	return true;
}

/////////////////////////////////////////////////////////////////////////////////////////
// Close CAN data channel
void CloseCAN()
{
	int ret;

	printf(">CAN: stop periodic communication\n");
	ret = command_set_period(CAN_Ch, 0);
	if(ret < 0)
	{
		printf("ERROR command_can_stop !!! \n");
	}

	if (ioThreadRun)
	{
		printf(">CAN: stoped listening CAN frames\n");
		ioThreadRun = false;
		WaitForSingleObject((HANDLE)ioThread, INFINITE);
		CloseHandle((HANDLE)ioThread);
		ioThread = 0;
	}

	printf(">CAN(%d): close\n", CAN_Ch);
	ret = command_can_close(CAN_Ch);
	if(ret < 0) printf("ERROR command_can_close !!! \n");
}

/////////////////////////////////////////////////////////////////////////////////////////
// Load and create grasping algorithm
bool CreateBHandAlgorithm()
{
	if (RIGHT_HAND)
		pBHand = bhCreateRightHand();
	else
		pBHand = bhCreateLeftHand();

	if (!pBHand) return false;
	pBHand->SetMotionType(eMotionType_NONE);
	pBHand->SetTimeInterval(delT);
	return true;
}

/////////////////////////////////////////////////////////////////////////////////////////
// Destroy grasping algorithm
void DestroyBHandAlgorithm()
{
	if (pBHand)
	{
#ifndef _DEBUG
		delete pBHand;
#endif
		pBHand = NULL;
	}
}

/////////////////////////////////////////////////////////////////////////////////////////
// Print program information and keyboard instructions
void PrintInstruction()
{
	printf("--------------------------------------------------\n");
	printf("myAllegroHand: ");
	if (RIGHT_HAND) printf("Right Hand, v%i.x\n\n", HAND_VERSION); else printf("Left Hand, v%i.x\n\n", HAND_VERSION);

	printf("Keyboard Commands:\n");
	printf("H: Home Position (PD control)\n");
	printf("R: Ready Position (used before grasping)\n");
	printf("G: Three-Finger Grasp\n");
	printf("K: Four-Finger Grasp\n");
	printf("P: Two-finger pinch (index-thumb)\n");
	printf("M: Two-finger pinch (middle-thumb)\n");
	printf("E: Envelop Grasp (all fingers)\n");
	printf("A: Gravity Compensation\n\n");
	printf("F: Servos OFF (any grasp cmd turns them back on)\n");
	printf("Q: Quit this program\n");

	printf("--------------------------------------------------\n\n");
}

/////////////////////////////////////////////////////////////////////////////////////////
// Get channel index for Peak CAN interface
int GetCANChannelIndex(const TCHAR* cname)
{
	if (!cname) return 0;

	if (!_tcsicmp(cname, _T("0")) || !_tcsicmp(cname, _T("PCAN_NONEBUS")) || !_tcsicmp(cname, _T("NONEBUS")))
		return 0;
	else if (!_tcsicmp(cname, _T("1")) || !_tcsicmp(cname, _T("PCAN_ISABUS1")) || !_tcsicmp(cname, _T("ISABUS1")))
		return 1;
	else if (!_tcsicmp(cname, _T("2")) || !_tcsicmp(cname, _T("PCAN_ISABUS2")) || !_tcsicmp(cname, _T("ISABUS2")))
		return 2;
	else if (!_tcsicmp(cname, _T("3")) || !_tcsicmp(cname, _T("PCAN_ISABUS3")) || !_tcsicmp(cname, _T("ISABUS3")))
		return 3;
	else if (!_tcsicmp(cname, _T("4")) || !_tcsicmp(cname, _T("PCAN_ISABUS4")) || !_tcsicmp(cname, _T("ISABUS4")))
		return 4;
	else if (!_tcsicmp(cname, _T("5")) || !_tcsicmp(cname, _T("PCAN_ISABUS5")) || !_tcsicmp(cname, _T("ISABUS5")))
		return 5;
	else if (!_tcsicmp(cname, _T("7")) || !_tcsicmp(cname, _T("PCAN_ISABUS6")) || !_tcsicmp(cname, _T("ISABUS6")))
		return 6;
	else if (!_tcsicmp(cname, _T("8")) || !_tcsicmp(cname, _T("PCAN_ISABUS7")) || !_tcsicmp(cname, _T("ISABUS7")))
		return 7;
	else if (!_tcsicmp(cname, _T("8")) || !_tcsicmp(cname, _T("PCAN_ISABUS8")) || !_tcsicmp(cname, _T("ISABUS8")))
		return 8;
	else if (!_tcsicmp(cname, _T("9")) || !_tcsicmp(cname, _T("PCAN_DNGBUS1")) || !_tcsicmp(cname, _T("DNGBUS1")))
		return 9;
	else if (!_tcsicmp(cname, _T("10")) || !_tcsicmp(cname, _T("PCAN_PCIBUS1")) || !_tcsicmp(cname, _T("PCIBUS1")))
		return 10;
	else if (!_tcsicmp(cname, _T("11")) || !_tcsicmp(cname, _T("PCAN_PCIBUS2")) || !_tcsicmp(cname, _T("PCIBUS2")))
		return 11;
	else if (!_tcsicmp(cname, _T("12")) || !_tcsicmp(cname, _T("PCAN_PCIBUS3")) || !_tcsicmp(cname, _T("PCIBUS3")))
		return 12;
	else if (!_tcsicmp(cname, _T("13")) || !_tcsicmp(cname, _T("PCAN_PCIBUS4")) || !_tcsicmp(cname, _T("PCIBUS4")))
		return 13;
	else if (!_tcsicmp(cname, _T("14")) || !_tcsicmp(cname, _T("PCAN_PCIBUS5")) || !_tcsicmp(cname, _T("PCIBUS5")))
		return 14;
	else if (!_tcsicmp(cname, _T("15")) || !_tcsicmp(cname, _T("PCAN_PCIBUS6")) || !_tcsicmp(cname, _T("PCIBUS6")))
		return 15;
	else if (!_tcsicmp(cname, _T("16")) || !_tcsicmp(cname, _T("PCAN_PCIBUS7")) || !_tcsicmp(cname, _T("PCIBUS7")))
		return 16;
	else if (!_tcsicmp(cname, _T("17")) || !_tcsicmp(cname, _T("PCAN_PCIBUS8")) || !_tcsicmp(cname, _T("PCIBUS8")))
		return 17;
	else if (!_tcsicmp(cname, _T("18")) || !_tcsicmp(cname, _T("PCAN_USBBUS1")) || !_tcsicmp(cname, _T("USBBUS1")))
		return 18;
	else if (!_tcsicmp(cname, _T("19")) || !_tcsicmp(cname, _T("PCAN_USBBUS2")) || !_tcsicmp(cname, _T("USBBUS2")))
		return 19;
	else if (!_tcsicmp(cname, _T("20")) || !_tcsicmp(cname, _T("PCAN_USBBUS3")) || !_tcsicmp(cname, _T("USBBUS3")))
		return 20;
	else if (!_tcsicmp(cname, _T("21")) || !_tcsicmp(cname, _T("PCAN_USBBUS4")) || !_tcsicmp(cname, _T("USBBUS4")))
		return 21;
	else if (!_tcsicmp(cname, _T("22")) || !_tcsicmp(cname, _T("PCAN_USBBUS5")) || !_tcsicmp(cname, _T("USBBUS5")))
		return 22;
	else if (!_tcsicmp(cname, _T("23")) || !_tcsicmp(cname, _T("PCAN_USBBUS6")) || !_tcsicmp(cname, _T("USBBUS6")))
		return 23;
	else if (!_tcsicmp(cname, _T("24")) || !_tcsicmp(cname, _T("PCAN_USBBUS7")) || !_tcsicmp(cname, _T("USBBUS7")))
		return 24;
	else if (!_tcsicmp(cname, _T("25")) || !_tcsicmp(cname, _T("PCAN_USBBUS8")) || !_tcsicmp(cname, _T("USBBUS8")))
		return 25;
	else if (!_tcsicmp(cname, _T("26")) || !_tcsicmp(cname, _T("PCAN_PCCBUS1")) || !_tcsicmp(cname, _T("PCCBUS1")))
		return 26;
	else if (!_tcsicmp(cname, _T("27")) || !_tcsicmp(cname, _T("PCAN_PCCBUS2")) || !_tcsicmp(cname, _T("PCCBUS2")))
		return 271;
	else
		return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////
// Program main
int _tmain(int argc, _TCHAR* argv[])
{
	PrintInstruction();

	memset(&vars, 0, sizeof(vars));
	memset(q, 0, sizeof(q));
	memset(q_des, 0, sizeof(q_des));
	memset(tau_des, 0, sizeof(tau_des));
	memset(cur_des, 0, sizeof(cur_des));
	curTime = 0.0;

	pSHM = getrPanelManipulatorCmdMemory();
	
	if (CreateBHandAlgorithm() && OpenCAN())
		MainLoop();

	CloseCAN();
	DestroyBHandAlgorithm();
	closerPanelManipulatorCmdMemory();

	return 0;
}
