#include "rDeviceAllegroHandCANDef.h"
#include "BHand/BHand.h"

// ROCK-SCISSORS-PAPER(RIGHT HAND)
static double rock[] = {
	-0.1194, 1.2068, 1.0, 1.4042, 
	-0.0093, 1.2481, 1.4073, 0.8163, 
	0.1116, 1.2712, 1.3881, 1.0122, 
	0.6017, 0.2976, 0.9034, 0.7929};
static double paper[] = {
	-0.1220, 0.4, 0.6, -0.0769, 
	0.0312, 0.4, 0.6, -0.0, 
	0.1767, 0.4, 0.6, -0.0528, 
	0.5284, 0.3693, 0.8977, 0.4863};
static double scissors[] = {
	0.0885, 0.4, 0.6, -0.0704, 
	0.0312, 0.4, 0.6, -0.0, 
	0.1019, 1.2375, 1.1346, 
	1.0244, 1.0, 0.6331, 1.3509, 1.0};

//// current position of the hand, which is updated in MoveFinger() function. This is used to move fingers incrementally.
//static double position[] = {
//		0, 0, 0, 0,
//		0, 0, 0, 0,
//	0, 0, 0, 0,
//	0.40, 1.25, -0.27, -0.24 };
//// initial position of the hand, which is used in MotionReset() function to reset the hand to the initial position.
//static double initpos[] = {
//		0, 0, 0, 0,
//		0, 0, 0, 0,
//	0, 0, 0, 0,
//	0.40, 1.25, -0.27, -0.24 };
// current position of the hand, which is updated in MoveFinger() function. This is used to move fingers incrementally.

static double position[] = {
	0.0169, -0.1330, 0.8200, 0.2134,
	-0.0140, -0.1228, 0.8172, 0.7974,
	0.0414, -0.0535, 0.9128, 0.0000,
	0.8510, 0.4430, 0.1285, 0.7840
};

static double initpos[] = {
	0.0169, -0.1330, 0.8200, 0.2134,
	-0.0140, -0.1228, 0.8172, 0.7974,
	0.0414, -0.0535, 0.9128, 0.0000,
	0.8510, 0.4430, 0.1285, 0.7840
};

// speed of finger movement. This value can be adjusted to make the fingers move faster or slower. The value is added to the current position of the finger in MoveFinger() function.
static double speed = 0.1;
// The thumb is moved slower than the other fingers to make the movement more natural. This value can also be adjusted as needed.
static double speed_thumb = 0.12;
// BHand library instance and desired joint positions. These are used in the motion functions to set the desired joint positions and apply the changes using BHand library.
extern BHand* pBHand;
extern double q_des[MAX_DOF];

static void SetGainsRSP()
{
	// This function should be called after the function SetMotionType() is called.
	// Once SetMotionType() function is called, all gains are reset using the default values.
	if (!pBHand) return;
	double kp[] = {
		500, 800, 900, 500,
		500, 800, 900, 500,
		500, 800, 900, 500,
		1000, 700, 600, 600
	};
	double kd[] = {
		25, 50, 55, 40,
		25, 50, 55, 40,
		25, 50, 55, 40,
		50, 50, 50, 40
	};
	pBHand->SetGainsEx(kp, kd);
}
// Rock, Scissors, and Paper motion functions. These functions set the desired joint positions for each motion and then call SetMotionType() and SetGainsRSP() to apply the changes.
void MotionRock()
{
	for (int i=0; i<16; i++)
		q_des[i] = rock[i];
	if (pBHand) pBHand->SetMotionType(eMotionType_JOINT_PD);
	SetGainsRSP();

}
void MotionScissors()
{
	for (int i=0; i<16; i++)
		q_des[i] = scissors[i];
	if (pBHand) pBHand->SetMotionType(eMotionType_JOINT_PD);
	SetGainsRSP();
}
void MotionPaper()
{
	for (int i=0; i<16; i++)
		q_des[i] = paper[i];
	if (pBHand) pBHand->SetMotionType(eMotionType_JOINT_PD);
	SetGainsRSP();
}

void MoveFinger(int max_idx, int max_val)
{
	int joint2Idx;
	int joint4Idx;


	if (max_idx == 0 && max_val > 0) {  // Thumb
		joint2Idx = 14;
		joint4Idx = 15;
		for (int i = 0; i < 16; i++) {
			q_des[i] = position[i];
			if ((i >= joint2Idx) && i <= joint4Idx) {
				position[i] += speed_thumb;
			}
		}
	}
	else if (max_idx == 1 && max_val > 0) {  // Index
		joint2Idx = 1;
		joint4Idx = 3;
		for (int i = 0; i < 16; i++) {
			q_des[i] = position[i];
			if ((i >= joint2Idx) && i <= joint4Idx) {
				position[i] += speed;
			}
		}

	}
	else if (max_idx == 2 && max_val > 0) {   // Middle
		joint2Idx = 5;
		joint4Idx = 7;
		for (int i = 0; i < 16; i++) {
			q_des[i] = position[i];
			if ((i >= joint2Idx) && i <= joint4Idx) {
				position[i] += speed;
			}
		}

	}
	else if (max_idx == 3 && max_val > 0) {    // Pinky
		joint2Idx = 9;
		joint4Idx = 11;
		for (int i = 0; i < 16; i++) {
			q_des[i] = position[i];
			if ((i >= joint2Idx) && i <= joint4Idx) {
				position[i] += speed;
			}
		}

	}
	else return;

	if (pBHand) pBHand->SetMotionType(eMotionType_JOINT_PD);
	SetGainsRSP();
	//usleep(10000);
}

// This function resets the hand to the initial position defined in 'initpos' array. This can be called when the user wants to reset the hand to the initial position.
void MotionReset() {
	for (int i = 0; i < 16; i++)
		position[i] = initpos[i];
	for (int i = 0; i < 16; i++)
		q_des[i] = position[i];
	if (pBHand) pBHand->SetMotionType(eMotionType_JOINT_PD);
	SetGainsRSP();
}