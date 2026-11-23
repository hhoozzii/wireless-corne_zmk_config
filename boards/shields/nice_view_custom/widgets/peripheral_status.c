/*
 * Custom nice!view status screen for the Miryoku Corne -- right (peripheral) half.
 * Based on ZMK's nice_view widgets, Copyright (c) 2023 The ZMK Contributors.
 * SPDX-License-Identifier: MIT
 *
 * Layout (portrait, 68 x 160):
 *   top     battery + link to the left half, link state, layer name
 *           (outlined on Base, inverted while a layer is held)
 *   middle  right hand of the active Miryoku layer (the left screen shows the left
 *           hand); keys that do nothing on that layer are left blank
 *   bottom  hint (which hand is shown / which thumb holds the layer)
 *
 * The right half does not normally know the active layer. Layer holds use the
 * &mo_sync behavior (module src/behaviors/behavior_layer_sync.c), which runs on
 * both halves and raises zmk_layer_sync_changed here.
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

#include <zmk_layer_sync/layer_sync_changed.h>

#include "peripheral_status.h"
#include "layer_art.h"

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
    lv_draw_label_dsc_t badge_fg_dsc;
    init_label_dsc(&badge_fg_dsc, LVGL_FOREGROUND, &lv_font_montserrat_16, LV_TEXT_ALIGN_CENTER);
    const struct art_layer *layer = &art_layers_right[state->layer_shown];

    lv_canvas_fill_bg(canvas, LVGL_BACKGROUND, LV_OPA_COVER);

    draw_battery(canvas, state);
    canvas_draw_text(canvas, 0, 0, CANVAS_SIZE, &symbol_dsc,
                     state->connected ? LV_SYMBOL_WIFI : LV_SYMBOL_CLOSE);

    canvas_draw_text(canvas, 0, 24, CANVAS_SIZE, &small_dsc,
                     state->connected ? "linked" : "no link");

    if (state->layer_held) {
        fill_fg(canvas, 0, 40, CANVAS_SIZE, 24);
        canvas_draw_text(canvas, 0, 43, CANVAS_SIZE, &badge_dsc, layer->name);
    } else {
        outline_fg(canvas, 0, 40, CANVAS_SIZE, 24, 1);
        canvas_draw_text(canvas, 0, 43, CANVAS_SIZE, &badge_fg_dsc, layer->name);
    }

    rotate_canvas(canvas);
}

static void draw_layer(lv_obj_t *widget, const struct status_state *state) {
    lv_obj_t *middle = lv_obj_get_child(widget, 1);
    lv_obj_t *bottom = lv_obj_get_child(widget, 2);
    const struct art_layer *layer = &art_layers_right[state->layer_shown];

    lv_canvas_fill_bg(middle, LVGL_BACKGROUND, LV_OPA_COVER);
    art_draw_keys(middle, layer, false);
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
    if (!state.connected && widget->state.layer_held) { // a hold can't be released over a dead link
        widget->state.layer_held = false;
        widget->state.layer_shown = 0;
        draw_layer(widget->obj, &widget->state);
    }
    draw_top(widget->obj, &widget->state);
}

static void output_status_update_cb(struct peripheral_status_state state) {
    struct zmk_widget_status *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) { set_connection_status(widget, state); }
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_peripheral_status, struct peripheral_status_state,
                            output_status_update_cb, get_state)
ZMK_SUBSCRIPTION(widget_peripheral_status, zmk_split_peripheral_status_changed);

/* -------------------------------------------------------------- layer sync */

struct layer_sync_state {
    uint16_t active; // bit i = layer id i held (as reported by &mo_sync)
};

static uint16_t synced_layers;

static struct layer_sync_state layer_sync_get_state(const zmk_event_t *eh) {
    const struct zmk_layer_sync_changed *ev = eh ? as_zmk_layer_sync_changed(eh) : NULL;
    if (ev && ev->layer < 16) {
        if (ev->state) {
            synced_layers |= BIT(ev->layer);
        } else {
            synced_layers &= ~BIT(ev->layer);
        }
    }
    if (!zmk_split_bt_peripheral_is_connected()) {
        synced_layers = 0;
    }
    return (struct layer_sync_state){.active = synced_layers};
}

static void layer_sync_update_cb(struct layer_sync_state state) {
    uint8_t shown = 0; // highest held layer wins, like ZMK's own layer priority
    for (int i = ART_LAYER_COUNT - 1; i > 0; i--) {
        if (state.active & BIT(i)) {
            shown = i;
            break;
        }
    }
    struct zmk_widget_status *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) {
        widget->state.layer_shown = shown;
        widget->state.layer_held = (shown != 0);
        draw_top(widget->obj, &widget->state);
        draw_layer(widget->obj, &widget->state);
    }
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_layer_sync, struct layer_sync_state, layer_sync_update_cb,
                            layer_sync_get_state)
ZMK_SUBSCRIPTION(widget_layer_sync, zmk_layer_sync_changed);

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

    widget->state.layer_shown = 0;
    widget->state.layer_held = false;
    draw_layer(widget->obj, &widget->state);

    sys_slist_append(&widgets, &widget->node);
    widget_battery_status_init();
    widget_peripheral_status_init();
    widget_layer_sync_init();

    return 0;
}

lv_obj_t *zmk_widget_status_obj(struct zmk_widget_status *widget) { return widget->obj; }
