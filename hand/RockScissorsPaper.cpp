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
// current commanded pose of the hand, updated by PressFinger()/MotionReset().
static double position[] = {
	0.0000, 0.0000, 0.9000, 0.2134,
	0.0000, 0.0000, 0.9000, 0.2134,
	0.0000, 0.0000, 0.9000, 0.2134,
	0.8510, 0.4430, 0.1285, 0.7840
};

// resting pose: fingers hovering over the keys. MotionReset() returns here, and
// PressFinger() presses relative to it. Recalibrate per the setup guide if the
// hand's mounting changes.
static double initpos[] = {
	0.0000, 0.0000, 0.9000, 0.2134,
	0.0000, 0.0000, 0.9000, 0.2134,
	0.0000, 0.0000, 0.9000, 0.2134,
	0.8510, 0.4430, 0.1285, 0.7840
};

// -----------------------------------------------------------------------
// Piano finger mapping
// -----------------------------------------------------------------------
// CopilotFingerPred (0/1/2 = left/center/right key) selects which of the three
// adjacent piano-playing fingers presses. Each entry is the {firstJoint, lastJoint}
// range (inclusive) of the Allegro finger that flexes to press.
//
// Allegro joint blocks:  index=0..3, middle=4..7, ring/pinky=8..11, thumb=12..15.
// The middle finger sits over the arm's current key, so:
//   0 (left)  -> index finger   (joints 1..3)
//   1 (center)-> middle finger  (joints 5..7)
//   2 (right) -> ring/pinky     (joints 9..11)
// >>> CONFIRM this matches how the hand is physically mounted over the keys. <<<
static const int fingerJoints[3][2] = {
	{ 1, 3 },   // 0 = left   -> index
	{ 5, 7 },   // 1 = center -> middle
	{ 9, 11 },  // 2 = right  -> ring/pinky
};

// Radians the proximal (MCP) knuckle joint rotates to press a key. Every other
// finger joint is held at its resting posture (initpos), which is set so the
// fingertips already point straight down at the keys; the press is therefore a
// pure proximal-joint rotation that drives the rigid fingertip down. Tune on the
// physical rig so the fingertip depresses the key without jamming.
static double press_flexion = 0.80;
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

// Press one piano key with the selected finger. fingerSel is CopilotFingerPred
// (0=left, 1=center, 2=right). Sets an absolute pressed pose: the resting pose
// with the chosen finger's flexion joints bent down by press_flexion. Call
// MotionReset() afterwards to lift the finger back to rest.
void PressFinger(int fingerSel)
{
	if (fingerSel < 0 || fingerSel > 2) return;

	int j0 = fingerJoints[fingerSel][0];   // proximal (MCP) knuckle joint

	// Hold every joint at the resting posture (fingertips pointing straight
	// down, set in initpos) and press by rotating ONLY the proximal knuckle
	// joint, so the rigid down-pointing fingertip drives straight into the key.
	for (int i = 0; i < 16; i++)
		q_des[i] = initpos[i];
	q_des[j0] = initpos[j0] + press_flexion;
	q_des[j0+1] = initpos[j0+1] - press_flexion;

	for (int i = 0; i < 16; i++)
		position[i] = q_des[i];

	if (pBHand) pBHand->SetMotionType(eMotionType_JOINT_PD);
	SetGainsRSP();
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