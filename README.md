# svg2omap
A python command line tool for importing SVG files into [OpenOrienteering Mapper](https://www.openorienteering.org/)

## Introduction
OpenOrienteering Mapper (OOM) currently lacks specific tools for creating map marginalia such as logos, legends, scalebars and so on. It can therefore be easier to create such artwork in a separate graphics program, such as Inkscape or Adobe Illustrator, that can output SVG.
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
![Example 1](./example/Screen%20Shot%20Command-Ex1.png)

- `./src/svg2omap.py` is the python program file 

- `./example/'Bluff Lake_210404.omap'` the target OOM map file

- `./example/NArrow1_arc.svg` the SVG file to import

- `-ht 2.5` specifies the desired height of the imported SVG graphics in the default unit of centimeters


Next import the output geojson file into OOM using the following steps:

1. Choose Import from the File menu and select the geojson file.
![Import file](./example/Screen%20Shot%20Import1.png)

2. Click OK in the symbol mapping menu. 
![Example 1](./example/Screen%20Shot%20Import_symbol.png)
This imports the file and places it in the map (it may be located outside of the current map view).

3. Move the selected object to the desired location.
![Example 1](./example/Screen%20Shot%20Import_place.png)

4. Replace the default symbology as desired
![Example 1](./example/Screen%20Shot%20Import_replace_symbol.png)

### Example 2
`python3 ./src/svg2omap.py -m ./example/'Bluff Lake_210404.omap' -i ./example/SBar2-10k.svg -wd 60.157 -u mm -o scalebar1.geojson -dpi 600`

### Example 3
`python3 ./src/svg2omap.py -m ./example/'complete map.omap' -i ./example/open-orienteering_ill.svg -o oo.geojson -wd 3 -epsg 32632 -rotation 1.98`

## Limitations
x

## Usage
x

## Dependencies
x
