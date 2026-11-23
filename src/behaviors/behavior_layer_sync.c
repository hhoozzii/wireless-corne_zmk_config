/*
 * &mo_sync <layer>: momentary layer that runs on every half (BEHAVIOR_LOCALITY_GLOBAL).
 * On the central it activates the layer exactly like &mo; on every half it raises
 * zmk_layer_sync_changed, which the right half's nice!view uses to draw the layer.
 * Based on ZMK's behavior_momentary_layer.c, Copyright (c) 2020 The ZMK Contributors.
 * SPDX-License-Identifier: MIT
 */

#define DT_DRV_COMPAT zmk_behavior_layer_sync

#include <zephyr/device.h>
#include <zephyr/logging/log.h>
#include <drivers/behavior.h>

#include <zmk/behavior.h>
#include <zmk_layer_sync/layer_sync_changed.h>

#if !IS_ENABLED(CONFIG_ZMK_SPLIT) || IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
#include <zmk/keymap.h>
#define LAYER_SYNC_IS_CENTRAL 1
#endif

LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)

#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
static const struct behavior_parameter_value_metadata param_values[] = {
    {
        .display_name = "Layer",
        .type = BEHAVIOR_PARAMETER_VALUE_TYPE_LAYER_ID,
    },
};

static const struct behavior_parameter_metadata_set param_metadata_set[] = {{
    .param1_values = param_values,
    .param1_values_len = ARRAY_SIZE(param_values),
}};

static const struct behavior_parameter_metadata metadata = {
    .sets_len = ARRAY_SIZE(param_metadata_set),
    .sets = param_metadata_set,
};
#endif

static int layer_sync_pressed(struct zmk_behavior_binding *binding,
                              struct zmk_behavior_binding_event event) {
    LOG_DBG("position %d layer %d", event.position, binding->param1);
    raise_zmk_layer_sync_changed(
        (struct zmk_layer_sync_changed){.layer = binding->param1, .state = true});
#ifdef LAYER_SYNC_IS_CENTRAL
    return zmk_keymap_layer_activate(binding->param1, false);
#else
    return 0;
#endif
}

static int layer_sync_released(struct zmk_behavior_binding *binding,
                               struct zmk_behavior_binding_event event) {
    LOG_DBG("position %d layer %d", event.position, binding->param1);
    raise_zmk_layer_sync_changed(
        (struct zmk_layer_sync_changed){.layer = binding->param1, .state = false});
#ifdef LAYER_SYNC_IS_CENTRAL
    return zmk_keymap_layer_deactivate(binding->param1, false);
#else
    return 0;
#endif
}

static const struct behavior_driver_api behavior_layer_sync_driver_api = {
    .binding_pressed = layer_sync_pressed,
    .binding_released = layer_sync_released,
    .locality = BEHAVIOR_LOCALITY_GLOBAL,
#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
    .parameter_metadata = &metadata,
#endif
};

#define LAYER_SYNC_INST(n)                                                                         \
    BEHAVIOR_DT_INST_DEFINE(n, NULL, NULL, NULL, NULL, POST_KERNEL,                                \
                            CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &behavior_layer_sync_driver_api);

DT_INST_FOREACH_STATUS_OKAY(LAYER_SYNC_INST)

#endif /* DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT) */
