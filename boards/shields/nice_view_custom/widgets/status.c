/*
 * Custom nice!view status screen for the Miryoku Corne -- left (central) half.
 * Based on ZMK's nice_view widgets, Copyright (c) 2025 The ZMK Contributors.
 * SPDX-License-Identifier: MIT
 *
 * Layout (portrait, 68 x 160), same style as the right half:
 *   top     battery + output symbol, "USB" or "BLE <profile>" with its state,
 *           layer name (outlined on a default layer, inverted while a layer is held)
 *   middle  left hand of the active Miryoku layer (the right screen shows the right
 *           hand); keys that do nothing on that layer are left blank
 *   bottom  hint (which thumb holds the layer)
 */

#include <stdio.h>
#include <string.h>
#include <zephyr/kernel.h>

#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#include <zmk/battery.h>
#include <zmk/display.h>
#include "status.h"
#include "layer_art.h"
#include <zmk/events/usb_conn_state_changed.h>
#include <zmk/event_manager.h>
#include <zmk/events/battery_state_changed.h>
#include <zmk/events/ble_active_profile_changed.h>
#include <zmk/events/endpoint_changed.h>
#include <zmk/events/layer_state_changed.h>
#include <zmk/usb.h>
#include <zmk/ble.h>
#include <zmk/endpoints.h>
#include <zmk/keymap.h>

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
    uint8_t id; // Miryoku layer id (devicetree order), used to pick the key map
    uint32_t active;
    const char *label;
};


/* ------------------------------------------------------------------ drawing */

static const struct art_layer *shown_layer(const struct status_state *state) {
    return &art_layers_left[state->layer_id < ART_LAYER_COUNT ? state->layer_id : 0];
}

static void draw_top(lv_obj_t *widget, const struct status_state *state) {
    lv_obj_t *canvas = lv_obj_get_child(widget, 0);

    lv_draw_label_dsc_t symbol_dsc;
    init_label_dsc(&symbol_dsc, LVGL_FOREGROUND, &lv_font_montserrat_16, LV_TEXT_ALIGN_RIGHT);
    lv_draw_label_dsc_t text_dsc;
    init_label_dsc(&text_dsc, LVGL_FOREGROUND, &lv_font_unscii_8, LV_TEXT_ALIGN_CENTER);
    lv_draw_label_dsc_t badge_bg;
    init_label_dsc(&badge_bg, LVGL_BACKGROUND, &lv_font_montserrat_16, LV_TEXT_ALIGN_CENTER);
    lv_draw_label_dsc_t badge_fg;
    init_label_dsc(&badge_fg, LVGL_FOREGROUND, &lv_font_montserrat_16, LV_TEXT_ALIGN_CENTER);

    lv_canvas_fill_bg(canvas, LVGL_BACKGROUND, LV_OPA_COVER);
    draw_battery(canvas, state);

    // output: symbol top right, "USB" / "BLE n" and its state below the battery
    char line[12] = {};
    const char *status = "";
    if (state->selected_endpoint.transport == ZMK_TRANSPORT_USB) {
        canvas_draw_text(canvas, 0, 0, CANVAS_SIZE, &symbol_dsc, LV_SYMBOL_USB);
        strcpy(line, "USB");
    } else {
        canvas_draw_text(canvas, 0, 0, CANVAS_SIZE, &symbol_dsc, LV_SYMBOL_BLUETOOTH);
        snprintf(line, sizeof(line), "BLE %d", state->active_profile_index + 1);
        if (!state->active_profile_bonded) {
            status = "PAIRING"; // open profile, advertising for a new host
        } else if (state->active_profile_connected) {
            status = "CONNECTED";
        } else {
            status = "WAITING"; // paired host not connected
        }
    }
    canvas_draw_text(canvas, 0, 19, CANVAS_SIZE, &text_dsc, line);
    art_draw_tiny(canvas, 0, 30, CANVAS_SIZE, status, true);

    // layer badge: outlined on a default layer (Base / Extra / Tap), inverted otherwise
    const struct art_layer *layer = shown_layer(state);
    if (state->layer_id >= 3) {
        fill_fg(canvas, 0, 40, CANVAS_SIZE, 24);
        canvas_draw_text(canvas, 0, 43, CANVAS_SIZE, &badge_bg, layer->name);
    } else {
        outline_fg(canvas, 0, 40, CANVAS_SIZE, 24, 1);
        canvas_draw_text(canvas, 0, 43, CANVAS_SIZE, &badge_fg, layer->name);
    }

    rotate_canvas(canvas);
}

static void draw_layer(lv_obj_t *widget, const struct status_state *state) {
    lv_obj_t *middle = lv_obj_get_child(widget, 1);
    lv_obj_t *bottom = lv_obj_get_child(widget, 2);
    const struct art_layer *layer = shown_layer(state);

    lv_canvas_fill_bg(middle, LVGL_BACKGROUND, LV_OPA_COVER);
    art_draw_keys(middle, layer, true);
    rotate_canvas(middle);
    lv_obj_invalidate(middle);

    lv_canvas_fill_bg(bottom, LVGL_BACKGROUND, LV_OPA_COVER);
    art_draw_tiny(bottom, 0, 10, CANVAS_SIZE, layer->hint, true);
    rotate_canvas(bottom);
    lv_obj_invalidate(bottom);
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
    const bool changed = widget->state.layer_id != state.id;
    widget->state.layer_index = state.index;
    widget->state.layer_id = state.id;
    widget->state.layers_active = state.active;
    widget->state.layer_label = state.label;

    draw_top(widget->obj, &widget->state);
    if (changed) {
        draw_layer(widget->obj, &widget->state);
    }
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
        .id = zmk_keymap_layer_index_to_id(index),
        .active = active,
        .label = zmk_keymap_layer_name(zmk_keymap_layer_index_to_id(index)),
    };
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_layer_status, struct layer_status_state, layer_status_update_cb,
                            layer_status_get_state)
ZMK_SUBSCRIPTION(widget_layer_status, zmk_layer_state_changed);

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

    widget->state.layer_id = 0;
    draw_layer(widget->obj, &widget->state);

    sys_slist_append(&widgets, &widget->node);
    widget_battery_status_init();
    widget_output_status_init();
    widget_layer_status_init();

    return 0;
}

lv_obj_t *zmk_widget_status_obj(struct zmk_widget_status *widget) { return widget->obj; }
