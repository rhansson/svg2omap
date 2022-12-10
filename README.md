# svg2omap
A python command line tool for importing SVG files into [OpenOrienteering Mapper](https://www.openorienteering.org/)

## Introduction
OpenOrienteering Mapper (OOM) currently lacks specific tools for creating map marginalia such as logos, legends, scale bars and so on. It can therefore be easier to create such artwork in a separate graphics program, such as Inkscape or Adobe Illustrator, that can output SVG.
**svg2omap** lets you convert an SVG file (*see limitations below*) to GeoJSON that can be imported by OOM. It transforms the SVG into map coordinates matching the coordinate system (typically UTM) of the target omap file and with the desired dimensions.

## Installation
Download the python file [svg2omap.py](./src/svg2omap.py) or create a clone/fork.

***The program requires Python 3 and the the following packages:***
- [svgpathtools](https://pypi.org/project/svgpathtools/)
- [pyproj](https://pypi.org/project/pyproj/)
- [geojson](https://pypi.org/project/geojson/)
- [numpy](https://pypi.org/project/numpy/)

## Examples
### Example 1
`python3 ./src/svg2omap.py -m ./example/'Bluff Lake_210404.omap' -i ./example/NArrow1_arc.svg -ht 2.5`

Executing the command generates the following output:
![Example 1](./doc/Screen%20Shot%20Command-Ex1.png)

- `./src/svg2omap.py` is the python program file.

- `./example/'Bluff Lake_210404.omap'` the target OOM map file.

- `./example/NArrow1_arc.svg` the SVG file to import.

- `-ht 2.5` specifies the desired height of the imported SVG graphics in the default unit of centimeters.


__Next import the output geojson file into OOM using the following steps:__

1. Choose Import from the File menu and select the geojson file.

![Import file](./doc/Screen%20Shot%20Import1.png)

![Example 1](./doc/Screen%20Shot%20Import_file.png)

2. Click OK in the symbol mapping menu. 

![Example 1](./doc/Screen%20Shot%20Import_symbol.png)

This imports the file and places it in the map (it may be located outside of the current map view).

3. Move the selected object to the desired location.

![Example 1](./doc/Screen%20Shot%20Import_place.png)

4. Replace the default symbology as desired

![Example 1](./doc/Screen%20Shot%20Import_replace_symbol.png)


### Example 2
`python3 ./src/svg2omap.py -m ./example/'Bluff Lake_210404.omap' -i ./example/SBar2-10k.svg -wd 60.157 -u mm -o scalebar1.geojson -dpi 600`

- `-u mm` specifies that the units for the width are given in millimeters.

- `-o scalebar1.geojson` the name of the output file (default is <input_file>.geojson).

- `-dpi 600` the resolution at which the graphics are converted (default is 300).

For this example, the given width of the scale bar must match the map scale including the text "Meters" to the right of the bar.

![Example 2](./doc/Screen%20Shot%20Illu_size_sbar2.png)

In order to fill the outlined text, we need to create a black fill symbol that is below the white "Forest" in the drawing order

![Example 2](./doc/Screen%20Shot%20Import_text-fill.png)

that will be used for the interior rings of the "0":s.

![Example 2](./doc/Screen%20Shot%20Import_fill_text_interior.png)


### Example 3
`python3 ./src/svg2omap.py -m ./example/'complete map.omap' -i ./example/open-orienteering_ill.svg -o oo.geojson -wd 3 -epsg 32632 -rotation 1.98`

- `-epsg 32632` specifies [EPSG code](https://epsg.io/).
- `-rotation 1.98` specifies the map rotation (declination/grivation).

![Example 3](./doc/Screen%20Shot%20Import_oo-logo.png)

In this example we are forcing an EPSG code and a rotation matching the georeferencing of the map. Normally, this information is automatically extracted from the omap file when available.


## Limitations

The intention of the program is to create a starting point for the most intricate layout elements by converting lines, curves and paths. It does not support all parts of the SVG format! The following are the most notable limitations:

- Text

Actual text strings and fonts are not supported. Instead, text must be vectorized (outlined) in the source SVG (*see Creating Outlined Text below*.

- Compound Paths

So called compound paths are not supported. In Illustrator, these can be removed by the Release command:

![Compound Path](./doc/Screen%20Shot%20Illustrator%20Release%20CPath.png)

- Colors

No part of the graphic properties such as color and line width are preserved (only the skeleton). This means that the symbology must be reapplied in OOM (*see Examples above*).

- Compression

Compressed or minified SVG is not supported.

### Creating Outlined Text

Follow these steps to create outlined text:

***Inkscape***

1. Select the text elements
2. Select Path> Object to Path

![Compound Path](./doc/Screen%20Shot%20Inkscape_Outline-Text.png)

***Illustrator***

1. Choose File> Save As> SVG with the following options:

![Compound Path](./doc/Screen%20Shot%20Illustrator_SaveAs-SVG.png)

## Usage

The following arguments are available:
+ `-i  <file name>` SVG input file (***required***).
+ `-o  <file name>` Output geojson file (default: input file name *.geojson).
+ `-m  <file name>` Target OOM (*.omap) file identifying map scale, CRS and declination (default: SVG coords).
+ `-wd <number>` Width of graphic in target (default: SVG coords). **_Notice:_ normally you should specify either width or height.**
+ `-ht <number>` Height of graphic in target (default: SVG coords). **_Notice:_ normally you should specify either width or height.**
+ `-u  <unit>` Units for height/width (default: cm). Choices are: 'mm', 'cm', 'in', 'pt'.
+ `-dpi <number>` Resolution for converting curve paths incl text outlines (default: 300). This is an approximate measure. **_Notice:_ a too high value may not yield a better result.**
+ `-rotation <number>` Rotation of graphic relative to the map measured counterclockwise (default: map declination). **_Notice:_ Normally, this information is automatically extracted from the omap file when available.**
+ `-epsg <code>` EPSG code (default: map coordinate system as specified in target omap file). **_Notice:_ Normally, this information is automatically extracted from the omap file when available.**
+ `-skip_list <list of numbers>` List of id's to ignore. Ex '0,3,9' (default: None). This allows you to filter out certain input elements. Id numbers are part of the output properties (attributes). You can inspect them in OOM or a GIS.
+ `-debug <y/n>` Prints debug statements (default: No).")

