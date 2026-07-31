/*
 * physical_piano_firmware
 * -----------------------
 * Reads 11 momentary key switches on the physical piano and plays one
 * electronic tone per key. Pitches are TUNABLE FROM A COMPUTER over the USB
 * serial link and saved to EEPROM, so they survive power cycles without
 * re-flashing. Mirrors the BCI2000 piano simulator: same 11 keys, same
 * default note frequencies, one note at a time.
 *
 * Board:   Arduino Uno / Nano (any AVR board with tone() + EEPROM works)
 * Sensing: 11 momentary switches, each between its pin and GND.
 *          INPUT_PULLUP is used, so NO external resistors are needed.
 *          A key is "pressed" when its pin reads LOW.
 * Sound:   tone() on SPEAKER_PIN. This is an ELECTRONIC square-wave tone:
 *          you can tune the PITCH (Hz) of each key, but not the timbre.
 *          tone() is MONOPHONIC (one hardware timer) -> one key at a time,
 *          which matches the task (the robot presses one finger per phase).
 *
 * ---- Serial tuning protocol (115200 baud, newline-terminated, case-insensitive) ----
 *   list              print all 11 key frequencies as CSV
 *   set <i> <hz>      set key i (0..10) to <hz> (0 = silent, else 20..8000)
 *   play <i>          audition key i for a moment (no robot needed)
 *   stop              silence any sounding note
 *   save              store the current frequencies to EEPROM
 *   load              reload frequencies from EEPROM (or defaults if empty)
 *   reset             restore built-in default frequencies (not saved until 'save')
 *   help              print this command list
 *
 * Key index 0..10 runs LEFT -> RIGHT and matches the simulator's indices in
 * Piano_Application_vel.py:
 *   labels:  ['', '', 'C', 'D', 'E', 'F', 'G', 'A', 'B', '', '']
 *   (indices 2..8 are the named white keys; 0,1 and 9,10 are padding keys
 *    that still produce a tone, exactly as in the sim.)
 */

#include <EEPROM.h>

const uint8_t NUM_KEYS = 11;

// Built-in default frequencies (Hz), from Piano_Application_vel.py:753.
// Index:   0     1     2(C)  3(D)  4(E)  5(F)  6(G)  7(A)  8(B)  9     10
const unsigned int DEFAULT_FREQ[NUM_KEYS] = {
  233, 247, 262, 294, 330, 349, 392, 440, 494, 523, 554
};

// Live, tunable frequencies (start from defaults; overwritten by EEPROM/serial).
unsigned int freq[NUM_KEYS];

// ---- Pin assignments ----
// 11 switch pins (avoid 0/1 = serial). Left key = KEY_PIN[0].
const uint8_t KEY_PIN[NUM_KEYS] = { 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 };
const uint8_t SPEAKER_PIN = 13;   // piezo / small amp input

// ---- EEPROM layout ----
const int      EE_ADDR  = 0;
const uint16_t EE_MAGIC = 0xB1C2;   // marks a valid saved frequency table

// ---- Debounce / audition ----
const unsigned long DEBOUNCE_MS = 15;
const unsigned long PLAY_MS     = 500;   // how long 'play <i>' auditions a note

bool          keyDown[NUM_KEYS]     = { false };
bool          lastReading[NUM_KEYS] = { false };
unsigned long lastChange[NUM_KEYS]  = { 0 };

int           activeKey     = -1;   // physically held key that is sounding (-1 = none)
unsigned long auditionUntil = 0;    // 0 = not auditioning

// ---- Serial input buffer ----
char    cmdBuf[48];
uint8_t cmdLen = 0;

// -------------------------------------------------------------------------

void startNote(unsigned int hz) {
  if (hz == 0) { noTone(SPEAKER_PIN); }
  else         { tone(SPEAKER_PIN, hz); }
}
void stopNote() { noTone(SPEAKER_PIN); }

void loadDefaults() {
  for (uint8_t i = 0; i < NUM_KEYS; i++) freq[i] = DEFAULT_FREQ[i];
}

void saveToEeprom() {
  EEPROM.put(EE_ADDR, EE_MAGIC);
  for (uint8_t i = 0; i < NUM_KEYS; i++)
    EEPROM.put(EE_ADDR + 2 + i * 2, freq[i]);
  Serial.println(F("saved"));
}

void loadFromEeprom() {
  uint16_t magic = 0;
  EEPROM.get(EE_ADDR, magic);
  if (magic == EE_MAGIC) {
    for (uint8_t i = 0; i < NUM_KEYS; i++)
      EEPROM.get(EE_ADDR + 2 + i * 2, freq[i]);
    Serial.println(F("loaded from EEPROM"));
  } else {
    loadDefaults();
    Serial.println(F("no saved data - using defaults"));
  }
}

