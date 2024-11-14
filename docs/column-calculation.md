# Column Calculation Algorithm

This document explains how scrollshot2pdf automatically calculates the optimal number of columns for laying out an image in a PDF.

## Goal

The goal is to find the smallest number of columns that allows the image to be scaled by a clean integer factor (1/2, 1/3, etc.) while fitting within the page width. This produces the highest quality output by avoiding fractional scaling.

## DPI Handling

The algorithm first normalizes the image dimensions to account for different DPI (dots per inch) settings:

1. Input image DPI is read from metadata, defaulting to 72 DPI if not specified
2. Output PDF is targeted at 300 DPI for high quality
3. Image width is converted to points using the formula:

   $\text{width}_\text{points} = \text{width}_\text{pixels} \times \frac{72}{\text{DPI}_\text{image}}$

where 72 is the number of points per inch.

## Column Width Calculation

For each number of columns $n$ from 1 to 10:

1. Calculate available width per column:

   $\text{column}_\text{width} = \frac{\text{page}_\text{width} - \text{gap}_\text{width} \times (n-1)}{n}$

   where $\text{gap}_\text{width}$ is 20 points by default.

2. Calculate the scale factor:

   $\text{scale} = \frac{\text{column}_\text{width}}{\text{image}_\text{width}}$

3. Calculate inverse scale:

   $\text{scale}_\text{inverse} = \frac{1}{\text{scale}}$

## Finding Optimal Columns

The algorithm chooses the number of columns based on these criteria:

1. If $\text{scale} \geq 1$, use 1 column (image fits without scaling)

2. Otherwise, find smallest $n$ where $\text{scale}_\text{inverse}$ is close to an integer:

   $|\text{round}(\text{scale}_\text{inverse}) - \text{scale}_\text{inverse}| < 0.01$

3. If no solution is found up to 10 columns, default to 1 column

## Example

For an image 2000px wide at 72 DPI on A4 paper (595pt width, 20pt margins):

1. Convert to points: $2000 \times \frac{72}{72} = 2000\text{pt}$
2. Usable width: $595 - 2 \times 20 = 555\text{pt}$

For 3 columns:
1. Column width: $\frac{555 - 20 \times 2}{3} = 171.67\text{pt}$
2. Scale: $\frac{171.67}{2000} = 0.0858$
3. Inverse scale: $\frac{1}{0.0858} \approx 11.65$

Since 11.65 is not close to an integer, try next number of columns...

## Quality Considerations

Integer scaling factors (1/2, 1/3, etc.) preserve image quality better than arbitrary scaling because:

1. Each output pixel represents an equal number of input pixels
2. No interpolation artifacts are introduced
3. Fine details and text remain sharp

The algorithm prioritizes finding these clean scaling factors even if it means using more columns.
