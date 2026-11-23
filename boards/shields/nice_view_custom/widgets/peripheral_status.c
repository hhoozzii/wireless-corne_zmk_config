/*
 * Custom nice!view status screen for the Miryoku Corne -- right (peripheral) half.
 * Based on ZMK's nice_view widgets, Copyright (c) 2023 The ZMK Contributors.
 * SPDX-License-Identifier: MIT
 *
 * Layout (portrait, 68 x 160):
 *   top     battery + link to the left half, link state, "corne" badge
 *   middle  map of the right half's Miryoku QWERTY keys; home-row mods
 *           (Shift Ctrl Alt GUI) shown inverted, thumbs drawn below
 *   bottom  "MIRYOKU"
 */

#include <zephyr/kernel.h>

#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#include <zmk/battery.h>
#include <zmk/display.h>
#include <zmk/events/usb_conn_state_changed.h>
#include <zmk/event_manager.h>
#include <zmk/events/battery_state_changed.h>
#include <zmk/split/bluetooth/peripheral.h>
#include <zmk/events/split_peripheral_status_changed.h>
#include <zmk/usb.h>
#include <zmk/ble.h>

#include "peripheral_status.h"

static sys_slist_t widgets = SYS_SLIST_STATIC_INIT(&widgets);

struct peripheral_status_state {
    bool connected;
};

static void draw_top(lv_obj_t *widget, const struct status_state *state) {
    lv_obj_t *canvas = lv_obj_get_child(widget, 0);

    lv_draw_label_dsc_t symbol_dsc;
    init_label_dsc(&symbol_dsc, LVGL_FOREGROUND, &lv_font_montserrat_16, LV_TEXT_ALIGN_RIGHT);
    lv_draw_label_dsc_t small_dsc;
    init_label_dsc(&small_dsc, LVGL_FOREGROUND, &lv_font_unscii_8, LV_TEXT_ALIGN_CENTER);
    lv_draw_label_dsc_t badge_dsc;
    init_label_dsc(&badge_dsc, LVGL_BACKGROUND, &lv_font_montserrat_16, LV_TEXT_ALIGN_CENTER);

    lv_canvas_fill_bg(canvas, LVGL_BACKGROUND, LV_OPA_COVER);

    draw_battery(canvas, state);
    canvas_draw_text(canvas, 0, 0, CANVAS_SIZE, &symbol_dsc,
                     state->connected ? LV_SYMBOL_WIFI : LV_SYMBOL_CLOSE);

    canvas_draw_text(canvas, 0, 24, CANVAS_SIZE, &small_dsc,
                     state->connected ? "linked" : "no link");

    fill_fg(canvas, 0, 40, CANVAS_SIZE, 24);
    canvas_draw_text(canvas, 0, 43, CANVAS_SIZE, &badge_dsc, "corne");

    rotate_canvas(canvas);
}

static void draw_art(lv_obj_t *widget) {
    lv_obj_t *middle = lv_obj_get_child(widget, 1);
    lv_obj_t *bottom = lv_obj_get_child(widget, 2);

    lv_draw_label_dsc_t key_fg;
    init_label_dsc(&key_fg, LVGL_FOREGROUND, &lv_font_unscii_8, LV_TEXT_ALIGN_CENTER);
    lv_draw_label_dsc_t key_bg;
    init_label_dsc(&key_bg, LVGL_BACKGROUND, &lv_font_unscii_8, LV_TEXT_ALIGN_CENTER);

    // Right half of Miryoku QWERTY. Home row keys carry mods: J=Shift K=Ctrl L=Alt '=GUI
    static const char *const keys[3][5] = {
        {"Y", "U", "I", "O", "P"},
        {"H", "J", "K", "L", "'"},
        {"N", "M", ",", ".", "/"},
    };

    lv_canvas_fill_bg(middle, LVGL_BACKGROUND, LV_OPA_COVER);
    for (int r = 0; r < 3; r++) {
        for (int c = 0; c < 5; c++) {
            const lv_coord_t x = c * 14;
            const lv_coord_t y = 2 + r * 14;
            const bool mod = (r == 1 && c >= 1);
            if (mod) {
                fill_fg(middle, x, y, 12, 12);
            } else {
                outline_fg(middle, x, y, 12, 12, 1);
            }
            canvas_draw_text(middle, x, y + 2, 12, mod ? &key_bg : &key_fg, keys[r][c]);
        }
    }

    // Thumb cluster (Enter / Backspace / Delete), inner side, fanned downwards
    outline_fg(middle, 0, 47, 14, 14, 1);
    outline_fg(middle, 16, 48, 14, 15, 1);
    outline_fg(middle, 32, 50, 14, 16, 1);
    fill_fg(middle, 4, 53, 6, 2);    // enter
    fill_fg(middle, 20, 55, 6, 2);   // backspace
    fill_fg(middle, 36, 57, 6, 2);   // delete
    rotate_canvas(middle);

    lv_canvas_fill_bg(bottom, LVGL_BACKGROUND, LV_OPA_COVER);
    canvas_draw_text(bottom, 0, 8, CANVAS_SIZE, &key_fg, "MIRYOKU");
    rotate_canvas(bottom);
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
    return (struct battery_status_state){
        .level = zmk_battery_state_of_charge(),
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

/* --------------------------------------------------------------------- link */

static struct peripheral_status_state get_state(const zmk_event_t *_eh) {
    return (struct peripheral_status_state){.connected = zmk_split_bt_peripheral_is_connected()};
}

static void set_connection_status(struct zmk_widget_status *widget,
                                  struct peripheral_status_state state) {
    widget->state.connected = state.connected;
    draw_top(widget->obj, &widget->state);
}

static void output_status_update_cb(struct peripheral_status_state state) {
    struct zmk_widget_status *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) { set_connection_status(widget, state); }
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_peripheral_status, struct peripheral_status_state,
                            output_status_update_cb, get_state)
ZMK_SUBSCRIPTION(widget_peripheral_status, zmk_split_peripheral_status_changed);

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

    draw_art(widget->obj);

    sys_slist_append(&widgets, &widget->node);
    widget_battery_status_init();
    widget_peripheral_status_init();

    return 0;
}

lv_obj_t *zmk_widget_status_obj(struct zmk_widget_status *widget) { return widget->obj; }
