/*
 * Raised on every half when a &mo_sync layer hold starts or ends.
 * SPDX-License-Identifier: MIT
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>
#include <zmk/event_manager.h>

struct zmk_layer_sync_changed {
    uint8_t layer; // Miryoku layer id (devicetree order of the keymap layers)
    bool state;    // true = held, false = released
};

ZMK_EVENT_DECLARE(zmk_layer_sync_changed);
