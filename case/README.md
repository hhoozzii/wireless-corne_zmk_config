# 36-key Corne tray case (Boardsource Wireless Corne SMT v1.01, Choc v2 + MX keycaps)

Low-profile tray for the Boardsource board with the outer pinky column broken off.
(An acrylic-bottom variant is on hold: `bottom='acrylic'` in `corne36_case.py`.)
**One half only:** the board is symmetric, so print `corne36_case_half.3mf` once as-is and once
mirrored in the slicer for the other side (same for the fit-test frame).

![preview](preview.png)

* **Board outline** is a clean polygon (straight edges, square column steps, straight cut and inner edges);
  each edge position is measured from Boardsource's two high-res product photos (~7.7 px/mm, scaled with the
  19.05 mm key grid). The cut edge sits on the breakaway mouse-bite line; the USB-C shell and power-switch nub
  are left out of the outline (the case has openings for them). Mounting holes, USB-C and power switch are
  measured from the same photos (`tools/clean_outline.py`, `tools/outline_hires2.py`).
  `case_on_boardsource_photos.png` shows the case drawn over both photos; `tools/` has the extraction
  scripts (point them at the two photos).
* **Print `corne36_fit_test_half.3mf` first** (0.8 mm frame with the case's pins, ~10 min): lower the PCB onto it
  bottom-side down. The pins should drop into the mounting holes and the board edge should sit inside the rim.
* **Case** `corne36_case_half.3mf`: ~120 x 97 mm, 8.3 mm high, 14.1 mm at the display. Print floor-down, no supports, ~30 g PLA.
  * 1.8 mm walls (4 perimeters at 0.45 mm).
  * The wall round the controller strip (top edge and inner edge, alongside the nice!view) rises to 7 mm above the
    PCB top to guard the display, with 45 degree ramps down to the normal wall at both ends. The USB-C slot goes
    through it full height. Set `display_wall` / `display_zone` to change it.
  * The mounting holes are ~4.2-4.8 mm (no grommets), so every hole gets a 3.6 mm **locating pin** with a
    5.4 mm shoulder under the PCB (clear of the socket tabs). The pin stops 0.3 mm below the PCB top.
  * **Two M2 screws** hold the board down, at the holes below the middle column and between the thumb keys:
    M2 x 8 screw + M2 washer (5 mm OD) into the 1.7 mm pilot. The other three holes sit ~1.9 mm from the
    switch housings, so there is no room for a washer there; they are pins only.
  * Hardware per half: 2x M2 x 8 screw (self-tapping or machine), 2x M2 washer (DIN 125, 5 mm OD).
  * 0.7 mm clearance to the board edge, 0.5 mm along the broken-off edge. No support ledge on the
    broken-off edge: its hotswap sockets reach the board edge (the ledge elsewhere reaches 1 mm under the PCB).
  * 3.5 mm under the PCB for sockets and the nRF module, flat floor. The battery (301230, 3 x 12 x 30 mm)
    sits on top of the PCB under the nice!view, so the case needs no battery space.
  * Openings for USB-C (top edge of the controller strip) and the power slide switch (inner edge).
  * Wall rises 1.2 mm above the PCB top; keycaps clear it bottomed out.
  * Five 10 x 0.8 mm recesses for rubber feet.

* **Top cover** `corne36_cover_half.3mf` (optional): a 1 mm plate that lies on the PCB inside the wall and hides
  the board between the keys. 15.6 mm square cutouts around every switch (thumbs at 0 / 15 / 30 degrees), open
  over the controller strip (USB-C, display + battery, power switch, reset) with a channel for the battery wires.
  The two M2 screws go through it, so they clamp cover + PCB together; no features narrower than 1.2 mm.
  Pull the switches, lay the cover on the PCB, push the switches back in. ~3 g PLA, prints flat.
  `cover_on_top_photo.png` shows it over Boardsource's top-side photo.

Regenerate after editing `P` in `corne36_case.py` (needs numpy, scikit-image, matplotlib):

    python3 corne36_case.py boardsource_outline.json out
