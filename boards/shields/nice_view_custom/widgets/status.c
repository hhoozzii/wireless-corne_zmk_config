/*
 * Custom nice!view status screen for the Miryoku Corne -- left (central) half.
 * Based on ZMK's nice_view widgets, Copyright (c) 2025 The ZMK Contributors.
 * SPDX-License-Identifier: MIT
 *
 * Layout (portrait, 68 x 160):
 *   top     battery + output (USB / BLE state)
 *           current Miryoku layer name in an inverted bar
 *           ten layer pips (filled = active, underline = the one you're on)
 *   middle  home-row mods G A C S, lit while held
 *           Bluetooth profiles 1-5 (filled = selected, thick = connected,
 *           thin = paired, none = free)
 *   bottom  words per minute
 */

#include <stdio.h>
#include <string.h>
#include <zephyr/kernel.h>

#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#include <dt-bindings/zmk/hid_usage.h>
#include <zmk/battery.h>
#include <zmk/display.h>
#include "status.h"
#include <zmk/events/usb_conn_state_changed.h>
#include <zmk/event_manager.h>
#include <zmk/events/battery_state_changed.h>
#include <zmk/events/ble_active_profile_changed.h>
#include <zmk/events/endpoint_changed.h>
#include <zmk/events/wpm_state_changed.h>
#include <zmk/events/layer_state_changed.h>
#include <zmk/events/keycode_state_changed.h>
#include <zmk/usb.h>
#include <zmk/ble.h>
#include <zmk/endpoints.h>
#include <zmk/keymap.h>
#include <zmk/wpm.h>

static sys_slist_t widgets = SYS_SLIST_STATIC_INIT(&widgets);

struct output_status_state {
    struct zmk_endpoint_instance selected_endpoint;
    int active_profile_index;
    bool active_profile_connected;
    bool active_profile_bonded;
    bool profiles_connected[NICEVIEW_PROFILE_COUNT];
    bool profiles_bonded[NICEVIEW_PROFILE_COUNT];
};

struct layer_status_state {
    zmk_keymap_layer_index_t index;
    uint32_t active;
    const char *label;
};

struct wpm_status_state {
    uint8_t wpm;
};

struct mods_status_state {
    uint8_t mods;
};

/* ------------------------------------------------------------------ drawing */

static void draw_top(lv_obj_t *widget, const struct status_state *state) {
    lv_obj_t *canvas = lv_obj_get_child(widget, 0);

    lv_draw_label_dsc_t output_dsc;
    init_label_dsc(&output_dsc, LVGL_FOREGROUND, &lv_font_montserrat_16, LV_TEXT_ALIGN_RIGHT);
    lv_draw_label_dsc_t layer_dsc;
    init_label_dsc(&layer_dsc, LVGL_BACKGROUND, &lv_font_montserrat_18, LV_TEXT_ALIGN_CENTER);

    lv_canvas_fill_bg(canvas, LVGL_BACKGROUND, LV_OPA_COVER);

    // Battery + output
    draw_battery(canvas, state);

    char output_text[12] = {};
    switch (state->selected_endpoint.transport) {
    case ZMK_TRANSPORT_USB:
        strcat(output_text, LV_SYMBOL_USB);
        break;
    case ZMK_TRANSPORT_BLE:
        if (state->active_profile_bonded) {
            strcat(output_text,
                   state->active_profile_connected ? LV_SYMBOL_WIFI : LV_SYMBOL_CLOSE);
        } else {
            strcat(output_text, LV_SYMBOL_SETTINGS); // advertising, waiting to pair
        }
        break;
    default:
        break;
    }
    canvas_draw_text(canvas, 0, 0, CANVAS_SIZE, &output_dsc, output_text);

    // Layer name bar
    fill_fg(canvas, 0, 19, CANVAS_SIZE, 26);
    const char *label = state->layer_label;
    char fallback[10] = {};
    if (label == NULL || label[0] == '\0') {
        snprintf(fallback, sizeof(fallback), "L%d", state->layer_index);
        label = fallback;
    }
    canvas_draw_text(canvas, 0, 22, CANVAS_SIZE, &layer_dsc, label);

    // Layer pips: 10 x (5 wide, 1 gap) = 59 px, centred
    for (int i = 0; i < MIRYOKU_LAYER_PIPS; i++) {
        const lv_coord_t x = 4 + i * 6;
        if (state->layers_active & BIT(i)) {
            fill_fg(canvas, x, 51, 5, 8);
        } else {
            outline_fg(canvas, x, 51, 5, 8, 1);
        }
        if (i == state->layer_index) {
            fill_fg(canvas, x, 62, 5, 2);
        }
    }

    rotate_canvas(canvas);
}

