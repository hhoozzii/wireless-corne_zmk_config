# ZMK module: &mo_sync, a momentary-layer behavior that also runs on the right half,
# so its nice!view can show the active layer. SPDX-License-Identifier: MIT
if(CONFIG_ZMK_BEHAVIOR_LAYER_SYNC)
  zephyr_include_directories(include)
  target_sources(app PRIVATE src/behaviors/behavior_layer_sync.c)
  target_sources(app PRIVATE src/events/layer_sync_changed.c)
endif()
