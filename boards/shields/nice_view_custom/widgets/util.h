/*
 * Custom nice!view status screen for the Miryoku Corne.
 * Based on ZMK's nice_view widgets, Copyright (c) 2025 The ZMK Contributors.
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include <zephyr/kernel.h>
#include <lvgl.h>
#include <zmk/endpoints.h>

#define NICEVIEW_PROFILE_COUNT 5
#define MIRYOKU_LAYER_PIPS 10

// The nice!view is 160x68. It is drawn as three 68x68 canvases that are rotated
// 270 degrees, so on the keyboard it reads in portrait: 68 px wide, 160 px tall.
// In canvas coordinates x runs left->right and y top->bottom as you look at it.
// Top canvas: 68 px tall, middle canvas: 68 px tall, bottom canvas: 24 px tall.
#define CANVAS_SIZE 68
#define BOTTOM_VISIBLE 24
#define CANVAS_COLOR_FORMAT LV_COLOR_FORMAT_L8 // smallest type supported by sw_rotate
#define CANVAS_BUF_SIZE                                                                            \
    LV_CANVAS_BUF_SIZE(CANVAS_SIZE, CANVAS_SIZE, LV_COLOR_FORMAT_GET_BPP(CANVAS_COLOR_FORMAT),     \
                       LV_DRAW_BUF_STRIDE_ALIGN)

#define LVGL_BACKGROUND                                                                            \
    (IS_ENABLED(CONFIG_NICE_VIEW_CUSTOM_INVERTED) ? lv_color_black() : lv_color_white())
#define LVGL_FOREGROUND                                                                            \
    (IS_ENABLED(CONFIG_NICE_VIEW_CUSTOM_INVERTED) ? lv_color_white() : lv_color_black())

// Modifier bits, merged left/right, in Miryoku home-row order (pinky -> index).
#define MOD_BIT_GUI BIT(0)
#define MOD_BIT_ALT BIT(1)
#define MOD_BIT_CTRL BIT(2)
#define MOD_BIT_SHIFT BIT(3)

struct status_state {
    uint8_t battery;
    bool charging;
#if !IS_ENABLED(CONFIG_ZMK_SPLIT) || IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    struct zmk_endpoint_instance selected_endpoint;
    int active_profile_index;
    bool active_profile_connected;
    bool active_profile_bonded;
    bool profiles_connected[NICEVIEW_PROFILE_COUNT];
    bool profiles_bonded[NICEVIEW_PROFILE_COUNT];
    uint8_t layer_index;
    uint8_t layer_id;        // Miryoku layer id of the highest active layer
    uint32_t layers_active; // bit i = layer index i is active
    const char *layer_label;
    uint8_t mods;
    uint8_t wpm;
#else
    bool connected;
    uint8_t layer_shown; // Miryoku layer id drawn on the right half (0 = Base)
    bool layer_held;
#endif
};

struct battery_status_state {
    uint8_t level;
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
    bool usb_present;
#endif
};

void rotate_canvas(lv_obj_t *canvas);
void draw_battery(lv_obj_t *canvas, const struct status_state *state);
void init_label_dsc(lv_draw_label_dsc_t *label_dsc, lv_color_t color, const lv_font_t *font,
                    lv_text_align_t align);
void init_rect_dsc(lv_draw_rect_dsc_t *rect_dsc, lv_color_t bg_color);

void canvas_draw_rect(lv_obj_t *canvas, lv_coord_t x, lv_coord_t y, lv_coord_t w, lv_coord_t h,
                      lv_draw_rect_dsc_t *draw_dsc);
void canvas_draw_text(lv_obj_t *canvas, lv_coord_t x, lv_coord_t y, lv_coord_t max_w,
                      lv_draw_label_dsc_t *draw_dsc, const char *txt);
void canvas_draw_img(lv_obj_t *canvas, lv_coord_t x, lv_coord_t y, const lv_image_dsc_t *src,
                     lv_draw_image_dsc_t *draw_dsc);

// Filled rectangle in the foreground colour.
void fill_fg(lv_obj_t *canvas, lv_coord_t x, lv_coord_t y, lv_coord_t w, lv_coord_t h);
// Rectangle outline (thickness t) in the foreground colour, interior cleared.
void outline_fg(lv_obj_t *canvas, lv_coord_t x, lv_coord_t y, lv_coord_t w, lv_coord_t h,
                lv_coord_t t);