static void draw_middle(lv_obj_t *widget, const struct status_state *state) {
    lv_obj_t *canvas = lv_obj_get_child(widget, 1);

    lv_draw_label_dsc_t mod_fg;
    init_label_dsc(&mod_fg, LVGL_FOREGROUND, &lv_font_montserrat_14, LV_TEXT_ALIGN_CENTER);
    lv_draw_label_dsc_t mod_bg;
    init_label_dsc(&mod_bg, LVGL_BACKGROUND, &lv_font_montserrat_14, LV_TEXT_ALIGN_CENTER);
    lv_draw_label_dsc_t bt_fg;
    init_label_dsc(&bt_fg, LVGL_FOREGROUND, &lv_font_unscii_8, LV_TEXT_ALIGN_CENTER);
    lv_draw_label_dsc_t bt_bg;
    init_label_dsc(&bt_bg, LVGL_BACKGROUND, &lv_font_unscii_8, LV_TEXT_ALIGN_CENTER);

    lv_canvas_fill_bg(canvas, LVGL_BACKGROUND, LV_OPA_COVER);

    // Home-row mods, same order as Miryoku's A S D F: GUI ALT CTRL SHIFT
    static const char *const mod_names[] = {"G", "A", "C", "S"};
    for (int i = 0; i < 4; i++) {
        const lv_coord_t x = i * 17;
        const bool held = state->mods & BIT(i);
        if (held) {
            fill_fg(canvas, x, 2, 16, 22);
        } else {
            outline_fg(canvas, x, 2, 16, 22, 1);
        }
        canvas_draw_text(canvas, x, 5, 16, held ? &mod_bg : &mod_fg, mod_names[i]);
    }

    // Divider
    fill_fg(canvas, 0, 31, CANVAS_SIZE, 1);

    // Bluetooth profiles: 5 x 12 px with 2 px gaps = 68 px
    for (int i = 0; i < NICEVIEW_PROFILE_COUNT; i++) {
        const lv_coord_t x = i * 14;
        const lv_coord_t y = 40;
        const bool selected = i == state->active_profile_index;

        if (selected) {
            fill_fg(canvas, x, y, 12, 18);
        } else if (state->profiles_connected[i]) {
            outline_fg(canvas, x, y, 12, 18, 2);
        } else if (state->profiles_bonded[i]) {
            outline_fg(canvas, x, y, 12, 18, 1);
        }

        char num[2] = {(char)('1' + i), '\0'};
        canvas_draw_text(canvas, x, y + 5, 12, selected ? &bt_bg : &bt_fg, num);

        // Connected marker under the box
        if (state->profiles_connected[i]) {
            fill_fg(canvas, x + 4, y + 21, 4, 2);
        }
    }

    rotate_canvas(canvas);
}

static void draw_bottom(lv_obj_t *widget, const struct status_state *state) {
    lv_obj_t *canvas = lv_obj_get_child(widget, 2);

    lv_draw_label_dsc_t label_dsc;
    init_label_dsc(&label_dsc, LVGL_FOREGROUND, &lv_font_unscii_8, LV_TEXT_ALIGN_CENTER);

    lv_canvas_fill_bg(canvas, LVGL_BACKGROUND, LV_OPA_COVER);

    char text[12] = {};
    snprintf(text, sizeof(text), "%u WPM", state->wpm);
    canvas_draw_text(canvas, 0, 8, CANVAS_SIZE, &label_dsc, text);

    rotate_canvas(canvas);
}

/* ------------------------------------------------------------------ battery */

static void set_battery_status(struct zmk_widget_status *widget,
                               struct battery_status_state state) {
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
    widget->state.charging = state.usb_present;
#endif
    widget->state.battery = state.level;
    draw_top(widget->obj, &widget->state);
}

static void battery_status_update_cb(struct battery_status_state state) {
    struct zmk_widget_status *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) { set_battery_status(widget, state); }
}

static struct battery_status_state battery_status_get_state(const zmk_event_t *eh) {
    const struct zmk_battery_state_changed *ev = as_zmk_battery_state_changed(eh);

    return (struct battery_status_state){
        .level = (ev != NULL) ? ev->state_of_charge : zmk_battery_state_of_charge(),
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
        .usb_present = zmk_usb_is_powered(),
#endif
    };
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_battery_status, struct battery_status_state,
                            battery_status_update_cb, battery_status_get_state)
