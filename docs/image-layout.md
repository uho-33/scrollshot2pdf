# Image Layout Specification

## Page Layout

### Effective Page Size
Given:
- Page dimensions $(w_p, h_p)$ in points
- Margin $m$ in points
- Number of columns $n$ (default 1)
- Column gap $g$ (default 20 points)

The effective usable area has dimensions:
- Total Width: $w_e = w_p - 2m$
- Column Width: $w_c = (w_e - g(n-1))/n$
- Height: $h_e = h_p - 2m$

### Image Scaling
For an input image with dimensions $(w_i, h_i)$ pixels:

1. The scale factor $s$ is computed to fit the image width to the column width:
   $s = \frac{w_c}{w_i}$

2. The scaled image dimensions are:
   - Width: $w_s = w_i \cdot s$
   - Height: $h_s = h_i \cdot s$

## Image Slicing

### Content Gap Detection
1. The image is analyzed in its original resolution (before scaling)
2. A row is considered a "gap" if all pixels have brightness > 250
3. Consecutive gap rows are grouped
4. Groups longer than the minimum gap size (default 50px) are recorded
5. The middle position of each qualifying gap is stored

### Slice Calculation
For each slice:

1. Starting from position $y_0$ (0 for first slice):
   - Ideal next position $y_1 = \min(y_0 + h_e/s, h_i)$
   - Search window: $[y_1 - h_e/(4s), y_1]$
   - If a content gap exists in window, use its position
   - Otherwise use $y_1$

2. This produces slice coordinates $(y_0, y_1)$ in original image coordinates

### Page Positioning
For each slice with coordinates $(y_0, y_1)$:

1. Slice height in original coordinates: $h_{slice} = y_1 - y_0$

2. Position on page (in points):
   - Column index: $c = \text{slice_index} \bmod n$
   - X: $x = m + c(w_c + g)$
   - Y: $y = h_p - h_{slice} \cdot s - m - \lfloor\text{slice_index}/n\rfloor \cdot h_e$

3. Dimensions on page (in points):
   - Width: $w_s = w_i \cdot s$
   - Height: $h_s = h_{slice} \cdot s$

## Example

For an A4 page (595.276 × 841.89 points) with 10mm margins (28.346 points) and 2 columns:

1. Effective area: 538.584 × 785.198 points
   Column width: 259.119 points (with 20pt gap)

2. For a 1000×3000px image:
   - Scale factor: $s = 259.119/1000 = 0.259119$
   - Scaled width: 259.119 points per column
   - Scaled height: 777.357 points

3. Each slice will be approximately 785.198 points high (scaled), or 3030 pixels in original coordinates, adjusted to nearest content gap

4. Final slice positioning:
   - Left margins: 28.346 points (col 1), 307.465 points (col 2)
   - Top margin from slice top: 28.346 points