void printList() {
  Serial.print(F("freq: "));
  for (uint8_t i = 0; i < NUM_KEYS; i++) {
    Serial.print(freq[i]);
    if (i < NUM_KEYS - 1) Serial.print(',');
  }
  Serial.println();
}

void printHelp() {
  Serial.println(F("commands: list | set <i> <hz> | play <i> | stop | save | load | reset | help"));
}

void handleCommand(char *line) {
  // Tokenize on spaces.
  char *cmd = strtok(line, " ");
  if (!cmd) return;

  if (!strcasecmp(cmd, "list")) {
    printList();
  } else if (!strcasecmp(cmd, "help")) {
    printHelp();
  } else if (!strcasecmp(cmd, "stop")) {
    stopNote(); activeKey = -1; auditionUntil = 0;
    Serial.println(F("stopped"));
  } else if (!strcasecmp(cmd, "save")) {
    saveToEeprom();
  } else if (!strcasecmp(cmd, "load")) {
    loadFromEeprom(); printList();
  } else if (!strcasecmp(cmd, "reset")) {
    loadDefaults(); Serial.println(F("defaults restored (not saved)")); printList();
  } else if (!strcasecmp(cmd, "set")) {
    char *sIdx = strtok(NULL, " ");
    char *sHz  = strtok(NULL, " ");
    if (!sIdx || !sHz) { Serial.println(F("usage: set <i> <hz>")); return; }
    int idx = atoi(sIdx);
    long hz = atol(sHz);
    if (idx < 0 || idx >= NUM_KEYS) { Serial.println(F("err: i must be 0..10")); return; }
    if (hz != 0 && (hz < 20 || hz > 8000)) { Serial.println(F("err: hz must be 0 or 20..8000")); return; }
    freq[idx] = (unsigned int)hz;
    Serial.print(F("key ")); Serial.print(idx);
    Serial.print(F(" = ")); Serial.print(freq[idx]); Serial.println(F(" Hz"));
  } else if (!strcasecmp(cmd, "play")) {
    char *sIdx = strtok(NULL, " ");
    if (!sIdx) { Serial.println(F("usage: play <i>")); return; }
    int idx = atoi(sIdx);
    if (idx < 0 || idx >= NUM_KEYS) { Serial.println(F("err: i must be 0..10")); return; }
    if (activeKey == -1) {              // don't stomp a physically held key
      startNote(freq[idx]);
      auditionUntil = millis() + PLAY_MS;
    }
    Serial.print(F("play ")); Serial.print(idx);
    Serial.print(F(" (")); Serial.print(freq[idx]); Serial.println(F(" Hz)"));
  } else {
    Serial.print(F("unknown cmd: ")); Serial.println(cmd);
    printHelp();
  }
}

void pollSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (cmdLen > 0) { cmdBuf[cmdLen] = '\0'; handleCommand(cmdBuf); cmdLen = 0; }
    } else if (cmdLen < sizeof(cmdBuf) - 1) {
      cmdBuf[cmdLen++] = c;
    }
  }
}

void pollKeys() {
  unsigned long now = millis();
  for (uint8_t i = 0; i < NUM_KEYS; i++) {
    bool reading = (digitalRead(KEY_PIN[i]) == LOW);   // pressed == LOW (pullup)

    if (reading != lastReading[i]) {
      lastReading[i] = reading;
      lastChange[i]  = now;
    }
    if ((now - lastChange[i]) >= DEBOUNCE_MS && reading != keyDown[i]) {
      keyDown[i] = reading;
      if (keyDown[i]) {
        activeKey     = i;
        auditionUntil = 0;
        startNote(freq[i]);
        Serial.print(F("press ")); Serial.println(i);
      } else if (activeKey == i) {
        stopNote();
        activeKey = -1;
        Serial.print(F("release ")); Serial.println(i);
      }
    }
  }
}

void setup() {
  for (uint8_t i = 0; i < NUM_KEYS; i++) pinMode(KEY_PIN[i], INPUT_PULLUP);
  pinMode(SPEAKER_PIN, OUTPUT);
  Serial.begin(115200);
  loadFromEeprom();                 // defaults if nothing saved yet
  Serial.println(F("physical_piano ready (11 keys, tunable, monophonic)"));
  printHelp();
  printList();
}

void loop() {
  pollSerial();
  pollKeys();

  // End an audition once its window elapses (unless a real key is held).
  if (auditionUntil && millis() >= auditionUntil && activeKey == -1) {
    stopNote();
    auditionUntil = 0;
  }
}