ZMK_SUBSCRIPTION(widget_battery_status, zmk_battery_state_changed);
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
ZMK_SUBSCRIPTION(widget_battery_status, zmk_usb_conn_state_changed);
#endif

/* ------------------------------------------------------------------- output */

static void set_output_status(struct zmk_widget_status *widget,
                              const struct output_status_state *state) {
    widget->state.selected_endpoint = state->selected_endpoint;
    widget->state.active_profile_index = state->active_profile_index;
    widget->state.active_profile_connected = state->active_profile_connected;
    widget->state.active_profile_bonded = state->active_profile_bonded;
    for (int i = 0; i < NICEVIEW_PROFILE_COUNT; ++i) {
        widget->state.profiles_connected[i] = state->profiles_connected[i];
        widget->state.profiles_bonded[i] = state->profiles_bonded[i];
    }

    draw_top(widget->obj, &widget->state);
    draw_middle(widget->obj, &widget->state);
}

static void output_status_update_cb(struct output_status_state state) {
    struct zmk_widget_status *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) { set_output_status(widget, &state); }
}

static struct output_status_state output_status_get_state(const zmk_event_t *_eh) {
    struct output_status_state state = {
        .selected_endpoint = zmk_endpoint_get_selected(),
        .active_profile_index = zmk_ble_active_profile_index(),
        .active_profile_connected = zmk_ble_active_profile_is_connected(),
        .active_profile_bonded = !zmk_ble_active_profile_is_open(),
    };
    for (int i = 0; i < MIN(NICEVIEW_PROFILE_COUNT, ZMK_BLE_PROFILE_COUNT); ++i) {
        state.profiles_connected[i] = zmk_ble_profile_is_connected(i);
        state.profiles_bonded[i] = !zmk_ble_profile_is_open(i);
    }
    return state;
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_output_status, struct output_status_state,
                            output_status_update_cb, output_status_get_state)
ZMK_SUBSCRIPTION(widget_output_status, zmk_endpoint_changed);
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
ZMK_SUBSCRIPTION(widget_output_status, zmk_usb_conn_state_changed);
#endif
#if defined(CONFIG_ZMK_BLE)
ZMK_SUBSCRIPTION(widget_output_status, zmk_ble_active_profile_changed);
#endif

/* -------------------------------------------------------------------- layer */

static void set_layer_status(struct zmk_widget_status *widget, struct layer_status_state state) {
    widget->state.layer_index = state.index;
    widget->state.layers_active = state.active;
    widget->state.layer_label = state.label;

    draw_top(widget->obj, &widget->state);
}

static void layer_status_update_cb(struct layer_status_state state) {
    struct zmk_widget_status *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) { set_layer_status(widget, state); }
}

static struct layer_status_state layer_status_get_state(const zmk_event_t *eh) {
    zmk_keymap_layer_index_t index = zmk_keymap_highest_layer_active();
    uint32_t active = 0;
    for (int i = 0; i < MIN(MIRYOKU_LAYER_PIPS, ZMK_KEYMAP_LAYERS_LEN); i++) {
        if (zmk_keymap_layer_active(zmk_keymap_layer_index_to_id(i))) {
            active |= BIT(i);
        }
    }
    return (struct layer_status_state){
        .index = index,
        .active = active,
        .label = zmk_keymap_layer_name(zmk_keymap_layer_index_to_id(index)),
    };
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_layer_status, struct layer_status_state, layer_status_update_cb,
                            layer_status_get_state)
ZMK_SUBSCRIPTION(widget_layer_status, zmk_layer_state_changed);

/* ---------------------------------------------------------------------- wpm */

static void set_wpm_status(struct zmk_widget_status *widget, struct wpm_status_state state) {
    widget->state.wpm = state.wpm;
    draw_bottom(widget->obj, &widget->state);
}

static void wpm_status_update_cb(struct wpm_status_state state) {
    struct zmk_widget_status *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) { set_wpm_status(widget, state); }
}

static struct wpm_status_state wpm_status_get_state(const zmk_event_t *eh) {
    return (struct wpm_status_state){.wpm = zmk_wpm_get_state()};
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_wpm_status, struct wpm_status_state, wpm_status_update_cb,
                            wpm_status_get_state)
ZMK_SUBSCRIPTION(widget_wpm_status, zmk_wpm_state_changed);

