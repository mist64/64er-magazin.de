# #!/bin/bash

# fav icons collection


# https://evilmartians.com/chronicles/how-to-favicon-in-2021-six-files-that-fit-most-needs
# https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/ConfiguringWebApplications/ConfiguringWebApplications.html
# 
# 
# Header Code:
#
# <link rel="icon" href="/favicon.ico" sizes="32x32">
# <link rel="icon" href="/fav/icon.svg" type="image/svg+xml">
# <link rel="apple-touch-icon" href="/fav/apple-touch-icon.png">
# 
#
# Icons:
# 
# * 1 SVG with CSS for @media (prefers-color-scheme: dark)
#     - Generated with help by 
#       https://doodad.dev/gradient-generator/
# 
# * 1 apple-touch-icon.png (180x180)
#     - "Small note: an Apple touch icon will look better
#         if you place 20px padding around the icon and add some background color."
# 
# * 1 favicon.ico containing multiple sizes (located at top level) generated via:
#     convert icon.svg -define icon:auto-resize=32,16 favicon.ico
# 
# 
# * each of these 3 icon files in a "-dev" version that is used for local builds of the site
#    (so it is more recognizable if the page is the local one or not)
# 
# everything generated from the svgs (icon.svg, icon-dev.svg) via:
#

# favicon.ico (ensuring transparent background):
convert issues/fav/icon.svg -transparent white -define icon:auto-resize=32,16 "issues/favicon.ico"
convert issues/fav/icon-dev.svg -transparent white -define icon:auto-resize=32,16 "issues/favicon-dev.ico"

# apple touch icons (with border and custom background color):
inkscape "issues/fav/icon.svg" --export-width=160 --export-filename="issues/fav/icon.png"
inkscape "issues/fav/icon-dev.svg" --export-width=160 --export-filename="issues/fav/icon-dev.png"

convert "issues/fav/icon.png" -bordercolor "#00A7D1" -border 20 "issues/fav/apple-touch-icon.png"
convert "issues/fav/icon-dev.png" -bordercolor "#ff582e" -border 20 "issues/fav/apple-touch-icon-dev.png"
