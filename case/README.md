# 36-key Corne tray case (Boardsource Wireless Corne SMT v1.01, Choc v2 + MX keycaps)

Low-profile tray for the Boardsource board with the outer pinky column broken off.
**One half only:** the board is symmetric, so print `corne36_case_half.3mf` once as-is and once
mirrored in the slicer for the other side (same for the fit-test frame).

![preview](preview.png)

* **Board geometry** (outline, 5 mounting holes, USB-C, power switch) is extracted from Boardsource's two
  high-res product photos (bottom and top side, ~7.7 px/mm), scaled with the 19.05 mm key grid
  (residual <0.1 mm), three board halves averaged, cut at the breakaway mouse-bite line.
  `case_on_boardsource_photos.png` shows the case drawn over both photos; `tools/` has the extraction
  scripts (point them at the two photos).
* **Print `corne36_fit_test_half.3mf` first** (0.8 mm frame with the case's pins, ~10 min): lower the PCB onto it
  bottom-side down. The pins should drop into the mounting holes and the board edge should sit inside the rim.
* **Case** `corne36_case_half.3mf`: ~124 x 98 x 8.3 mm, print floor-down, no supports, ~33 g PLA.
  * The mounting holes are ~4.2-4.8 mm (no grommets), so every hole gets a 3.6 mm **locating pin** with a
    5.4 mm shoulder under the PCB (clear of the socket tabs). The pin stops 0.3 mm below the PCB top.
  * **Two M2 screws** hold the board down, at the holes below the middle column and between the thumb keys:
    M2 x 8 screw + M2 washer (5 mm OD) into the 1.7 mm pilot. The other three holes sit ~1.9 mm from the
    switch housings, so there is no room for a washer there; they are pins only.
  * Hardware per half: 2x M2 x 8 screw (self-tapping or machine), 2x M2 washer (DIN 125, 5 mm OD).
  * 0.7 mm clearance to the board edge, 1 mm extra along the broken-off edge.
  * 3.5 mm under the PCB for sockets and the nRF module, flat floor. The battery (301230, 3 x 12 x 30 mm)
    sits on top of the PCB under the nice!view, so the case needs no battery space.
  * Openings for USB-C (top edge of the controller strip) and the power slide switch (inner edge).
  * Wall rises 1.2 mm above the PCB top; keycaps clear it bottomed out.
  * Five 10 x 0.8 mm recesses for rubber feet.

Regenerate after editing `P` in `corne36_case.py` (needs numpy, scikit-image, matplotlib):

    python3 corne36_case.py boardsource_outline.json out
