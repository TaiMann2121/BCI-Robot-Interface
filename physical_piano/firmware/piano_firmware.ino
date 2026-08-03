/*
 * piano_firmware — key scanner for the physical piano
 * ---------------------------------------------------
 * Reads 18 key switches (11 white + 7 black) and reports press/release events
 * over USB serial. It makes NO SOUND: the PC plays the notes, which is how the
 * BCI2000 simulator already works (Piano_Application_vel.py builds
 * psychopy.sound objects). See ../pc/piano_listener.py for the other half.
 *
 * WHY NO PIEZO: an Arduino Uno has 18 usable digital pins once D0/D1 are
 * reserved for the USB serial this sketch depends on. 18 switches need all 18.
 * Driving a speaker as well would need a 19th pin, so sound moved to the PC —
 * which also gets real samples, polyphony and software tuning for free.
 *
 * Board:   Arduino Uno / Nano
 * Sensing: momentary MX switches, each between its pin and GND. INPUT_PULLUP
 *          is used, so NO external resistors. A pressed key reads LOW.
 *          Kailh CPG1511F01S04-1: bounce is 5 ms new / 10 ms end-of-life, so
 *          the 15 ms debounce below has margin over the whole switch life.
 *          The switch needs >= 10 uA wetting current; the internal pull-up
 *          supplies ~167 uA at 5 V, inside its 10 uA .. 10 mA rating.
 *
 * ---- Serial protocol, 115200 baud, newline-terminated ----
 *   out:  P <id>     key pressed
 *         R <id>     key released
 *         READY 18   sent once at boot, with the key count
 *   in :  ping       -> replies PONG
 *         keys       -> lists every id with its pin and label
 *
 * <id> is 0..17:  0-10  = white keys, left to right (0 is the leftmost key,
 *                         matching the simulator and the notch on the board)
 *                11-17  = black keys, left to right
 */

const uint8_t N_WHITE = 11;
const uint8_t N_BLACK = 7;
const uint8_t N_KEYS  = N_WHITE + N_BLACK;   // 18

// White keys, left to right. D2..D12.
const uint8_t WHITE_PIN[N_WHITE] = { 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 };

// Black keys, left to right. These sit in the white-key gaps
// [0,2,3,5,6,7,9] — the same black_idx as piano_params.scad and the simulator.
//
// D13 IS DELIBERATELY LAST. On many Uno clones pin 13 carries the onboard LED
// directly, which can load INPUT_PULLUP enough to read unreliably. It is
// therefore given the RIGHTMOST black key — a decorative padding key the task
// never presses — so if that pin misbehaves nothing important is affected.
const uint8_t BLACK_PIN[N_BLACK] = { A5, A0, A1, A2, A3, A4, 13 };

// Which white-key gap each black key sits in (for the `keys` listing only).
const uint8_t BLACK_GAP[N_BLACK] = { 0, 2, 3, 5, 6, 7, 9 };

const unsigned long DEBOUNCE_MS = 15;

bool          state[N_KEYS];        // debounced: true = pressed
bool          lastRead[N_KEYS];
unsigned long lastChange[N_KEYS];

char    cmd[16];
uint8_t cmdLen = 0;

uint8_t pinFor(uint8_t id) {
  return (id < N_WHITE) ? WHITE_PIN[id] : BLACK_PIN[id - N_WHITE];
}

void setup() {
  for (uint8_t i = 0; i < N_KEYS; i++) {
    pinMode(pinFor(i), INPUT_PULLUP);
    state[i] = lastRead[i] = false;
    lastChange[i] = 0;
  }
  Serial.begin(115200);
  Serial.print(F("READY "));
  Serial.println(N_KEYS);
}

void listKeys() {
  for (uint8_t i = 0; i < N_WHITE; i++) {
    Serial.print(F("  id ")); Serial.print(i);
    Serial.print(F("  pin D")); Serial.print(WHITE_PIN[i]);
    Serial.print(F("  white ")); Serial.println(i);
  }
  for (uint8_t k = 0; k < N_BLACK; k++) {
    Serial.print(F("  id ")); Serial.print(N_WHITE + k);
    Serial.print(F("  pin ")); Serial.print(BLACK_PIN[k]);
    Serial.print(F("  black between white "));
    Serial.print(BLACK_GAP[k]); Serial.print('/');
    Serial.println(BLACK_GAP[k] + 1);
  }
}

void pollSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (cmdLen) {
        cmd[cmdLen] = '\0';
        if      (!strcasecmp(cmd, "ping")) Serial.println(F("PONG"));
        else if (!strcasecmp(cmd, "keys")) listKeys();
        cmdLen = 0;
      }
    } else if (cmdLen < sizeof(cmd) - 1) {
      cmd[cmdLen++] = c;
    }
  }
}

void loop() {
  pollSerial();

  unsigned long now = millis();
  for (uint8_t i = 0; i < N_KEYS; i++) {
    bool reading = (digitalRead(pinFor(i)) == LOW);   // pressed == LOW

    if (reading != lastRead[i]) {
      lastRead[i]   = reading;
      lastChange[i] = now;
    }
    if ((now - lastChange[i]) >= DEBOUNCE_MS && reading != state[i]) {
      state[i] = reading;
      Serial.print(state[i] ? F("P ") : F("R "));
      Serial.println(i);
    }
  }
}