/* --------------------------------------------------------------------- mods */
/*
 * Track held modifiers from keycode events (covers Miryoku's home-row mod-taps
 * on both halves). Counts per modifier so holding Shift on both hands and
 * releasing one keeps the indicator lit. Only redraws when the shown set changes.
 */

K_MUTEX_DEFINE(mods_mutex);
static uint8_t mod_counts[8];
static uint8_t mods_shown;

static uint8_t mods_from_counts(void) {
    // HID order: LCtrl LShift LAlt LGui RCtrl RShift RAlt RGui
    uint8_t m = 0;
    if (mod_counts[0] || mod_counts[4]) {
        m |= MOD_BIT_CTRL;
    }
    if (mod_counts[1] || mod_counts[5]) {
        m |= MOD_BIT_SHIFT;
    }
    if (mod_counts[2] || mod_counts[6]) {
        m |= MOD_BIT_ALT;
    }
    if (mod_counts[3] || mod_counts[7]) {
        m |= MOD_BIT_GUI;
    }
    return m;
}

static void mods_status_update_cb(struct mods_status_state state) {
    struct zmk_widget_status *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) {
        widget->state.mods = state.mods;
        draw_middle(widget->obj, &widget->state);
    }
}

static void mods_work_cb(struct k_work *work) {
    k_mutex_lock(&mods_mutex, K_FOREVER);
    struct mods_status_state state = {.mods = mods_shown};
    k_mutex_unlock(&mods_mutex);
    mods_status_update_cb(state);
}

K_WORK_DEFINE(mods_work, mods_work_cb);

static int mods_listener_cb(const zmk_event_t *eh) {
    const struct zmk_keycode_state_changed *ev = as_zmk_keycode_state_changed(eh);
    if (ev == NULL || ev->usage_page != HID_USAGE_KEY ||
        ev->keycode < HID_USAGE_KEY_KEYBOARD_LEFTCONTROL ||
        ev->keycode > HID_USAGE_KEY_KEYBOARD_RIGHT_GUI) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    const uint8_t bit = ev->keycode - HID_USAGE_KEY_KEYBOARD_LEFTCONTROL;
    bool changed;

    k_mutex_lock(&mods_mutex, K_FOREVER);
    if (ev->state) {
        if (mod_counts[bit] < UINT8_MAX) {
            mod_counts[bit]++;
        }
    } else if (mod_counts[bit] > 0) {
        mod_counts[bit]--;
    }
    const uint8_t now = mods_from_counts();
    changed = now != mods_shown;
    mods_shown = now;
    k_mutex_unlock(&mods_mutex);

    if (changed && zmk_display_is_initialized()) {
        k_work_submit_to_queue(zmk_display_work_q(), &mods_work);
    }
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(widget_mods_status, mods_listener_cb);
ZMK_SUBSCRIPTION(widget_mods_status, zmk_keycode_state_changed);

/* --------------------------------------------------------------------- init */

int zmk_widget_status_init(struct zmk_widget_status *widget, lv_obj_t *parent) {
    widget->obj = lv_obj_create(parent);
    lv_obj_set_size(widget->obj, 160, 68);
    lv_obj_t *top = lv_canvas_create(widget->obj);
    lv_obj_align(top, LV_ALIGN_TOP_RIGHT, 0, 0);
    lv_canvas_set_buffer(top, widget->cbuf, CANVAS_SIZE, CANVAS_SIZE, CANVAS_COLOR_FORMAT);
    lv_obj_t *middle = lv_canvas_create(widget->obj);
    lv_obj_align(middle, LV_ALIGN_TOP_LEFT, 24, 0);
    lv_canvas_set_buffer(middle, widget->cbuf2, CANVAS_SIZE, CANVAS_SIZE, CANVAS_COLOR_FORMAT);
    lv_obj_t *bottom = lv_canvas_create(widget->obj);
    lv_obj_align(bottom, LV_ALIGN_TOP_LEFT, -44, 0);
    lv_canvas_set_buffer(bottom, widget->cbuf3, CANVAS_SIZE, CANVAS_SIZE, CANVAS_COLOR_FORMAT);

    sys_slist_append(&widgets, &widget->node);
    widget_battery_status_init();
    widget_output_status_init();
    widget_layer_status_init();
    widget_wpm_status_init();
    mods_work_cb(NULL);

    return 0;
}

lv_obj_t *zmk_widget_status_obj(struct zmk_widget_status *widget) { return widget->obj; }
